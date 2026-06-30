from datetime import datetime
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


def is_canadian(city: str, market: str = "") -> bool:
    return (market or "").upper() == "CA" or city in CA_CITIES

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
    return _in_window(local_now(city, market), EMAIL_SEND_DAYS, EMAIL_HOUR_START, EMAIL_MINUTE_START, EMAIL_HOUR_END)


def is_wa_window(city: str, market: str = "") -> bool:
    return _in_window(local_now(city, market), WA_SEND_DAYS, WA_HOUR_START, WA_MINUTE_START, WA_HOUR_END)


def is_voice_window(city: str, market: str = "") -> bool:
    now = local_now(city, market)
    if now.weekday() not in VOICE_SEND_DAYS:
        return False
    return VOICE_HOUR_START <= now.hour < VOICE_HOUR_END


def window_description(city: str, market: str = "") -> str:
    now = local_now(city, market)
    tz_name = get_tz_name(city, market)
    return f"{now.strftime('%a %H:%M')} {tz_name}"
