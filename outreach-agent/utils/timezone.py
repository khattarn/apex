from datetime import datetime, timedelta
from functools import lru_cache
import calendar
import pytz

CITY_TZ = {
    # Canada
    "Toronto": "America/Toronto", "Mississauga": "America/Toronto",
    "Brampton": "America/Toronto", "Markham": "America/Toronto",
    "Richmond Hill": "America/Toronto", "Hamilton": "America/Toronto",
    "Kitchener": "America/Toronto", "Ottawa": "America/Toronto",
    "Montreal": "America/Toronto", "Quebec City": "America/Toronto",
    "Windsor": "America/Toronto", "Barrie": "America/Toronto",
    "Halifax": "America/Halifax",
    "Winnipeg": "America/Winnipeg", "Saskatoon": "America/Regina",
    "Regina": "America/Regina",
    "Calgary": "America/Edmonton", "Edmonton": "America/Edmonton",
    "Vancouver": "America/Vancouver", "Victoria": "America/Vancouver",
    "Kelowna": "America/Vancouver", "Abbotsford": "America/Vancouver",
    # USA
    "New York": "America/New_York", "Philadelphia": "America/New_York",
    "Jacksonville": "America/New_York", "Columbus": "America/New_York",
    "Charlotte": "America/New_York", "Baltimore": "America/New_York",
    "Atlanta": "America/New_York", "Miami": "America/New_York",
    "Tampa": "America/New_York", "Raleigh": "America/New_York",
    "Cleveland": "America/New_York", "Virginia Beach": "America/New_York",
    "Indianapolis": "America/Indiana/Indianapolis",
    "Louisville": "America/Kentucky/Louisville",
    "Chicago": "America/Chicago", "Houston": "America/Chicago",
    "San Antonio": "America/Chicago", "Dallas": "America/Chicago",
    "Austin": "America/Chicago", "Fort Worth": "America/Chicago",
    "Nashville": "America/Chicago", "Memphis": "America/Chicago",
    "Milwaukee": "America/Chicago", "Minneapolis": "America/Chicago",
    "New Orleans": "America/Chicago", "Omaha": "America/Chicago",
    "Denver": "America/Denver", "Colorado Springs": "America/Denver",
    "Phoenix": "America/Phoenix", "Tucson": "America/Phoenix",
    "Los Angeles": "America/Los_Angeles", "San Diego": "America/Los_Angeles",
    "San Jose": "America/Los_Angeles", "San Francisco": "America/Los_Angeles",
    "Seattle": "America/Los_Angeles", "Portland": "America/Los_Angeles",
    "Las Vegas": "America/Los_Angeles", "Sacramento": "America/Los_Angeles",
    "Long Beach": "America/Los_Angeles", "Fresno": "America/Los_Angeles",
    # Australia
    "Sydney": "Australia/Sydney", "Canberra": "Australia/Sydney",
    "Newcastle": "Australia/Sydney", "Wollongong": "Australia/Sydney",
    "Melbourne": "Australia/Melbourne", "Geelong": "Australia/Melbourne",
    "Ballarat": "Australia/Melbourne", "Bendigo": "Australia/Melbourne",
    "Brisbane": "Australia/Brisbane", "Gold Coast": "Australia/Brisbane",
    "Sunshine Coast": "Australia/Brisbane", "Cairns": "Australia/Brisbane",
    "Toowoomba": "Australia/Brisbane", "Townsville": "Australia/Brisbane",
    "Rockhampton": "Australia/Brisbane", "Mackay": "Australia/Brisbane",
    "Adelaide": "Australia/Adelaide",
    "Perth": "Australia/Perth", "Mandurah": "Australia/Perth",
    "Hobart": "Australia/Hobart", "Launceston": "Australia/Hobart",
    "Darwin": "Australia/Darwin",
    # UK
    "London": "Europe/London", "Birmingham": "Europe/London",
    "Manchester": "Europe/London", "Glasgow": "Europe/London",
    "Leeds": "Europe/London", "Liverpool": "Europe/London",
    "Sheffield": "Europe/London", "Edinburgh": "Europe/London",
    "Bristol": "Europe/London", "Leicester": "Europe/London",
    "Coventry": "Europe/London", "Bradford": "Europe/London",
    "Nottingham": "Europe/London", "Cardiff": "Europe/London",
    "Belfast": "Europe/London", "Southampton": "Europe/London",
    "Reading": "Europe/London", "Aberdeen": "Europe/London",
    "Oxford": "Europe/London", "Cambridge": "Europe/London",
    "Brighton": "Europe/London", "Exeter": "Europe/London",
    "Norwich": "Europe/London",
}

MARKET_TZ = {
    "CA": "America/Toronto",
    "US": "America/New_York",
    "AU": "Australia/Sydney",
    "UK": "Europe/London",
}

CA_CITIES = {
    "Toronto", "Mississauga", "Brampton", "Markham", "Richmond Hill",
    "Hamilton", "Kitchener", "Ottawa", "Montreal", "Quebec City",
    "Windsor", "Barrie", "Halifax", "Winnipeg", "Saskatoon", "Regina",
    "Calgary", "Edmonton", "Vancouver", "Victoria", "Kelowna", "Abbotsford",
}

US_CITIES = {
    "New York", "Philadelphia", "Jacksonville", "Columbus", "Charlotte",
    "Baltimore", "Atlanta", "Miami", "Tampa", "Raleigh", "Cleveland",
    "Virginia Beach", "Indianapolis", "Louisville", "Chicago", "Houston",
    "San Antonio", "Dallas", "Austin", "Fort Worth", "Nashville", "Memphis",
    "Milwaukee", "Minneapolis", "New Orleans", "Omaha", "Denver",
    "Colorado Springs", "Phoenix", "Tucson", "Los Angeles", "San Diego",
    "San Jose", "San Francisco", "Seattle", "Portland", "Las Vegas",
    "Sacramento", "Long Beach", "Fresno",
}

# ── Fixed-date public holidays ────────────────────────────────────────────────
# (month, day) → set of markets where outreach is blocked (treated as weekend)
HOLIDAYS_FIXED = {
    (1, 1):   {"CA", "US"},  # New Year's Day
    (6, 19):  {"US"},        # Juneteenth
    (7, 1):   {"CA"},        # Canada Day
    (7, 4):   {"US"},        # Independence Day
    (9, 30):  {"CA"},        # National Day for Truth & Reconciliation
    (11, 11): {"CA", "US"},  # Remembrance Day (CA) / Veterans Day (US)
    (12, 25): {"CA", "US"},  # Christmas Day
    (12, 26): {"CA"},        # Boxing Day
}

# ── Floating-date helpers ─────────────────────────────────────────────────────

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> tuple:
    """(month, day) of the nth occurrence of weekday in month.
    weekday: 0=Mon … 6=Sun.  n=1=first, n=2=second, n=-1=last."""
    if n > 0:
        first_dow = datetime(year, month, 1).weekday()
        day = 1 + (weekday - first_dow) % 7 + (n - 1) * 7
    else:  # last occurrence
        last_day = calendar.monthrange(year, month)[1]
        last_dow = datetime(year, month, last_day).weekday()
        day = last_day - (last_dow - weekday) % 7
    return (month, day)


def _easter(year: int) -> tuple:
    """(month, day) of Easter Sunday — Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return (month, day + 1)


@lru_cache(maxsize=4)
def _floating_holidays(year: int) -> dict:
    """Return {(month, day): set-of-markets} for all floating holidays in year."""
    result: dict = {}

    def add(md: tuple, markets: set) -> None:
        result.setdefault(md, set()).update(markets)

    easter_m, easter_d = _easter(year)
    easter_dt = datetime(year, easter_m, easter_d)

    # Canada floating holidays
    good_friday = easter_dt - timedelta(days=2)
    add((good_friday.month, good_friday.day), {"CA"})        # Good Friday

    easter_monday = easter_dt + timedelta(days=1)
    add((easter_monday.month, easter_monday.day), {"CA"})    # Easter Monday

    add(_nth_weekday(year, 2, 0, 3), {"CA"})                 # Family Day (3rd Mon Feb)

    may24 = datetime(year, 5, 24)                            # Victoria Day: last Mon ≤ May 24
    victoria = may24 - timedelta(days=may24.weekday())
    add((victoria.month, victoria.day), {"CA"})

    add(_nth_weekday(year, 8, 0, 1), {"CA"})                 # Civic Holiday (1st Mon Aug)
    add(_nth_weekday(year, 9, 0, 1), {"CA", "US"})           # Labour / Labor Day (1st Mon Sep)
    add(_nth_weekday(year, 10, 0, 2), {"CA"})                # Thanksgiving CA (2nd Mon Oct)

    # US floating holidays
    add(_nth_weekday(year, 1, 0, 3), {"US"})                 # MLK Day (3rd Mon Jan)
    add(_nth_weekday(year, 2, 0, 3), {"US"})                 # Presidents' Day (3rd Mon Feb)
    add(_nth_weekday(year, 5, 0, -1), {"US"})                # Memorial Day (last Mon May)
    add(_nth_weekday(year, 10, 0, 2), {"US"})                # Columbus Day (2nd Mon Oct)
    add(_nth_weekday(year, 11, 3, 4), {"US"})                # Thanksgiving US (4th Thu Nov)

    return result


def is_canadian(city: str, market: str = "") -> bool:
    return (market or "").upper() == "CA" or city in CA_CITIES


def is_american(city: str, market: str = "") -> bool:
    return (market or "").upper() == "US" or city in US_CITIES


def _is_holiday(city: str, market: str = "") -> bool:
    """Return True if today is a public holiday for this city/market."""
    now = local_now(city, market)
    key = (now.month, now.day)
    affected = HOLIDAYS_FIXED.get(key, set()) | _floating_holidays(now.year).get(key, set())
    if not affected:
        return False
    if "CA" in affected and is_canadian(city, market):
        return True
    if "US" in affected and is_american(city, market):
        return True
    return False


# ── Send-window constants ─────────────────────────────────────────────────────

# Email: Mon–Fri, 8:30 AM – 7 PM local
EMAIL_SEND_DAYS = {0, 1, 2, 3, 4}
EMAIL_HOUR_START = 8
EMAIL_MINUTE_START = 30
EMAIL_HOUR_END = 19

# WhatsApp: Mon–Fri, 10 AM – 5:30 PM local
# Cron fires at :15 past each hour; first eligible tick is 10:15 AM, last is 5:15 PM
WA_SEND_DAYS = {0, 1, 2, 3, 4}
WA_HOUR_START = 10
WA_MINUTE_START = 0
WA_HOUR_END = 18  # hour >= 18 → outside; 17:15 ✓, 18:15 ✗

# Outbound voice calls: Mon–Fri, 11 AM – 5 PM local time
VOICE_SEND_DAYS = {0, 1, 2, 3, 4}
VOICE_HOUR_START = 11
VOICE_HOUR_END = 17


def get_tz_name(city: str, market: str = "") -> str:
    # UK is a single timezone nationally, and city names can collide with
    # identically-named cities elsewhere (e.g. "Newcastle" also exists in
    # NSW Australia and in Washington State, both mapped in CITY_TZ) — when
    # the market is confidently UK, skip the ambiguous city lookup entirely.
    if (market or "").upper() == "UK":
        return "Europe/London"
    return CITY_TZ.get(city) or MARKET_TZ.get(market, "America/Toronto")


def local_now(city: str, market: str = "") -> datetime:
    tz = pytz.timezone(get_tz_name(city, market))
    return datetime.now(tz)


def _in_window(now: datetime, allowed_days: set, hour_start: int, minute_start: int, hour_end: int) -> bool:
    if now.weekday() not in allowed_days:
        return False
    if now.hour < hour_start:
        return False
    if now.hour == hour_start and now.minute < minute_start:
        return False
    if now.hour >= hour_end:
        return False
    return True


def is_email_window(city: str, market: str = "") -> bool:
    if _is_holiday(city, market):
        return False
    return _in_window(local_now(city, market), EMAIL_SEND_DAYS, EMAIL_HOUR_START, EMAIL_MINUTE_START, EMAIL_HOUR_END)


def is_wa_window(city: str, market: str = "") -> bool:
    if _is_holiday(city, market):
        return False
    return _in_window(local_now(city, market), WA_SEND_DAYS, WA_HOUR_START, WA_MINUTE_START, WA_HOUR_END)


def is_voice_window(city: str, market: str = "") -> bool:
    if _is_holiday(city, market):
        return False
    now = local_now(city, market)
    if now.weekday() not in VOICE_SEND_DAYS:
        return False
    return VOICE_HOUR_START <= now.hour < VOICE_HOUR_END


def window_description(city: str, market: str = "") -> str:
    now = local_now(city, market)
    tz_name = get_tz_name(city, market)
    return f"{now.strftime('%a %H:%M')} {tz_name}"
