#!/usr/bin/env python3
"""
run.py -- Main entry point for Part 2.

Usage:
    python run.py              # full pipeline (fetch -> parse -> analyse -> assemble)
    python run.py --test       # quick run on MSFT only, 3 years
    python run.py --no-resume  # ignore cached results, start fresh
    python run.py --stages fetch parse        # only specific stages

Requirements:
    pip install -r requirements.txt
    ANTHROPIC_API_KEY must be set (in .env file or as environment variable)
"""

import os
import sys
import logging
from pathlib import Path

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run")


def preflight():
    """Check API key + dependencies + SEC EDGAR connectivity before starting."""
    errors = []

    # 1. Anthropic API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        errors.append(
            "ANTHROPIC_API_KEY is not set.\n"
            "  -> Create .env file with: ANTHROPIC_API_KEY=sk-ant-...\n"
            "  -> Get a key at: https://console.anthropic.com/account/keys"
        )

    # 2. Required packages
    missing = []
    for pkg in ["requests", "bs4", "anthropic", "pandas", "tqdm", "lxml"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        errors.append(
            f"Missing packages: {', '.join(missing)}\n"
            "  -> Run: pip install -r requirements.txt"
        )

    # 3. SEC EDGAR connectivity
    if not missing:
        import requests
        try:
            r = requests.get(
                "https://data.sec.gov/submissions/CIK0000320193.json",
                headers={"User-Agent": "Part2 Research Bot research@example.com"},
                timeout=10,
            )
            if r.status_code != 200:
                errors.append(
                    f"SEC EDGAR returned HTTP {r.status_code}.\n"
                    "  -> Check internet connectivity to data.sec.gov"
                )
        except requests.exceptions.RequestException as e:
            errors.append(
                f"Cannot reach data.sec.gov: {e}\n"
                "  -> Check internet connectivity / firewall."
            )

    if errors:
        print("\n[FAIL]  Pre-flight check failed:\n")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}\n")
        sys.exit(1)

    print("[ok]  Pre-flight checks passed.\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Part 2 -- Proxy ESG analysis pipeline")
    parser.add_argument("--test", action="store_true",
                        help="Run on MSFT only (3 years) to verify setup")
    parser.add_argument("--no-resume", action="store_true",
                        help="Re-run from scratch, ignoring cached results")
    parser.add_argument("--stages", nargs="+",
                        choices=["fetch", "parse", "analyse", "assemble"],
                        help="Run only specific stages")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()

    if not args.skip_preflight:
        preflight()

    if args.test:
        print("[TEST MODE]  MSFT only, years 2016/2020/2024\n")
        import companies as comp_mod
        comp_mod.COMPANIES = [c for c in comp_mod.COMPANIES if c["ticker"] == "MSFT"]
        comp_mod.YEARS     = [2016, 2020, 2024]

    resume = not args.no_resume
    stages = set(args.stages or ["fetch", "parse", "analyse", "assemble"])

    from pipeline import (stage_fetch, stage_parse, stage_analyse, stage_assemble,
                          coverage_report, OUT_DIR)

    fr = pr = an = None
    if "fetch"    in stages: fr = stage_fetch(resume)
    if "parse"    in stages: pr = stage_parse(fr, resume)
    if "analyse"  in stages: an = stage_analyse(pr, resume)
    if "assemble" in stages:
        df = stage_assemble(pr, an)
        coverage_report(df)

    print(f"\n[OK]  Done. Outputs in: {OUT_DIR}/")
    print( "   part2_dataset.csv          -- full dataset (with text)")
    print( "   part2_dataset_no_text.csv  -- dataset without text columns")
    print( "   part2_dataset.json         -- JSON format")
    print( "   coverage_report.json       -- gap summary")
    print( "   fetch_manifest.json        -- per-record fetch log")


if __name__ == "__main__":
    main()
