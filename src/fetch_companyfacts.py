#!/usr/bin/env python3
"""
Fetch SEC EDGAR XBRL companyfacts JSON.

Usage:
  python fetch_companyfacts.py --cik 0000320193 --user-agent "Test User test@example.com"
  python fetch_companyfacts.py --ticker AAPL --user-agent "Test User test@example.com"
"""

import argparse
import json
import sys
import time
from pathlib import Path
import re

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("ERROR: This script requires 'requests' library. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

SEC_BASE = "https://data.sec.gov"
COMPANYFACTS_PATH_TMPL = "/api/xbrl/companyfacts/CIK{cik}.json"
# Public mapping of tickers -> CIK (periodically updated by SEC):
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"

def make_session(user_agent: str, timeout: float = 15.0) -> requests.Session:
    if not user_agent or "@" not in user_agent:
        raise ValueError("Per SEC guidelines, User-Agent must include a contact email.")
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.request = _with_timeout(s.request, timeout)
    return s

def _with_timeout(request_func, timeout):
    def wrapper(method, url, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return request_func(method, url, **kwargs)
    return wrapper

def zero_pad_cik(cik: str) -> str:
    cik_digits = re.sub(r"\D", "", cik or "")
    if not cik_digits:
        raise ValueError("CIK must contain digits.")
    return cik_digits.zfill(10)

def resolve_cik_from_ticker(session: requests.Session, ticker: str) -> str:
    """
    Returns 10-digit zero-padded CIK for a given ticker (case-insensitive).
    """
    r = session.get(TICKER_MAP_URL)
    r.raise_for_status()
    data = r.json()
    # Format is { "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    ticker_upper = ticker.strip().upper()
    for _, entry in data.items():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker not found in SEC mapping: {ticker}")

def fetch_companyfacts(session: requests.Session, cik_10: str) -> dict:
    url = f"{SEC_BASE}{COMPANYFACTS_PATH_TMPL.format(cik=cik_10)}"
    # polite small delay to respect fair-use (esp. when batching)
    time.sleep(0.2)
    r = session.get(url)
    if r.status_code == 404:
        raise FileNotFoundError(f"No companyfacts found for CIK {cik_10}")
    r.raise_for_status()
    return r.json()

def main():
    ap = argparse.ArgumentParser(description="Fetch SEC companyfacts (XBRL) JSON.")
    ap.add_argument("--cik", help="10-digit CIK (can be unpadded; digits only).")
    ap.add_argument("--ticker", help="Stock ticker (e.g., AAPL).")
    ap.add_argument("--user-agent", required=True,
                    help='Required: e.g., "Your Name your.email@example.com"')
    ap.add_argument("--out", help="Output file path (defaults to companyfacts_<CIK>.json)")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON to stdout")
    args = ap.parse_args()

    if not (args.cik or args.ticker):
        ap.error("Provide either --cik or --ticker")

    session = make_session(args.user_agent)

    if args.ticker:
        cik_10 = resolve_cik_from_ticker(session, args.ticker)
    else:
        cik_10 = zero_pad_cik(args.cik)

    data = fetch_companyfacts(session, cik_10)

    out_path = Path(args.out) if args.out else Path(f"companyfacts_{cik_10}.json")
    out_path.write_text(json.dumps(data, indent=2 if args.pretty else None))
    print(f"Wrote {out_path}")

    if args.pretty:
        # Also echo a tiny snippet to confirm shape
        entity = data.get("entityName")
        facts_keys = list((data.get("facts") or {}).keys())[:5]
        print("\nSummary:")
        print(f"  entityName: {entity}")
        print(f"  taxonomies (sample): {facts_keys}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
