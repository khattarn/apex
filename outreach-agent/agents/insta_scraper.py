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

# Seed accounts — major Indian legal Instagram accounts that follow hundreds of
# practising advocates. We scrape their followee lists and filter for influencers.
SEED_ACCOUNTS = [
    "livelaw.in",        # biggest Indian legal news site
    "barandbench",       # major Indian legal news
    "scobserver_india",  # Supreme Court observer
    "the.legal.brief",   # Indian legal content
    "lawctopus",         # Indian law school / legal career
    "latestlaws.com",    # Indian legislation news
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


def _is_legal_profile(handle: str, bio: str) -> bool:
    """Accept if username OR bio contains a legal keyword."""
    text = (handle + " " + bio).lower()
    return any(kw in text for kw in LEGAL_KEYWORDS)


_COOKIE_INSTRUCTIONS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 INSTA_SESSION_ID not set (or expired)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Instagram no longer allows password login from scripts.
 You must use a browser session cookie instead.

 Steps:
   1. Open Chrome and log in to instagram.com as @leaglebeagle
   2. Press F12 → Application tab → Cookies (left sidebar)
      → click https://www.instagram.com
   3. Find the row named  sessionid  — copy its entire Value
      (it looks like: 24176945060%3AVR7Sz...long string...)
   4. Open  outreach-agent/.env  and add this line:
        INSTA_SESSION_ID=<paste the value here>
   5. Run the scraper again:  python scrape_local.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def _login():
    """Authenticate instaloader via browser session cookie (required — password login is blocked)."""
    import instaloader

    username = os.getenv("INSTA_USERNAME", "leaglebeagle")
    session_id = os.getenv("INSTA_SESSION_ID", "").strip()

    if not session_id:
        raise RuntimeError(_COOKIE_INSTRUCTIONS)

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

    # Inject browser cookie — this is the only method that works reliably
    L.context._session.cookies.set("sessionid", session_id, domain=".instagram.com")
    L.context.username = username

    # Verify with a known public account (instagram.com itself)
    try:
        instaloader.Profile.from_username(L.context, "instagram")
        log.info("Authenticated via INSTA_SESSION_ID cookie")
        return L
    except Exception as exc:
        raise RuntimeError(
            f"Session cookie is invalid or expired. Re-copy sessionid from your browser.\n"
            f"Error: {exc}\n"
            f"{_COOKIE_INSTRUCTIONS}"
        )


def scrape(
    seed_accounts: list[str] | None = None,
    max_per_query: int = 30,
    min_followers: int = MIN_FOLLOWERS,
    max_followers: int = MAX_FOLLOWERS,
) -> Generator[str, None, None]:
    """
    Scrape Instagram for legal influencer prospects by iterating the followee
    lists of major Indian legal news accounts. Yields log lines for SSE streaming.
    Saves new prospects to the affiliates table.
    """
    import instaloader

    from database.affiliate_client import save_affiliate, get_existing_handles

    seeds = seed_accounts or SEED_ACCOUNTS

    yield f"Logging in to Instagram as @{os.getenv('INSTA_USERNAME', '?')}..."
    try:
        L = _login()
    except Exception as exc:
        yield f"Login failed: {exc}"
        return

    yield f"Logged in. Scanning followee lists of {len(seeds)} seed account(s), up to {max_per_query} prospects each."
    yield ""

    existing_handles = get_existing_handles()
    seen_handles: set[str] = set(existing_handles)

    total_new = 0
    total_skipped = 0

    for seed_handle in seeds:
        yield f"# @{seed_handle}"
        new_from_seed = 0

        try:
            seed_profile = instaloader.Profile.from_username(L.context, seed_handle)
        except Exception as exc:
            yield f"  Could not load @{seed_handle}: {exc}"
            continue

        yield f"  Loaded @{seed_handle} ({seed_profile.followees:,} following)"
        count = 0

        try:
            for profile in seed_profile.get_followees():
                if count >= max_per_query:
                    break

                handle = profile.username

                if handle in seen_handles:
                    total_skipped += 1
                    time.sleep(0.3)
                    continue

                seen_handles.add(handle)

                try:
                    if profile.is_private:
                        time.sleep(0.3)
                        continue

                    followers = profile.followers
                    if not (min_followers <= followers <= max_followers):
                        time.sleep(0.3)
                        continue

                    bio = profile.biography or ""
                    if not _is_legal_profile(handle, bio):
                        time.sleep(0.3)
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
                        "source": f"followee_of:@{seed_handle}",
                    })

                    total_new += 1
                    new_from_seed += 1
                    count += 1

                    contact = phone or email or "no contact in bio"
                    yield f"  + @{handle} ({followers:,} followers) · {contact}"

                except instaloader.exceptions.TooManyRequestsException:
                    yield "  Rate limited — pausing 90s..."
                    time.sleep(90)
                except Exception as exc:
                    log.warning("Profile error for @%s: %s", handle, exc)

                time.sleep(1.5)

        except instaloader.exceptions.TooManyRequestsException:
            yield f"  Rate limited while scanning @{seed_handle} — moving on."
            time.sleep(30)
        except Exception as exc:
            yield f"  Error scanning @{seed_handle}: {exc}"

        yield f"  → {new_from_seed} new prospect(s) from @{seed_handle}"
        yield ""
        time.sleep(5)

    yield f"Done. {total_new} new prospects saved. {total_skipped} already in DB."
