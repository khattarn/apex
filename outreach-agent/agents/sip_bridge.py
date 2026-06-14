"""
sip_bridge.py — Manual bridge call via Vobiz India SIP trunk.

Flow:
1. Open TCP connection to Vobiz SIP server
2. REGISTER with digest auth
3. INVITE founder's mobile (a=inactive SDP — no RTP on server)
4. Wait up to 45s for founder to answer (200 OK)
5. Send REFER: tells Vobiz to transfer founder's call to the destination number
6. Vobiz bridges both parties; our leg ends

Railway uses TCP for SIP (connection-oriented, so Vobiz responses come back
on the same socket — no NAT/UDP issue). a=inactive SDP means no RTP ports
are needed on the server.
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
CALLER_NUMBER = "+919262171423"  # outbound caller ID

# In-memory state for active bridges
_bridges: dict[str, dict] = {}


def _normalize(number: str) -> str:
    """Ensure number is E.164 (starts with +)."""
    digits = re.sub(r"[^\d+]", "", number)
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits


# ── Low-level SIP client ───────────────────────────────────────────────────────

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
        self._from_tag = uuid.uuid4().hex[:8]
        self._reg_call_id = uuid.uuid4().hex

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self):
        self._sock = socket.create_connection((self._host, self._port), timeout=15)
        self._local_ip, self._local_port = self._sock.getsockname()
        log.info("SIP TCP connected %s:%s → %s:%s",
                 self._local_ip, self._local_port, self._host, self._port)

    def close(self):
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass

    # ── I/O ───────────────────────────────────────────────────────────────────

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
        return buf.decode("utf-8", errors="replace")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _via(self) -> str:
        branch = "z9hG4bK" + uuid.uuid4().hex[:12]
        return f"SIP/2.0/TCP {self._local_ip}:{self._local_port};branch={branch}"

    def _contact(self) -> str:
        return f"<sip:{self._user}@{self._local_ip}:{self._local_port};transport=tcp>"

    def _digest(self, realm: str, nonce: str, method: str, uri: str) -> str:
        ha1 = hashlib.md5(f"{self._user}:{realm}:{self._pw}".encode()).hexdigest()
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

    def _auth_hdr(self, resp: str, method: str, uri: str) -> str | None:
        realm_m = re.search(r'realm="([^"]+)"', resp)
        nonce_m = re.search(r'nonce="([^"]+)"', resp)
        if not realm_m or not nonce_m:
            return None
        realm = realm_m.group(1)
        nonce = nonce_m.group(1)
        response = self._digest(realm, nonce, method, uri)
        hdr_name = "Proxy-Authorization" if "407" in resp[:20] else "Authorization"
        return (
            f'{hdr_name}: Digest username="{self._user}",realm="{realm}",'
            f'nonce="{nonce}",uri="{uri}",response="{response}",algorithm=MD5'
        )

    @staticmethod
    def _to_tag(resp: str) -> str:
        m = re.search(r"(?i)^To:.*?tag=([^\s;>\r\n]+)", resp, re.MULTILINE)
        return m.group(1) if m else ""

    @staticmethod
    def _status_code(resp: str) -> int:
        m = re.match(r"SIP/2\.0\s+(\d{3})", resp)
        return int(m.group(1)) if m else 0

    # ── REGISTER ──────────────────────────────────────────────────────────────

    def _reg_msg(self, auth: str = "") -> str:
        uri = f"sip:{self._user}@{self._host}"
        lines = [
            f"REGISTER sip:{self._host} SIP/2.0",
            f"Via: {self._via()}",
            "Max-Forwards: 70",
            f"From: <{uri}>;tag={self._from_tag}",
            f"To: <{uri}>",
            f"Call-ID: {self._reg_call_id}",
            f"CSeq: {self._cseq} REGISTER",
            f"Contact: {self._contact()}",
            "Expires: 300",
            "Content-Length: 0",
        ]
        if auth:
            lines.append(auth)
        return "\r\n".join(lines) + "\r\n\r\n"

    def register(self) -> bool:
        self._send(self._reg_msg())
        resp = self._recv(15)
        code = self._status_code(resp)
        if code in (401, 407):
            uri = f"sip:{self._host}"
            auth = self._auth_hdr(resp, "REGISTER", uri)
            if not auth:
                log.error("REGISTER: could not parse auth challenge")
                return False
            self._cseq += 1
            self._send(self._reg_msg(auth))
            resp = self._recv(15)
            code = self._status_code(resp)
        ok = code == 200
        log.info("REGISTER → %s", code)
        return ok

    # ── INVITE ────────────────────────────────────────────────────────────────

    def _sdp(self) -> str:
        # m=audio 0 — port 0 disables the media line (signaling-only call).
        # Most SIP proxies accept this; avoids needing a real RTP port on server.
        lines = [
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
        ]
        return "\r\n".join(lines)

    def _invite_msg(self, to_number: str, call_id: str, from_tag: str,
                    cseq: int = 1, auth: str = "") -> str:
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        sdp = self._sdp()
        lines = [
            f"INVITE {to_uri} SIP/2.0",
            f"Via: {self._via()}",
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
        return "\r\n".join(lines) + "\r\n\r\n" + sdp

    def _ack_msg(self, to_number: str, call_id: str, from_tag: str, to_tag: str) -> str:
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        lines = [
            f"ACK {to_uri} SIP/2.0",
            f"Via: {self._via()}",
            "Max-Forwards: 70",
            f"From: <{from_uri}>;tag={from_tag}",
            f"To: <{to_uri}>;tag={to_tag}",
            f"Call-ID: {call_id}",
            "CSeq: 1 ACK",
            "Content-Length: 0",
            "",
        ]
        return "\r\n".join(lines) + "\r\n"

    def invite_and_wait(self, to_number: str, timeout: float = 45) -> tuple[bool, str, str, str]:
        """
        Send INVITE to to_number. Wait for answer (200 OK).
        Returns (answered, call_id, from_tag, to_tag).
        """
        call_id = uuid.uuid4().hex
        from_tag = uuid.uuid4().hex[:8]
        to_tag = ""

        self._send(self._invite_msg(to_number, call_id, from_tag))
        deadline = time.time() + timeout

        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            resp = self._recv(min(5.0, remaining))
            if not resp:
                continue

            code = self._status_code(resp)
            log.debug("INVITE response %s", code)

            if code in (100, 180, 183):
                continue  # Trying / Ringing

            if code in (401, 407):
                uri = f"sip:{to_number}@{self._host}"
                auth = self._auth_hdr(resp, "INVITE", uri)
                if not auth:
                    return False, call_id, from_tag, to_tag
                self._cseq += 1
                self._send(self._invite_msg(to_number, call_id, from_tag,
                                            cseq=self._cseq, auth=auth))
                continue

            if code == 200:
                to_tag = self._to_tag(resp)
                self._send(self._ack_msg(to_number, call_id, from_tag, to_tag))
                log.info("INVITE 200 OK — call established with %s", to_number)
                return True, call_id, from_tag, to_tag

            # Any 4xx/5xx/6xx = failure
            log.warning("INVITE failed with %s", code)
            return False, call_id, from_tag, to_tag

        log.warning("INVITE timed out for %s", to_number)
        return False, call_id, from_tag, to_tag

    # ── REFER (blind transfer) ─────────────────────────────────────────────────

    def refer(self, to_number: str, destination: str,
              call_id: str, from_tag: str, to_tag: str) -> bool:
        """
        Send REFER on an active call to transfer to_number → destination.
        Vobiz will call destination and bridge the two legs.
        """
        to_uri = f"sip:{to_number}@{self._host}"
        from_uri = f"sip:{self._user}@{self._host}"
        dest_uri = f"sip:{destination}@{self._host}"
        self._cseq += 1
        lines = [
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
            "",
        ]
        self._send("\r\n".join(lines) + "\r\n")
        resp = self._recv(10)
        code = self._status_code(resp)
        log.info("REFER → %s", code)
        return code in (200, 202)


# ── Public API ─────────────────────────────────────────────────────────────────

def start_bridge(destination: str) -> str:
    """
    Kick off a bridge call in a background thread.
    Returns bridge_id — poll get_bridge_status(bridge_id) for updates.
    """
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

            status["state"] = "registering"
            if not client.register():
                status["state"] = "error"
                status["error"] = "SIP registration failed — check Vobiz credentials"
                return

            # Send WA heads-up to founder so they know what's happening
            try:
                from agents.outreach import send_whatsapp_message
                send_whatsapp_message(founder, f"📞 Bridge call incoming: connecting you to {dest}. Your phone will ring now.")
            except Exception:
                pass

            status["state"] = "calling_founder"
            answered, call_id, from_tag, to_tag = client.invite_and_wait(founder, timeout=45)

            if not answered:
                status["state"] = "no_answer"
                status["error"] = "Founder did not answer"
                return

            status["state"] = "transferring"
            time.sleep(0.5)  # brief pause before REFER

            if client.refer(founder, dest, call_id, from_tag, to_tag):
                status["state"] = "connected"
                status["connected_at"] = time.time()
            else:
                status["state"] = "transfer_failed"
                status["error"] = "REFER rejected by Vobiz"

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
