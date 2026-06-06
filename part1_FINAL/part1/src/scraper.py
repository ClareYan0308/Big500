"""
scraper.py  --  Wayback Machine CDX API scraper.

CDX API endpoint:  https://web.archive.org/cdx/search/cdx
Snapshot fetch:    https://web.archive.org/web/{timestamp}id_/{url}

The id_ modifier returns raw archived HTML without the Wayback toolbar overlay.
Snapshot selection: among all 200-status snapshots in a calendar year, pick the
one whose date is closest to July 1 (mid-year anchor).
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("scraper")

CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
WAYBACK_BASE = "https://web.archive.org/web"
CDX_SLEEP    = 0.8   # seconds between CDX requests (polite rate)
FETCH_SLEEP  = 2.0   # seconds between HTML fetches
MIN_HTML_LEN = 500   # chars; below this treat a fetch as empty

# Global flag: once we detect archive.org is blocked, skip remaining requests
_CDX_BLOCKED = False


def _make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=2,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = (
        "SP500-AboutPage-Research/1.0 (academic; contact: research@example.com)"
    )
    return s


SESSION = _make_session()


def _build_cdx_url(domain: str, path: str, year: int) -> str:
    """Return the full CDX query URL (for documentation/reproducibility)."""
    params = {
        "url":            f"{domain}{path}",
        "matchType":      "prefix",
        "output":         "json",
        "fl":             "timestamp,original,statuscode,digest",
        "filter":         ["statuscode:200", "mimetype:text/html"],
        "from":           f"{year}0101",
        "to":             f"{year}1231",
        "limit":          "50",
        "collapse":       "timestamp:8",
        "resolveRevisits":"true",
    }
    return f"{CDX_ENDPOINT}?{urlencode(params, doseq=True)}"


def cdx_query(domain: str, path: str, year: int) -> dict:
    """
    Query CDX for one domain+path in a calendar year.
    Returns dict with keys: status, timestamps [(ts, url), ...], cdx_url, error.
    """
    global _CDX_BLOCKED
    cdx_url = _build_cdx_url(domain, path, year)

    if _CDX_BLOCKED:
        return {"status": "BLOCKED_403", "timestamps": [],
                "cdx_url": cdx_url, "error": "archive.org blocked (cached)"}

    time.sleep(CDX_SLEEP)
    try:
        resp = SESSION.get(
            CDX_ENDPOINT,
            params={
                "url": f"{domain}{path}", "matchType": "prefix",
                "output": "json",
                "fl": "timestamp,original,statuscode,digest",
                "filter": ["statuscode:200", "mimetype:text/html"],
                "from": f"{year}0101", "to": f"{year}1231",
                "limit": "50", "collapse": "timestamp:8",
                "resolveRevisits": "true",
            },
            timeout=30,
        )
    except requests.ConnectionError as exc:
        return {"status": "NETWORK_ERROR", "timestamps": [],
                "cdx_url": cdx_url, "error": str(exc)[:200]}

    if resp.status_code == 403:
        deny = resp.headers.get("x-deny-reason", "")
        _CDX_BLOCKED = (deny == "host_not_allowed")
        return {"status": "BLOCKED_403", "timestamps": [],
                "cdx_url": cdx_url, "error": f"HTTP 403: {deny}"}

    if resp.status_code != 200:
        return {"status": f"ERROR_{resp.status_code}", "timestamps": [],
                "cdx_url": cdx_url, "error": f"HTTP {resp.status_code}"}

    try:
        rows = resp.json()
    except ValueError:
        return {"status": "PARSE_ERROR", "timestamps": [],
                "cdx_url": cdx_url, "error": "JSON parse failed"}

    if len(rows) < 2:   # row 0 is header; no data rows means no snapshots
        return {"status": "NO_HIT", "timestamps": [],
                "cdx_url": cdx_url, "error": None}

    header   = rows[0]
    ts_idx   = header.index("timestamp") if "timestamp" in header else 0
    url_idx  = header.index("original")  if "original"  in header else 1
    timestamps = [(r[ts_idx], r[url_idx]) for r in rows[1:] if r]

    return {"status": "OK", "timestamps": timestamps,
            "cdx_url": cdx_url, "error": None}


def pick_closest(timestamps: list, year: int) -> Optional[tuple]:
    """Return (timestamp, original_url) closest to {year}-07-01."""
    if not timestamps:
        return None
    target = int(f"{year}0701000000")
    return min(timestamps, key=lambda t: abs(int(t[0]) - target))


def fetch_html(timestamp: str, original_url: str) -> dict:
    """
    Fetch raw archived HTML via the id_ (no-toolbar) replay URL.
    Returns dict: status, html, replay_url, error.
    """
    global _CDX_BLOCKED
    if _CDX_BLOCKED:
        replay_url = f"{WAYBACK_BASE}/{timestamp}id_/{original_url}"
        return {"status": "BLOCKED_403", "html": None,
                "replay_url": replay_url, "error": "archive.org blocked"}

    replay_url = f"{WAYBACK_BASE}/{timestamp}id_/{original_url}"
    time.sleep(FETCH_SLEEP)

    try:
        resp = SESSION.get(replay_url, timeout=45, allow_redirects=True)
    except requests.ConnectionError as exc:
        return {"status": "NETWORK_ERROR", "html": None,
                "replay_url": replay_url, "error": str(exc)[:200]}

    if resp.status_code == 403:
        deny = resp.headers.get("x-deny-reason", "")
        _CDX_BLOCKED = (deny == "host_not_allowed")
        return {"status": "BLOCKED_403", "html": None,
                "replay_url": resp.url, "error": f"HTTP 403: {deny}"}

    if resp.status_code != 200:
        return {"status": f"ERROR_{resp.status_code}", "html": None,
                "replay_url": resp.url, "error": ""}

    # Guard: redirect must stay within web.archive.org
    if not resp.url.startswith("https://web.archive.org"):
        return {"status": "REDIRECT_ESCAPED", "html": None,
                "replay_url": resp.url, "error": f"Left Wayback: {resp.url}"}

    html = resp.text
    if len(html) < MIN_HTML_LEN:
        return {"status": "HTML_TOO_SHORT", "html": None,
                "replay_url": resp.url, "error": f"{len(html)} chars"}

    return {"status": "OK", "html": html, "replay_url": resp.url, "error": None}


def scrape_one(company: dict, year: int, raw_dir: Path) -> dict:
    """
    Collect the best snapshot for (company, year).
    Tries URL hints in priority order; returns a metadata dict.
    """
    ticker    = company["ticker"]
    domain    = company["domain"]
    all_hints = list(zip([domain]*len(company["url_hints"]), company["url_hints"]))
    if "domain_alt" in company:
        alt = company["domain_alt"]
        all_hints += [(alt, p) for p in company.get("url_hints_alt", [])]

    result = {
        "ticker": ticker, "company_name": company["name"],
        "sector": company["sector"], "year": year,
        "scrape_status": "MISSING",
        "missing_reason": "all_hints_exhausted",
        "snapshot_ts": None, "snapshot_url": None,
        "replay_url": None, "cdx_query_url": None,
        "html_path": None, "html_length": 0,
    }

    for dom, path in all_hints:
        cdx  = cdx_query(dom, path, year)
        result["cdx_query_url"] = cdx["cdx_url"]

        if cdx["status"] in ("BLOCKED_403", "NETWORK_ERROR"):
            result.update(scrape_status="BLOCKED", missing_reason=cdx["error"])
            log.warning("[%s %d] CDX %s", ticker, year, cdx["status"])
            return result   # no point trying more hints; whole API is blocked

        if cdx["status"] != "OK":
            log.info("[%s %d] CDX %s -> %s%s", ticker, year, cdx["status"], dom, path)
            continue

        best = pick_closest(cdx["timestamps"], year)
        if not best:
            log.info("[%s %d] NO_HIT -> %s%s", ticker, year, dom, path)
            result["missing_reason"] = "NO_CDX_HIT"
            continue

        ts, orig = best
        fetch = fetch_html(ts, orig)

        if fetch["status"] in ("BLOCKED_403", "NETWORK_ERROR"):
            result.update(scrape_status="BLOCKED",
                          missing_reason=fetch["error"],
                          snapshot_ts=ts, snapshot_url=orig,
                          replay_url=fetch["replay_url"])
            return result

        if fetch["status"] == "OK":
            out_dir  = raw_dir / ticker
            out_dir.mkdir(parents=True, exist_ok=True)
            html_path = out_dir / f"{ticker}_{year}.html"
            html_path.write_text(fetch["html"], encoding="utf-8", errors="replace")

            result.update(
                scrape_status="OK", missing_reason=None,
                snapshot_ts=ts, snapshot_url=orig,
                replay_url=fetch["replay_url"],
                html_path=str(html_path),
                html_length=len(fetch["html"]),
            )
            log.info("[%s %d] [ok]  ts=%s  %d chars  %s%s",
                     ticker, year, ts, len(fetch["html"]), dom, path)
            return result

        log.info("[%s %d] fetch %s -> %s%s", ticker, year, fetch["status"], dom, path)
        result["missing_reason"] = fetch["status"]

    return result


def run_all(companies: list, years: list, raw_dir: Path,
            meta_dir: Path, resume: bool = True) -> list:
    """
    Scrape all (company, year) pairs.  Saves per-record JSON to meta_dir.
    Returns list of metadata dicts.
    """
    from tqdm import tqdm
    meta_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    pairs   = [(c, y) for c in companies for y in years]
    results = []

    with tqdm(pairs, desc="Scraping", unit="record") as bar:
        for company, year in bar:
            ticker    = company["ticker"]
            meta_path = meta_dir / f"{ticker}_{year}.json"
            bar.set_postfix(company=ticker, year=year)

            if resume and meta_path.exists():
                results.append(json.loads(meta_path.read_text()))
                continue

            meta = scrape_one(company, year, raw_dir)
            meta_path.write_text(json.dumps(meta, indent=2))
            results.append(meta)

    ok  = sum(1 for r in results if r["scrape_status"] == "OK")
    bl  = sum(1 for r in results if r["scrape_status"] == "BLOCKED")
    mis = sum(1 for r in results if r["scrape_status"] == "MISSING")
    log.info("Scrape done  OK=%d  BLOCKED=%d  MISSING=%d / %d",
             ok, bl, mis, len(results))
    return results
