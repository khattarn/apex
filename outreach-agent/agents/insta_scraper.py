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

# Search terms — used with Instagram's profile/top search
SEARCH_QUERIES = [
    "indian advocate",
    "advocate india",
    "lawyer india",
    "high court advocate",
    "supreme court advocate",
    "vakil",
    "legal india",
    "advocate delhi",
    "advocate mumbai",
    "advocate bangalore",
    "advocate chennai",
    "advocate kolkata",
    "bar council india",
    "legal advice india",
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


def _login():
    """
    Authenticate instaloader via browser session cookie (most reliable).

    Priority:
      1. INSTA_SESSION_ID env var — sessionid cookie from instagram.com (works everywhere)
      2. Username + password — blocked by Instagram checkpoints on datacenter IPs
    """
    import instaloader

    username = os.getenv("INSTA_USERNAME", "leaglebeagle")

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

    session_id = os.getenv("INSTA_SESSION_ID", "")
    if session_id:
        # Inject browser cookie — bypasses all checkpoint/IP restrictions
        L.context._session.cookies.set("sessionid", session_id, domain=".instagram.com")
        L.context.username = username
        # Verify it works
        try:
            import instaloader
            instaloader.Profile.from_username(L.context, username)
            log.info("Authenticated via INSTA_SESSION_ID cookie")
            return L
        except Exception as exc:
            raise RuntimeError(f"INSTA_SESSION_ID cookie is invalid or expired: {exc}")

    # Fallback: password (will fail on Railway due to checkpoint)
    password = os.getenv("INSTA_PASSWORD", "")
    if not password:
        raise RuntimeError(
            "INSTA_SESSION_ID not set. "
            "Go to instagram.com in your browser as @leaglebeagle → F12 → "
            "Application → Cookies → find 'sessionid' → copy its value → "
            "set INSTA_SESSION_ID=<value> in Railway environment variables."
        )
    L.login(username, password)
    return L


def scrape(
    queries: list[str] | None = None,
    max_per_query: int = 30,
    min_followers: int = MIN_FOLLOWERS,
    max_followers: int = MAX_FOLLOWERS,
) -> Generator[str, None, None]:
    """
    Scrape Instagram for legal influencer prospects via profile search.
    Yields log lines for SSE streaming.
    Saves new prospects to the affiliates table.
    """
    import instaloader

    from database.affiliate_client import save_affiliate, get_existing_handles

    search_queries = queries or SEARCH_QUERIES

    yield f"Logging in to Instagram as @{os.getenv('INSTA_USERNAME', '?')}..."
    try:
        L = _login()
    except Exception as exc:
        yield f"Login failed: {exc}"
        return

    yield f"Logged in. Searching {len(search_queries)} query/queries, up to {max_per_query} profiles each."
    yield ""

    existing_handles = get_existing_handles()
    seen_handles: set[str] = set(existing_handles)

    total_new = 0
    total_skipped = 0

    for query in search_queries:
        yield f"# \"{query}\""
        new_in_query = 0

        try:
            results = instaloader.TopSearchResults(L.context, query)
            profiles = list(results.get_profiles())
        except Exception as exc:
            yield f"  Search failed for \"{query}\": {exc}"
            continue

        count = 0
        for profile in profiles:
            if count >= max_per_query:
                break

            try:
                handle = profile.username

                if handle in seen_handles:
                    total_skipped += 1
                    continue

                seen_handles.add(handle)

                if profile.is_private:
                    continue

                followers = profile.followers
                if not (min_followers <= followers <= max_followers):
                    continue

                bio = profile.biography or ""
                if not _is_legal_bio(bio):
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
                    "source": f"instagram_search:{query}",
                })

                total_new += 1
                new_in_query += 1
                count += 1

                contact = phone or email or "no contact in bio"
                yield f"  + @{handle} ({followers:,} followers) · {contact}"

            except instaloader.exceptions.TooManyRequestsException:
                yield "  Rate limited — pausing 60s..."
                time.sleep(60)
            except Exception as exc:
                log.warning("Profile error for %s: %s", handle if 'handle' in dir() else '?', exc)

            time.sleep(1.5)

        yield f"  → {new_in_query} new prospect(s) for \"{query}\""
        yield ""
        time.sleep(4)

    yield f"Done. {total_new} new prospects saved. {total_skipped} already in DB."
