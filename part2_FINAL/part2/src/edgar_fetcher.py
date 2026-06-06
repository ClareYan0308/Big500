"""
edgar_fetcher.py -- SEC EDGAR client for DEF 14A (Proxy Statement) filings.

SEC EDGAR API endpoints used:
  - Submissions index:  https://data.sec.gov/submissions/CIK{padded_cik}.json
  - Older submissions:  https://data.sec.gov/submissions/CIK{padded_cik}-submissions-{n}.json
  - Filing archive:     https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/

Rules:
  - SEC requires a descriptive User-Agent header with contact info.
  - SEC rate limits to 10 requests per second; we use a polite 0.5s sleep.
  - Form types we want: "DEF 14A" (the main proxy statement). Amendments
    (DEFA14A) and "additional materials" (DEFM14A, PRE 14A) are skipped.

Strategy:
  1. Fetch the recent submissions index for each CIK.
  2. If older filings (>1000 records) exist, fetch the additional shard files.
  3. Filter for form=="DEF 14A" within 2016-01-01 to 2024-12-31.
  4. For each calendar year, pick the single filing whose filing date is
     closest to that year's mid-point (June 30).
  5. Download the primary document HTML and save to disk.

Note on year assignment: a DEF 14A filed in March 2024 covers the
fiscal year ending in late 2023, but reflects the company's "current"
disclosure as of early 2024. We use the FILING year (calendar year of
filing date) as the dataset year.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("edgar")

# SEC requires a descriptive User-Agent. Replace with your own contact info.
USER_AGENT = "Part2 Research Bot research@example.com"

EDGAR_BASE     = "https://data.sec.gov"
ARCHIVE_BASE   = "https://www.sec.gov/Archives/edgar/data"
SUBMISSIONS_URL= EDGAR_BASE + "/submissions/CIK{cik}.json"

SLEEP_SECS = 0.6     # 0.6s -> ~1.5 req/sec, well below SEC's 10/sec limit
TIMEOUT    = 30


def _session() -> requests.Session:
    """Build a requests session with retry policy and User-Agent header."""
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=2,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = USER_AGENT
    s.headers["Accept-Encoding"] = "gzip, deflate"
    return s


SESSION = _session()


def _pad_cik(cik: str) -> str:
    """SEC URLs require a 10-digit zero-padded CIK string."""
    return str(cik).zfill(10)


def _get_json(url: str) -> Optional[dict]:
    """GET a JSON resource from SEC, with rate limiting."""
    time.sleep(SLEEP_SECS)
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        log.warning("HTTP %d for %s", r.status_code, url)
    except Exception as e:
        log.warning("Error fetching %s: %s", url, e)
    return None


def get_all_filings(cik: str) -> list:
    """
    Return ALL filings (recent + older shards) for a given CIK.
    Each filing is a dict with: accession, date, form, primaryDoc.
    """
    padded = _pad_cik(cik)
    data = _get_json(SUBMISSIONS_URL.format(cik=padded))
    if not data:
        return []

    filings_block = data.get("filings", {})
    recent = filings_block.get("recent", {})

    def _zip_recent(rec: dict) -> list:
        """Convert the parallel-array recent block into a list of dicts."""
        accs   = rec.get("accessionNumber", [])
        dates  = rec.get("filingDate", [])
        forms  = rec.get("form", [])
        docs   = rec.get("primaryDocument", [])
        result = []
        for i in range(len(accs)):
            result.append({
                "accession":   accs[i],
                "date":        dates[i],
                "form":        forms[i],
                "primaryDoc":  docs[i] if i < len(docs) else "",
            })
        return result

    all_filings = _zip_recent(recent)

    # Older filings live in separate shard files
    for shard in filings_block.get("files", []):
        shard_url = f"{EDGAR_BASE}/submissions/{shard['name']}"
        shard_data = _get_json(shard_url)
        if shard_data:
            all_filings.extend(_zip_recent(shard_data))

    return all_filings


def filter_def14a(filings: list, start_year: int = 2016, end_year: int = 2024) -> list:
    """
    Filter filings list down to DEF 14A proxy statements within the year range.
    We exclude amendments (DEFA14A, DEFM14A) and preliminary proxies (PRE 14A);
    only the definitive proxy is kept.
    """
    out = []
    for f in filings:
        if f["form"] != "DEF 14A":
            continue
        year = int(f["date"][:4])
        if year < start_year or year > end_year:
            continue
        out.append(f)
    return out


def pick_one_per_year(def14a_filings: list, years: list) -> dict:
    """
    For each target year, pick the filing whose date is closest to July 1.
    Returns {year: filing_dict}.

    Companies file DEF 14A once per year, so usually there is exactly one
    per year. The "closest to mid-year" rule handles edge cases where a
    company files two definitive proxies in one calendar year (rare).
    """
    by_year = {}
    for f in def14a_filings:
        y = int(f["date"][:4])
        by_year.setdefault(y, []).append(f)

    selected = {}
    for y in years:
        candidates = by_year.get(y, [])
        if not candidates:
            continue
        # Pick closest to July 1
        target_md = (7, 1)
        def _dist(f):
            month, day = int(f["date"][5:7]), int(f["date"][8:10])
            return abs((month - target_md[0]) * 30 + (day - target_md[1]))
        selected[y] = min(candidates, key=_dist)
    return selected


def filing_url(cik: str, accession: str, primary_doc: str) -> str:
    """Construct the direct URL to a filing's primary document."""
    acc_no_dashes = accession.replace("-", "")
    return f"{ARCHIVE_BASE}/{int(cik)}/{acc_no_dashes}/{primary_doc}"


def download_filing(cik: str, accession: str, primary_doc: str,
                    save_path: Path) -> dict:
    """
    Download one filing's primary document and save to disk.
    Returns {"status": "OK"|"FAILED", "url": str, "size": int, "error": str}
    """
    url = filing_url(cik, accession, primary_doc)
    try:
        time.sleep(SLEEP_SECS)
        r = SESSION.get(url, timeout=60)
    except Exception as e:
        return {"status": "FAILED", "url": url, "size": 0, "error": str(e)[:200]}

    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "url": url, "size": 0,
                "error": f"HTTP {r.status_code}"}

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(r.content)
    return {"status": "OK", "url": url, "size": len(r.content), "error": None}


def fetch_one(company: dict, years: list, raw_dir: Path) -> list:
    """
    For one company, get all DEF 14A filings within `years` and download them.
    Returns a list of metadata dicts (one per year, even if missing).
    """
    ticker = company["ticker"]
    cik    = company["cik"]
    log.info("[%s] cik=%s -- fetching filings index", ticker, cik)
    filings = get_all_filings(cik)
    def14a  = filter_def14a(filings, years[0], years[-1])
    log.info("[%s] found %d DEF 14A filings between %d-%d",
             ticker, len(def14a), years[0], years[-1])
    selected = pick_one_per_year(def14a, years)

    out = []
    for y in years:
        rec = {
            "ticker":          ticker,
            "company_name":    company["name"],
            "sector":          company["sector"],
            "year":            y,
            "cik":             cik,
            "accession_number":None,
            "filing_date":     None,
            "filing_url":      None,
            "primary_doc":     None,
            "doc_local_path":  None,
            "doc_size":        0,
            "scrape_status":   "MISSING",
            "missing_reason":  "no_def14a_in_year",
        }
        if y not in selected:
            out.append(rec)
            continue

        f = selected[y]
        rec.update(
            accession_number=f["accession"],
            filing_date=f["date"],
            primary_doc=f["primaryDoc"],
            filing_url=filing_url(cik, f["accession"], f["primaryDoc"]),
        )

        # Download
        out_path = raw_dir / ticker / f"{ticker}_{y}_{f['accession']}.htm"
        result = download_filing(cik, f["accession"], f["primaryDoc"], out_path)
        rec["doc_size"] = result["size"]
        if result["status"] == "OK":
            rec["doc_local_path"] = str(out_path)
            rec["scrape_status"]  = "OK"
            rec["missing_reason"] = None
            log.info("[%s %d] OK -- %d bytes -- %s", ticker, y, result["size"], f["date"])
        else:
            rec["scrape_status"]  = "FAILED"
            rec["missing_reason"] = result.get("error", "download_failed")
            log.warning("[%s %d] FAILED -- %s", ticker, y, result.get("error"))
        out.append(rec)
    return out


def run_all(companies: list, years: list, raw_dir: Path, meta_dir: Path,
            resume: bool = True) -> list:
    """
    Fetch DEF 14A for all companies and years. Saves per-record meta JSON to
    meta_dir/{ticker}_{year}.json. Returns a list of all metadata records.
    """
    from tqdm import tqdm
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    for company in tqdm(companies, desc="Companies", unit="co"):
        ticker = company["ticker"]
        # Resume: if all per-year meta files exist, skip the network call
        all_cached = True
        cached_recs = []
        for y in years:
            mp = meta_dir / f"{ticker}_{y}.json"
            if mp.exists():
                cached_recs.append(json.loads(mp.read_text()))
            else:
                all_cached = False
                break
        if resume and all_cached:
            all_records.extend(cached_recs)
            continue

        recs = fetch_one(company, years, raw_dir)
        for r in recs:
            mp = meta_dir / f"{r['ticker']}_{r['year']}.json"
            mp.write_text(json.dumps(r, indent=2))
        all_records.extend(recs)

    ok   = sum(1 for r in all_records if r["scrape_status"] == "OK")
    mis  = sum(1 for r in all_records if r["scrape_status"] != "OK")
    log.info("Fetch done: OK=%d  MISSING/FAILED=%d / %d", ok, mis, len(all_records))
    return all_records
