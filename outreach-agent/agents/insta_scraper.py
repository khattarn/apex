"""
Instagram Affiliate Prospector — Agent 11a

Searches legal hashtags, finds advocate influencer accounts (2K–500K followers),
extracts contact info from bio, and saves them to the affiliates table as prospects.

Uses instaloader with the dedicated @leaglebeagle account.
"""

import os
import re
import time
import logging
from typing import Generator

log = logging.getLogger(__name__)

# Hashtags to search — posts under these tags are usually posted by advocates
HASHTAGS = [
    "indianlawyer",
    "advocatelife",
    "indianadvocate",
    "lawyersofindia",
    "legalindia",
    "highcourtadvocate",
    "supremecourtofindia",
    "legaladviceindia",
    "lawyerlife",
    "indianlegalprofessional",
    "courtroom",
    "lawstudentindia",
    "vakil",
    "barcouncil",
]

# Bio keywords that confirm the account is a legal professional
LEGAL_KEYWORDS = [
    "advocate", "lawyer", "vakil", "barrister", "solicitor",
    "legal", "llb", "high court", "supreme court", "district court",
    "bar council", "attorney", "hc ", " sc ", "legal aid",
]

MIN_FOLLOWERS = 2_000
MAX_FOLLOWERS = 500_000

# Regex patterns to extract contact info from bio
_PHONE_RE = re.compile(r'(?:\+91[\s\-]?)?[6-9]\d{9}')
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def _extract_phone(text: str) -> str:
    m = _PHONE_RE.search(text.replace(" ", ""))
    if not m:
        return ""
    raw = re.sub(r'\D', '', m.group())
    if len(raw) == 10:
        return f"+91{raw}"
    if len(raw) == 12 and raw.startswith("91"):
        return f"+{raw}"
    return raw


def _extract_email(text: str) -> str:
    m = _EMAIL_RE.search(text)
    return m.group().lower() if m else ""


def _is_legal_bio(bio: str) -> bool:
    bio_lower = bio.lower()
    return any(kw in bio_lower for kw in LEGAL_KEYWORDS)


_SESSION_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", ".insta_session")


def _login():
    """
    Login to Instagram and return an Instaloader instance.

    Priority order:
      1. INSTA_SESSION_B64 env var — base64-encoded session file (use on Railway)
      2. Local session file at .insta_session — created by /api/affiliates/export-session
      3. Username + password login — only works from trusted IPs (not Railway datacenters)
    """
    import instaloader
    import base64
    import tempfile

    username = os.getenv("INSTA_USERNAME", "")
    if not username:
        raise RuntimeError("INSTA_USERNAME must be set in .env")

    L = instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    # Option 1: session from env var (Railway)
    session_b64 = os.getenv("INSTA_SESSION_B64", "")
    if session_b64:
        try:
            data = base64.b64decode(session_b64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".session")
            tmp.write(data)
            tmp.flush()
            tmp.close()
            L.load_session_from_file(username, tmp.name)
            os.unlink(tmp.name)
            log.info("Loaded Instagram session from INSTA_SESSION_B64 env var")
            return L
        except Exception as exc:
            raise RuntimeError(f"INSTA_SESSION_B64 is set but could not be loaded: {exc}")

    # Option 2: local session file (saved after running export-session locally)
    session_file = _SESSION_FILE_PATH
    if os.path.exists(session_file):
        try:
            L.load_session_from_file(username, session_file)
            log.info("Loaded Instagram session from local file")
            return L
        except Exception:
            log.info("Local session file invalid, falling back to password login")

    # Option 3: password login (only works from home IP, not Railway)
    password = os.getenv("INSTA_PASSWORD", "")
    if not password:
        raise RuntimeError(
            "No Instagram session available. "
            "Either set INSTA_SESSION_B64 (Railway) or run /api/affiliates/export-session locally first."
        )
    L.login(username, password)
    L.save_session_to_file(session_file)
    log.info("Logged in to Instagram as %s and saved session", username)
    return L


def export_session_b64() -> str:
    """
    Login locally (where it works), save session, return base64 string.
    Paste the result into Railway as INSTA_SESSION_B64.
    """
    import base64
    L = _login()
    session_file = _SESSION_FILE_PATH
    L.save_session_to_file(session_file)
    with open(session_file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def scrape(
    hashtags: list[str] | None = None,
    max_per_hashtag: int = 30,
    min_followers: int = MIN_FOLLOWERS,
    max_followers: int = MAX_FOLLOWERS,
) -> Generator[str, None, None]:
    """
    Scrape Instagram for legal influencer prospects.
    Yields log lines for SSE streaming.
    Saves new prospects to the affiliates table.
    """
    import instaloader

    from database.affiliate_client import save_affiliate, get_existing_handles

    tags = hashtags or HASHTAGS

    yield f"Logging in to Instagram as @{os.getenv('INSTA_USERNAME', '?')}..."
    try:
        L = _login()
    except Exception as exc:
        yield f"Login failed: {exc}"
        return

    yield f"Logged in. Searching {len(tags)} hashtag(s), up to {max_per_hashtag} posts each."
    yield ""

    existing_handles = get_existing_handles()
    seen_handles: set[str] = set(existing_handles)

    total_new = 0
    total_skipped = 0

    for tag in tags:
        yield f"# #{tag}"
        new_in_tag = 0

        try:
            hashtag = instaloader.Hashtag.from_name(L.context, tag)
        except Exception as exc:
            yield f"  Could not load #{tag}: {exc}"
            continue

        count = 0
        try:
            for post in hashtag.get_posts():
                if count >= max_per_hashtag:
                    break
                count += 1

                try:
                    profile = post.owner_profile
                    handle = profile.username

                    if handle in seen_handles:
                        total_skipped += 1
                        time.sleep(0.5)
                        continue

                    if profile.is_private:
                        seen_handles.add(handle)
                        time.sleep(0.5)
                        continue

                    followers = profile.followers
                    if not (min_followers <= followers <= max_followers):
                        seen_handles.add(handle)
                        time.sleep(0.5)
                        continue

                    bio = profile.biography or ""
                    if not _is_legal_bio(bio):
                        seen_handles.add(handle)
                        time.sleep(0.5)
                        continue

                    phone = _extract_phone(bio)
                    email = _extract_email(bio)
                    name = profile.full_name or handle

                    save_affiliate({
                        "instagram_handle": handle,
                        "name": name,
                        "follower_count": followers,
                        "bio": bio[:500],
                        "phone": phone,
                        "email": email,
                        "status": "prospect",
                        "source": f"instagram_scrape:#{tag}",
                    })

                    seen_handles.add(handle)
                    total_new += 1
                    new_in_tag += 1

                    contact = phone or email or "no contact in bio"
                    yield f"  + @{handle} ({followers:,} followers) · {contact}"

                except instaloader.exceptions.QueryReturnedBadRequestException:
                    yield "  Rate limited — pausing 60s..."
                    time.sleep(60)
                except Exception as exc:
                    log.warning("Profile error: %s", exc)

                time.sleep(2)

        except instaloader.exceptions.TooManyRequestsException:
            yield f"  Instagram rate limit hit — stopping #{tag} early."
            time.sleep(30)
        except Exception as exc:
            yield f"  Error scraping #{tag}: {exc}"

        yield f"  → {new_in_tag} new prospect(s) from #{tag}"
        yield ""
        time.sleep(5)  # pause between hashtags

    yield f"Done. {total_new} new prospects saved. {total_skipped} already in DB."
