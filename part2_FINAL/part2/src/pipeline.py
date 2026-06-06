"""
pipeline.py -- Four-stage orchestrator for Part 2.

Stages:
  1. fetch   -- Download DEF 14A proxy statements from SEC EDGAR
  2. parse   -- Extract clean text and ESG sections; compute NLP signals
  3. analyse -- LLM-based ESG analysis (themes, change detection, register)
  4. assemble-- Build final CSV/JSON dataset

All stages are resumable. Re-running `python run.py` after an interruption
will skip cached records and only process new ones.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from companies import COMPANIES, COMPANIES_BY_TICKER, YEARS
from analyzer import THEMES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")

BASE       = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE / "data" / "raw"      # raw HTML filings
META_DIR   = BASE / "data" / "meta"     # per-record fetch metadata
PARSED_DIR = BASE / "data" / "parsed"   # parsed text + NLP signals
AN_DIR     = BASE / "data" / "analysis" # per-record LLM analysis
OUT_DIR    = BASE / "outputs"

for _d in [RAW_DIR, META_DIR, PARSED_DIR, AN_DIR, OUT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


# ---- Stage 1: Fetch -----------------------------------------------------------
def stage_fetch(resume: bool = True) -> list:
    from edgar_fetcher import run_all
    log.info("=== STAGE 1: FETCH from SEC EDGAR ===")
    results = run_all(COMPANIES, YEARS, RAW_DIR, META_DIR, resume=resume)
    (OUT_DIR / "fetch_manifest.json").write_text(json.dumps(results, indent=2))
    ok  = sum(1 for r in results if r["scrape_status"] == "OK")
    bad = sum(1 for r in results if r["scrape_status"] != "OK")
    log.info("Fetch: OK=%d  MISSING/FAILED=%d / %d", ok, bad, len(results))
    return results


# ---- Stage 2: Parse -----------------------------------------------------------
def stage_parse(fetch_results: list = None, resume: bool = True) -> list:
    from proxy_parser import parse_proxy
    log.info("=== STAGE 2: PARSE proxy HTML ===")

    if fetch_results is None:
        fetch_results = json.loads((OUT_DIR / "fetch_manifest.json").read_text())

    from tqdm import tqdm
    parsed_records = []
    for meta in tqdm(fetch_results, desc="Parsing", unit="filing"):
        ticker, year = meta["ticker"], meta["year"]
        parsed_path = PARSED_DIR / f"{ticker}_{year}.json"

        if resume and parsed_path.exists():
            parsed_records.append(json.loads(parsed_path.read_text()))
            continue

        # Start with all the metadata fields
        rec = {**meta, "proxy_text_clean": None, "esg_section_text": None,
               "esg_section_word_count": 0, "has_explicit_esg_section": False,
               "total_word_count": 0, "climate_mention_count": 0,
               "diversity_mention_count": 0, "governance_mention_count": 0,
               "net_zero_target_year": None, "pct_women_board": None,
               "has_quantitative_targets": False}

        if meta["scrape_status"] == "OK" and meta.get("doc_local_path"):
            html_path = Path(meta["doc_local_path"])
            if html_path.exists():
                try:
                    html = html_path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    log.warning("[%s %d] read error: %s", ticker, year, e)
                    html = ""
                if html:
                    parsed = parse_proxy(html)
                    rec.update(parsed)

        # Write per-record parsed JSON (without huge text payloads in meta)
        # We keep the full text in the parsed record on disk
        parsed_path.write_text(json.dumps(rec, indent=2))
        parsed_records.append(rec)

    with_text = sum(1 for r in parsed_records if r.get("proxy_text_clean"))
    with_esg  = sum(1 for r in parsed_records if r.get("has_explicit_esg_section"))
    log.info("Parse: %d/%d have text, %d/%d have explicit ESG section",
             with_text, len(parsed_records), with_esg, len(parsed_records))
    return parsed_records


# ---- Stage 3: Analyse ---------------------------------------------------------
def stage_analyse(parsed_records: list = None, resume: bool = True) -> list:
    from analyzer import run_all
    log.info("=== STAGE 3: LLM ANALYSIS ===")
    if parsed_records is None:
        parsed_records = [json.loads(p.read_text())
                          for p in sorted(PARSED_DIR.glob("*.json"))]
    return run_all(parsed_records, COMPANIES_BY_TICKER, AN_DIR, resume=resume)


# ---- Stage 4: Assemble --------------------------------------------------------
def stage_assemble(parsed_records: list = None, analyses: list = None) -> pd.DataFrame:
    log.info("=== STAGE 4: ASSEMBLE dataset ===")
    if parsed_records is None:
        parsed_records = [json.loads(p.read_text())
                          for p in sorted(PARSED_DIR.glob("*.json"))]
    if analyses is None:
        analyses = [json.loads(p.read_text())
                    for p in sorted(AN_DIR.glob("*.json"))]

    an_lut = {(a["ticker"], a["year"]): a for a in analyses}
    rows = []

    for rec in parsed_records:
        ticker, year = rec["ticker"], rec["year"]
        an = an_lut.get((ticker, year), {})
        themes = an.get("esg_themes") or []
        # ESG keyword density: mentions per 1000 words of (ESG section OR full text)
        denom = max(rec.get("esg_section_word_count", 0) or rec.get("total_word_count", 0), 1)
        esg_total_mentions = (rec.get("climate_mention_count", 0)
                               + rec.get("diversity_mention_count", 0)
                               + rec.get("governance_mention_count", 0))
        density = round(1000 * esg_total_mentions / denom, 2) if denom > 0 else 0.0

        row = {
            # Identifiers
            "ticker":            ticker,
            "company_name":      rec["company_name"],
            "sector":            rec["sector"],
            "year":              year,
            # Filing metadata
            "cik":               rec.get("cik"),
            "accession_number":  rec.get("accession_number"),
            "filing_date":       rec.get("filing_date"),
            "filing_url":        rec.get("filing_url"),
            "scrape_status":     rec.get("scrape_status"),
            "missing_reason":    rec.get("missing_reason"),
            # Document content
            "doc_size_bytes":    rec.get("doc_size", 0),
            "total_word_count":  rec.get("total_word_count", 0),
            "esg_section_word_count":  rec.get("esg_section_word_count", 0),
            "has_explicit_esg_section":rec.get("has_explicit_esg_section", False),
            "proxy_text_clean":  rec.get("proxy_text_clean") or "",
            "esg_section_text":  rec.get("esg_section_text") or "",
            # Classical-NLP signals
            "climate_mention_count":   rec.get("climate_mention_count", 0),
            "diversity_mention_count": rec.get("diversity_mention_count", 0),
            "governance_mention_count":rec.get("governance_mention_count", 0),
            "esg_keyword_density":     density,
            "net_zero_target_year":    rec.get("net_zero_target_year"),
            "pct_women_board":         rec.get("pct_women_board"),
            "has_quantitative_targets":rec.get("has_quantitative_targets", False),
            # LLM analysis
            "esg_themes":             "|".join(sorted(themes)),
            "climate_commitment":     an.get("climate_commitment"),
            "dei_disclosure_quality": an.get("dei_disclosure_quality"),
            "changed_from_prior":     an.get("changed_from_prior"),
            "change_confidence":      an.get("change_confidence"),
            "change_summary":         an.get("change_summary"),
            "register":               an.get("register"),
            "analyst_notes":          an.get("analyst_notes"),
            "ngram_similarity":       an.get("ngram_similarity"),
            "analysis_method":        an.get("analysis_method"),
        }
        # Add binary theme columns (one per allowed theme)
        for t in THEMES:
            row[f"theme_{t.lower()}"] = 1 if t in themes else 0

        rows.append(row)

    df = (pd.DataFrame(rows)
          .sort_values(["sector", "ticker", "year"])
          .reset_index(drop=True))

    df.to_csv(OUT_DIR / "part2_dataset.csv", index=False)
    df.drop(columns=["proxy_text_clean", "esg_section_text"]).to_csv(
        OUT_DIR / "part2_dataset_no_text.csv", index=False)
    df.to_json(OUT_DIR / "part2_dataset.json", orient="records", indent=2)

    # Save individual ESG section text files
    txt_dir = OUT_DIR / "esg_sections"
    txt_dir.mkdir(exist_ok=True)
    for _, row in df.iterrows():
        if row["esg_section_text"]:
            (txt_dir / f"{row['ticker']}_{row['year']}.txt").write_text(
                row["esg_section_text"], encoding="utf-8")

    log.info("Dataset saved: %d rows x %d cols -> %s/", len(df), len(df.columns), OUT_DIR)
    return df


def coverage_report(df: pd.DataFrame) -> dict:
    """Print and save a coverage summary."""
    total   = len(df)
    ok      = (df["scrape_status"] == "OK").sum()
    bad     = total - ok
    w_text  = (df["total_word_count"] > 0).sum()
    w_esg   = df["has_explicit_esg_section"].sum()
    w_an    = (df["analysis_method"].notna() & (df["analysis_method"] != "skipped")).sum()

    print(f"\n{'-' * 56}")
    print(f"  PART 2 COVERAGE REPORT")
    print(f"{'-' * 56}")
    print(f"  Total records       : {total}")
    print(f"  Fetched OK          : {ok}  ({100 * ok / total:.1f}%)")
    print(f"  Missing/failed      : {bad}")
    print(f"  With proxy text     : {w_text}")
    print(f"  With explicit ESG   : {w_esg}  ({100 * w_esg / max(w_text,1):.0f}% of texted)")
    print(f"  With LLM analysis   : {w_an}")
    print(f"{'-' * 56}")

    if ok > 0:
        print(f"\n  By sector:")
        for sec, grp in df.groupby("sector"):
            n = (grp["scrape_status"] == "OK").sum()
            print(f"    {sec:28s} {n:3d}/{len(grp):3d}  ({100 * n / len(grp):.0f}%)")

    report = {
        "total": int(total), "ok": int(ok), "missing_or_failed": int(bad),
        "with_text": int(w_text), "with_explicit_esg": int(w_esg),
        "with_analysis": int(w_an),
    }
    (OUT_DIR / "coverage_report.json").write_text(json.dumps(report, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description="Part 2 pipeline")
    p.add_argument("--stages", nargs="+",
                   choices=["fetch", "parse", "analyse", "assemble"],
                   help="Stages to run (default: all)")
    p.add_argument("--no-resume", action="store_true",
                   help="Re-run from scratch, ignoring cached results")
    args = p.parse_args()

    resume = not args.no_resume
    stages = set(args.stages or ["fetch", "parse", "analyse", "assemble"])

    fr = pr = an = None
    if "fetch"    in stages: fr = stage_fetch(resume)
    if "parse"    in stages: pr = stage_parse(fr, resume)
    if "analyse"  in stages: an = stage_analyse(pr, resume)
    if "assemble" in stages:
        df = stage_assemble(pr, an)
        coverage_report(df)

    log.info("Done.")


if __name__ == "__main__":
    main()
