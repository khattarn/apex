"""
sip_bridge.py — Manual bridge call via Vobiz India SIP trunk.

Vobiz is a SIP trunk (not a registrar). Auth is per-INVITE via digest challenge.
No REGISTER needed.

Flow:
1. Open TCP connection to Vobiz SIP server
2. INVITE founder's mobile — Vobiz may challenge with 407
3. Re-INVITE with Proxy-Authorization digest header
4. Wait up to 45s for founder to answer (200 OK)
5. ACK the 200
6. Send REFER → Vobiz transfers founder's call to destination and bridges both parties
7. Our TCP leg ends; founder talks to lead directly
"""

import hashlib
import logging
import os
import re
import socket
import threading
import time
import uuid

log = logging.getLogger(__name__)

VOBIZ_HOST = "edcf4901.sip.vobiz.ai"
VOBIZ_PORT = 5060
SIP_USERNAME = "practicedesk-priya"
CALLER_NUMBER = "+919262171423"

_bridges: dict[str, dict] = {}


def _normalize(number: str) -> str:
    digits = re.sub(r"[^\d+]", "", number)
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits


# ── SIP client ─────────────────────────────────────────────────────────────────

class _SIPClient:
    def __init__(self):
        self._host = VOBIZ_HOST
        self._port = VOBIZ_PORT
        self._user = SIP_USERNAME
        self._pw = os.getenv("VOBIZ_SIP_PASSWORD", "")
        self._sock: socket.socket | None = None
        self._local_ip = ""
        self._local_port = 0
        self._cseq = 1

    def connect(self):
        self._sock = socket.create_connection((self._host, self._port), timeout=15)
        self._local_ip, self._local_port = self._sock.getsockname()
        log.info("SIP TCP %s:%s → %s:%s", self._local_ip, self._local_port, self._host, self._port)

    def close(self):
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass

    def _send(self, msg: str):
        self._sock.sendall(msg.encode("utf-8"))

    def _recv(self, timeout: float = 30) -> str:
        self._sock.settimeout(timeout)
        buf = b""
        try:
            while True:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                if b"\r\n\r\n" not in buf:
                    continue
                header_part, _, body = buf.partition(b"\r\n\r\n")
                m = re.search(rb"Content-Length:\s*(\d+)", header_part, re.IGNORECASE)
                clen = int(m.group(1)) if m else 0
                if len(body) >= clen:
                    break
        except socket.timeout:
            pass
        decoded = buf.decode("utf-8", errors="replace")
        if decoded:
            log.debug("SIP ← %s", decoded[:300])
        return decoded

    def _via(self) -> str:
        branch = "z9hG4bK" + uuid.uuid4().hex[:12]
        return f"SIP/2.0/TCP {self._local_ip}:{self._local_port};branch={branch}"

    def _contact(self) -> str:
        return f"<sip:{self._user}@{self._local_ip}:{self._local_port};transport=tcp>"

    def _digest(self, realm: str, nonce: str, method: str, uri: str,
                qop: str = "", cnonce: str = "", nc: str = "") -> str:
        ha1 = hashlib.md5(f"{self._user}:{realm}:{self._pw}".encode()).hexdigest()
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        if qop == "auth":
            return hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()).hexdigest()
        return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

    def _auth_hdr(self, challenge_resp: str, method: str, uri: str) -> str | None:
        """Parse 401/407 (including qop=auth) and return the appropriate auth header."""
        realm_m = re.search(r'realm="([^"]+)"', challenge_resp)
        nonce_m = re.search(r'nonce="([^"]+)"', challenge_resp)
        if not realm_m or not nonce_m:
            log.warning("Could not parse auth challenge: %s", challenge_resp[:300])
            return None
        realm = realm_m.group(1)
        nonce = nonce_m.group(1)
        qop_m = re.search(r'qop="([^"]+)"', challenge_resp)
        qop = qop_m.group(1).split(",")[0].strip() if qop_m else ""

        hdr_name = "Proxy-Authorization" if challenge_resp.lstrip().startswith("SIP/2.0 407") else "Authorization"

        if qop == "auth":
            cnonce = uuid.uuid4().hex[:8]
            nc = "00000001"
            response = self._digest(realm, nonce, method, uri, qop, cnonce, nc)
            return (
                f'{hdr_name}: Digest username="{self._user}",realm="{realm}",'
                f'nonce="{nonce}",uri="{uri}",qop={qop},nc={nc},cnonce="{cnonce}",'
                f'response="{response}",algorithm=MD5'
            )
        response = self._digest(realm, nonce, method, uri)
        return (
            f'{hdr_name}: Digest username="{self._user}",realm="{realm}",'
            f'nonce="{nonce}",uri="{uri}",response="{response}",algorithm=MD5'
        )

    @staticmethod
    def _status(resp: str) -> int:
        m = re.match(r"SIP/2\.0\s+(\d{3})", resp.lstrip())
        return int(m.group(1)) if m else 0

    @staticmethod
    def _to_tag(resp: str) -> str:
        m = re.search(r"(?i)^To:.*?;tag=([^\s;>\r\n]+)", resp, re.MULTILINE)
        return m.group(1) if m else ""

    def _sdp(self) -> str:
        # Port 0 + a=inactive = signaling-only call leg (no RTP on server)
        return "\r\n".join([
            "v=0",
            f"o={self._user} {int(time.time())} 1 IN IP4 {self._local_ip}",
            "s=Bridge",
            f"c=IN IP4 {self._local_ip}",
            "t=0 0",
            "m=audio 0 RTP/AVP 0 8",
            "a=rtpmap:0 PCMU/8000",
            "a=rtpmap:8 PCMA/8000",
            "a=inactive",
            "",
        ])

    def _invite_msg(self, to_number: str, call_id: str, from_tag: str,
                    cseq: int = 1, auth: str = "") -> tuple[str, str]:
        """Returns (sip_message, via_branch) so caller can reuse branch for ACK."""
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        sdp = self._sdp()
        branch = "z9hG4bK" + uuid.uuid4().hex[:12]
        via = f"SIP/2.0/TCP {self._local_ip}:{self._local_port};branch={branch}"
        lines = [
            f"INVITE {to_uri} SIP/2.0",
            f"Via: {via}",
            "Max-Forwards: 70",
            f"From: <{from_uri}>;tag={from_tag}",
            f"To: <{to_uri}>",
            f"Call-ID: {call_id}",
            f"CSeq: {cseq} INVITE",
            f"Contact: {self._contact()}",
            "Allow: INVITE,ACK,BYE,CANCEL,REFER,NOTIFY",
            "Content-Type: application/sdp",
            f"Content-Length: {len(sdp)}",
        ]
        if auth:
            lines.append(auth)
        return "\r\n".join(lines) + "\r\n\r\n" + sdp, branch

    def _ack(self, to_number: str, call_id: str, from_tag: str, to_tag: str,
             cseq_num: int = 1, via_branch: str = "") -> str:
        """
        ACK for a non-2xx response MUST reuse the same Via branch as the INVITE.
        ACK for a 2xx response uses a new branch (new transaction).
        """
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        via = (f"SIP/2.0/TCP {self._local_ip}:{self._local_port};branch={via_branch}"
               if via_branch else self._via())
        return "\r\n".join([
            f"ACK {to_uri} SIP/2.0",
            f"Via: {via}",
            "Max-Forwards: 70",
            f"From: <{from_uri}>;tag={from_tag}",
            f"To: <{to_uri}>;tag={to_tag}",
            f"Call-ID: {call_id}",
            f"CSeq: {cseq_num} ACK",
            "Content-Length: 0",
            "", "",
        ])

    # ── INVITE (with auto-retry on 401/407) ────────────────────────────────────

    def invite_and_wait(self, to_number: str, timeout: float = 45) -> tuple[bool, str, str, str, str]:
        """
        Send INVITE. Handles 407/401 digest challenge:
          1. Send initial INVITE
          2. On 407: send ACK (same branch), then re-INVITE with auth
        Returns (answered, call_id, from_tag, to_tag, last_raw_response).
        """
        call_id = uuid.uuid4().hex
        from_tag = uuid.uuid4().hex[:8]
        to_tag = ""
        to_uri = f"sip:{to_number}@{self._host}"
        last_resp = ""

        # ── Initial INVITE (no auth) ──────────────────────────────────────────
        msg, branch = self._invite_msg(to_number, call_id, from_tag, cseq=1)
        log.debug("SIP → INVITE %s (cseq=1)", to_number)
        self._send(msg)

        deadline = time.time() + timeout
        authed = False

        while time.time() < deadline:
            remaining = max(1.0, deadline - time.time())
            resp = self._recv(min(5.0, remaining))
            if not resp:
                continue

            last_resp = resp
            code = self._status(resp)
            log.info("INVITE response: %s", code)

            if code in (100, 180, 183):
                continue

            if code in (401, 407) and not authed:
                # Parse To-tag from the 407 for the ACK
                to_tag_407 = self._to_tag(resp)
                # ACK the 407 — MUST reuse same Via branch as original INVITE
                ack_msg = self._ack(to_number, call_id, from_tag, to_tag_407,
                                    cseq_num=1, via_branch=branch)
                self._send(ack_msg)
                log.debug("SIP → ACK (for 407)")

                auth = self._auth_hdr(resp, "INVITE", to_uri)
                if not auth:
                    return False, call_id, from_tag, "", resp

                # New INVITE with credentials (new transaction → new branch, incremented CSeq)
                self._cseq += 1
                msg, branch = self._invite_msg(to_number, call_id, from_tag,
                                               cseq=self._cseq, auth=auth)
                log.debug("SIP → INVITE (with auth, cseq=%s)", self._cseq)
                self._send(msg)
                authed = True
                to_tag = ""  # reset; new response will carry final to_tag
                continue

            if code == 200:
                to_tag = self._to_tag(resp)
                # 2xx ACK uses new branch (new transaction)
                self._send(self._ack(to_number, call_id, from_tag, to_tag,
                                     cseq_num=self._cseq))
                log.info("Call answered — to_tag=%s", to_tag)
                return True, call_id, from_tag, to_tag, resp

            # Terminal failure (4xx/5xx/6xx)
            log.warning("INVITE failed: %s", code)
            return False, call_id, from_tag, to_tag, resp

        return False, call_id, from_tag, to_tag, "timeout"

    # ── REFER (blind transfer) ──────────────────────────────────────────────────

    def refer(self, to_number: str, destination: str,
              call_id: str, from_tag: str, to_tag: str) -> tuple[bool, str]:
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        dest_uri = f"sip:{destination}@{self._host}"
        self._cseq += 1
        msg = "\r\n".join([
            f"REFER {to_uri} SIP/2.0",
            f"Via: {self._via()}",
            "Max-Forwards: 70",
            f"From: <{from_uri}>;tag={from_tag}",
            f"To: <{to_uri}>;tag={to_tag}",
            f"Call-ID: {call_id}",
            f"CSeq: {self._cseq} REFER",
            f"Contact: {self._contact()}",
            f"Refer-To: <{dest_uri}>",
            f"Referred-By: <{from_uri}>",
            "Content-Length: 0",
            "", "",
        ])
        self._send(msg)
        resp = self._recv(10)
        code = self._status(resp)
        log.info("REFER → %s", code)
        return code in (200, 202), resp


# ── Public probe (for /api/bridge/test) ───────────────────────────────────────

def probe_vobiz() -> dict:
    """
    Attempt a test INVITE to Vobiz and return the raw SIP exchange.
    Useful for debugging auth/connectivity issues without placing a real call.
    """
    client = _SIPClient()
    result: dict = {}
    try:
        client.connect()
        result["connected"] = True
        result["local"] = f"{client._local_ip}:{client._local_port}"

        # Send a test INVITE to a dummy number — we just want to see Vobiz's response
        call_id = uuid.uuid4().hex
        from_tag = uuid.uuid4().hex[:8]
        msg, _branch = client._invite_msg("+910000000000", call_id, from_tag)
        client._send(msg)
        resp = client._recv(8)
        result["invite_response_code"] = client._status(resp)
        result["invite_response_raw"] = resp[:600]

        if client._status(resp) in (401, 407):
            result["auth_challenge_parsed"] = bool(
                re.search(r'realm="', resp) and re.search(r'nonce="', resp)
            )

    except Exception as exc:
        result["error"] = str(exc)
    finally:
        client.close()
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

def start_bridge(destination: str) -> str:
    bridge_id = uuid.uuid4().hex[:8]
    dest = _normalize(destination)
    founder = _normalize(os.getenv("FOUNDER_WHATSAPP_NUMBER", "+919810982019"))

    status: dict = {
        "state": "starting",
        "destination": dest,
        "founder": founder,
        "started_at": time.time(),
    }
    _bridges[bridge_id] = status

    def _run():
        client = _SIPClient()
        try:
            status["state"] = "connecting"
            client.connect()

            # WA heads-up before phone rings
            try:
                from agents.outreach import send_whatsapp_message
                send_whatsapp_message(
                    founder,
                    f"📞 Bridge call incoming: connecting you to {dest}. Your phone will ring now.",
                )
            except Exception:
                pass

            status["state"] = "calling_founder"
            answered, call_id, from_tag, to_tag, raw = client.invite_and_wait(founder, timeout=45)

            if not answered:
                code = _SIPClient._status(raw)
                status["state"] = "no_answer"
                status["error"] = f"Call not answered (SIP {code}) — see Railway logs for detail"
                return

            status["state"] = "transferring"
            time.sleep(0.5)

            ok, raw_refer = client.refer(founder, dest, call_id, from_tag, to_tag)
            if ok:
                status["state"] = "connected"
                status["connected_at"] = time.time()
            else:
                code = _SIPClient._status(raw_refer)
                status["state"] = "transfer_failed"
                status["error"] = f"REFER rejected (SIP {code})"

        except Exception as exc:
            log.exception("sip_bridge error: %s", exc)
            status["state"] = "error"
            status["error"] = str(exc)
        finally:
            client.close()

    threading.Thread(target=_run, daemon=True).start()
    return bridge_id


def get_bridge_status(bridge_id: str) -> dict:
    return _bridges.get(bridge_id, {"state": "not_found"})
