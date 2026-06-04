import re
import requests
import dns.resolver
import dns.exception

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

_SKIP_PREFIXES = {
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'webmaster', 'postmaster', 'bounce', 'unsubscribe',
    'newsletter', 'notifications', 'alerts', 'mailer-daemon',
    'abuse', 'spam', 'help', 'support', 'admin',
}

_SKIP_DOMAINS = {
    'domain.com', 'example.com', 'yourdomain.com', 'yoursite.com',
    'test.com', 'email.com', 'mail.com', 'website.com', 'mysite.com',
    'company.com', 'business.com', 'practicedesk.com', 'sentry.io',
    'wixpress.com', 'squarespace.com', 'wordpress.com',
}

_SKIP_DOMAIN_SUFFIXES = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
    '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
)

_HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; ApexBot/1.0)'}

_mx_cache: dict[str, tuple[bool, str]] = {}


def validate_email(email: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    reason is '' when valid, or a human-readable explanation when invalid.
    """
    email = email.lower().strip().rstrip('.')

    # 1 — syntax
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
        return False, f"invalid syntax"

    if '@' not in email:
        return False, "missing @ symbol"

    prefix, domain = email.split('@', 1)

    # 2 — generic prefix
    if prefix in _SKIP_PREFIXES:
        return False, f"generic prefix '{prefix}'"

    # 3 — placeholder domain
    if domain in _SKIP_DOMAINS:
        return False, f"placeholder domain '{domain}'"

    # 4 — file extension false-positive
    if any(domain.endswith(s) for s in _SKIP_DOMAIN_SUFFIXES):
        return False, f"domain looks like a file path (ends with {domain.rsplit('.', 1)[-1]})"

    # 5 — MX record check (cached per domain)
    if domain not in _mx_cache:
        _mx_cache[domain] = _check_mx(domain)
    mx_ok, mx_reason = _mx_cache[domain]
    if not mx_ok:
        return False, mx_reason

    return True, ""


def _check_mx(domain: str) -> tuple[bool, str]:
    try:
        answers = dns.resolver.resolve(domain, 'MX', lifetime=5)
        if answers:
            return True, ""
        return False, f"no MX records for '{domain}'"
    except dns.resolver.NXDOMAIN:
        return False, f"domain '{domain}' does not exist (NXDOMAIN)"
    except dns.resolver.NoAnswer:
        # Some domains use implicit MX (A record fallback) — try A record
        try:
            dns.resolver.resolve(domain, 'A', lifetime=5)
            return True, ""
        except Exception:
            return False, f"no MX or A record for '{domain}'"
    except dns.resolver.Timeout:
        return False, f"DNS timeout for '{domain}'"
    except dns.exception.DNSException as exc:
        return False, f"DNS error for '{domain}': {exc}"


def scrape_email(website_url: str, timeout: int = 6) -> str | None:
    """
    Silent version — returns first valid email or None.
    Used by the pipeline (no debug output needed).
    """
    result, _ = scrape_email_debug(website_url, timeout=timeout)
    return result


def scrape_email_debug(website_url: str, timeout: int = 6) -> tuple[str | None, list[str]]:
    """
    Returns (best_email | None, debug_lines).
    debug_lines contains a human-readable trace of every candidate found
    and why it was accepted or rejected.
    """
    logs: list[str] = []

    if not website_url:
        logs.append("    no website URL — skipped")
        return None, logs

    base = website_url.rstrip('/')
    pages = [base, f"{base}/contact", f"{base}/contact-us"]
    all_candidates: list[str] = []

    for url in pages:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
            if resp.status_code != 200:
                logs.append(f"    {url} → HTTP {resp.status_code}")
                continue
            found = _extract_raw(resp.text)
            logs.append(f"    {url} → {len(found)} candidate(s) found")
            all_candidates.extend(found)
        except requests.exceptions.Timeout:
            logs.append(f"    {url} → timeout")
        except Exception as exc:
            logs.append(f"    {url} → error: {exc}")

    if not all_candidates:
        logs.append("    no email candidates on any page")
        return None, logs

    # Deduplicate preserving order
    seen: set[str] = set()
    unique = []
    for e in all_candidates:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    best: str | None = None
    for email in unique:
        valid, reason = validate_email(email)
        if valid:
            logs.append(f"    ✓  {email} — valid (MX confirmed)")
            if best is None:
                best = email
        else:
            logs.append(f"    ✗  {email} — rejected: {reason}")

    if best is None:
        logs.append("    no valid email survived validation")

    return best, logs


def _extract_raw(html: str) -> list[str]:
    """Return lowercased, deduplicated email candidates from HTML."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in _EMAIL_RE.findall(html):
        email = raw.lower().rstrip('.')
        if email not in seen:
            seen.add(email)
            result.append(email)
    return result
