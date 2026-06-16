"""
Local Instagram scraper runner — run this from your Windows laptop.

Instagram blocks Railway's datacenter IPs from GraphQL endpoints.
Running locally uses your home IP which is not blocked.

Usage:
    cd outreach-agent
    python scrape_local.py                  # 30 prospects per seed account
    python scrape_local.py --max 50         # more prospects per seed account
    python scrape_local.py --seeds livelaw.in barandbench   # specific seeds only

Requirements:
    pip install instaloader python-dotenv supabase
    INSTA_SESSION_ID must be set in .env (see below)

To get your session ID:
    1. Log in to instagram.com as @leaglebeagle in Chrome
    2. F12 → Application tab → Cookies → https://www.instagram.com
    3. Find "sessionid" → copy its Value
    4. Put it in outreach-agent/.env:  INSTA_SESSION_ID=<paste here>
"""

import argparse
import sys
import os

# Load .env from the same directory
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from agents.insta_scraper import scrape, SEED_ACCOUNTS


def main():
    parser = argparse.ArgumentParser(description="Scrape Instagram for affiliate prospects")
    parser.add_argument("--max", type=int, default=30, help="Max prospects per seed account (default: 30)")
    parser.add_argument("--min-followers", type=int, default=2000)
    parser.add_argument("--max-followers", type=int, default=500000)
    parser.add_argument("--seeds", nargs="*", default=None,
                        help="Seed account handles to scrape (default: all 6)")
    args = parser.parse_args()

    seeds = args.seeds or SEED_ACCOUNTS
    print(f"Scraping followees of: {', '.join(f'@{s}' for s in seeds)}")
    print(f"Follower range: {args.min_followers:,} – {args.max_followers:,}")
    print(f"Max per seed: {args.max}")
    print("-" * 60)

    try:
        for line in scrape(
            seed_accounts=seeds,
            max_per_query=args.max,
            min_followers=args.min_followers,
            max_followers=args.max_followers,
        ):
            print(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
