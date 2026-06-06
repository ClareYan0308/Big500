#!/usr/bin/env python3
"""
run.py  --  Single entry point for Part 1.

Usage:
    python run.py              # full pipeline (scrape -> extract -> analyse -> assemble)
    python run.py --test       # test run: MSFT only, 3 years (2016, 2020, 2024)
    python run.py --no-resume  # ignore cached results, start fresh
    python run.py --stages scrape extract   # run only specific stages

Requirements:
    pip install -r requirements.txt
    ANTHROPIC_API_KEY must be set (in .env file or as environment variable)
"""

import os
import sys
import logging
from pathlib import Path

# -- Load .env if present ------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass   # python-dotenv not installed -- rely on environment variable

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run")


def preflight():
    """Check requirements before starting."""
    errors = []

    # 1. Anthropic API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        errors.append(
            "ANTHROPIC_API_KEY is not set.\n"
            "  -> Create .env file with: ANTHROPIC_API_KEY=sk-ant-...\n"
            "  -> Get a key at: https://console.anthropic.com/account/keys"
        )

    # 2. Required packages
    missing_pkgs = []
    for pkg in ["requests","trafilatura","bs4","anthropic","pandas","tqdm"]:
        try:
            __import__(pkg)
        except ImportError:
            missing_pkgs.append(pkg)
    if missing_pkgs:
        errors.append(
            f"Missing packages: {', '.join(missing_pkgs)}\n"
            "  -> Run: pip install -r requirements.txt"
        )

    # 3. Internet connectivity to archive.org
    if not missing_pkgs:   # only check if requests is installed
        import requests
        try:
            r = requests.get("https://web.archive.org/cdx/search/cdx?limit=0",
                             timeout=10)
            if r.status_code == 403 and r.headers.get("x-deny-reason") == "host_not_allowed":
                errors.append(
                    "web.archive.org is blocked by your network policy.\n"
                    "  -> Try a VPN, or run on a cloud server (AWS/GCP/etc.)"
                )
        except requests.ConnectionError:
            errors.append(
                "Cannot reach web.archive.org (connection refused or DNS failure).\n"
                "  -> Check your internet connection, or try a VPN if in China."
            )

    if errors:
        print("\n[FAIL]  Pre-flight check failed:\n")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}\n")
        sys.exit(1)

    print("[ok]  Pre-flight checks passed.\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Part 1 -- About-page scraping pipeline")
    parser.add_argument("--test",      action="store_true",
                        help="Run on MSFT only (3 years) to verify setup")
    parser.add_argument("--no-resume", action="store_true",
                        help="Re-run from scratch, ignoring cached results")
    parser.add_argument("--stages",    nargs="+",
                        choices=["scrape","extract","analyse","assemble"],
                        help="Run only specific stages")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()

    if not args.skip_preflight:
        preflight()

    from companies import COMPANIES, YEARS

    if args.test:
        print("*  TEST MODE -- MSFT only, years 2016/2020/2024\n")
        companies = [c for c in COMPANIES if c["ticker"] == "MSFT"]
        years     = [2016, 2020, 2024]
    else:
        companies = COMPANIES
        years     = YEARS

    resume = not args.no_resume
    stages = set(args.stages or ["scrape","extract","analyse","assemble"])

    from pipeline import (stage_scrape, stage_extract,
                          stage_analyse, stage_assemble, coverage_report,
                          RAW_DIR, META_DIR, CLEAN_DIR, AN_DIR, OUT_DIR)

    # Temporarily override COMPANIES/YEARS for test mode
    if args.test:
        import pipeline as pl
        import companies as comp_mod
        orig_companies = comp_mod.COMPANIES
        orig_years     = comp_mod.YEARS
        comp_mod.COMPANIES = companies
        comp_mod.YEARS     = years

    sr = cr = an = None
    try:
        if "scrape"   in stages: sr = stage_scrape(resume)
        if "extract"  in stages: cr = stage_extract(sr, resume)
        if "analyse"  in stages: an = stage_analyse(cr, resume)
        if "assemble" in stages:
            df = stage_assemble(cr, an)
            coverage_report(df)
    finally:
        if args.test:
            comp_mod.COMPANIES = orig_companies
            comp_mod.YEARS     = orig_years

    print(f"\n[ok]  Done.  Outputs in: {OUT_DIR}/")
    print( "   part1_dataset.csv         -- full dataset")
    print( "   part1_dataset_no_text.csv -- dataset without raw text column")
    print( "   part1_dataset.json        -- JSON format")
    print( "   coverage_report.json      -- gap summary")


if __name__ == "__main__":
    main()
