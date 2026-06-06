"""
pipeline.py  --  Four-stage orchestrator.

Stages:
  1. scrape   -- Wayback CDX + HTML fetch
  2. extract  -- Text extraction from raw HTML
  3. analyse  -- LLM thematic analysis
  4. assemble -- Build final CSV / JSON dataset
"""

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

BASE      = Path(__file__).resolve().parent.parent
RAW_DIR   = BASE / "data" / "raw"
META_DIR  = BASE / "data" / "meta"
CLEAN_DIR = BASE / "data" / "clean"
AN_DIR    = BASE / "data" / "analysis"
OUT_DIR   = BASE / "outputs"

for _d in [RAW_DIR, META_DIR, CLEAN_DIR, AN_DIR, OUT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


# -- Stage 1: Scrape -----------------------------------------------------------
def stage_scrape(resume=True):
    from scraper import run_all
    log.info("=== STAGE 1: SCRAPE ===")
    results = run_all(COMPANIES, YEARS, RAW_DIR, META_DIR, resume=resume)
    (OUT_DIR / "scrape_manifest.json").write_text(json.dumps(results, indent=2))
    ok  = sum(1 for r in results if r["scrape_status"] == "OK")
    bl  = sum(1 for r in results if r["scrape_status"] == "BLOCKED")
    mis = sum(1 for r in results if r["scrape_status"] == "MISSING")
    log.info("Scrape: OK=%d  BLOCKED=%d  MISSING=%d / %d", ok, bl, mis, len(results))
    return results


# -- Stage 2: Extract ----------------------------------------------------------
def stage_extract(scrape_results=None, resume=True):
    from extractor import extract, word_count as wc
    log.info("=== STAGE 2: EXTRACT ===")

    if scrape_results is None:
        scrape_results = json.loads((OUT_DIR / "scrape_manifest.json").read_text())

    records = []
    for meta in scrape_results:
        ticker, year = meta["ticker"], meta["year"]
        cpath = CLEAN_DIR / f"{ticker}_{year}.json"

        if resume and cpath.exists():
            records.append(json.loads(cpath.read_text()))
            continue

        rec = {
            "ticker": ticker, "company_name": meta["company_name"],
            "sector": meta["sector"], "year": year,
            "scrape_status": meta["scrape_status"],
            "snapshot_ts":   meta.get("snapshot_ts"),
            "snapshot_url":  meta.get("snapshot_url"),
            "replay_url":    meta.get("replay_url"),
            "cdx_query_url": meta.get("cdx_query_url"),
            "page_text_clean": None, "word_count": 0,
            "missing_reason": meta.get("missing_reason"),
        }

        if meta["scrape_status"] == "OK" and meta.get("html_path"):
            hp = Path(meta["html_path"])
            if hp.exists():
                html = hp.read_text(encoding="utf-8", errors="replace")
                text = extract(html)
                rec["page_text_clean"] = text
                rec["word_count"]      = wc(text)

        cpath.write_text(json.dumps(rec, indent=2))
        records.append(rec)

    has_text = sum(1 for r in records if r["page_text_clean"])
    log.info("Extract: %d / %d records have text", has_text, len(records))
    return records


# -- Stage 3: Analyse ----------------------------------------------------------
def stage_analyse(clean_records=None, resume=True):
    from analyzer import run_all
    log.info("=== STAGE 3: ANALYSE ===")
    if clean_records is None:
        clean_records = [json.loads(p.read_text())
                         for p in sorted(CLEAN_DIR.glob("*.json"))]
    return run_all(clean_records, COMPANIES_BY_TICKER, AN_DIR, resume=resume)


# -- Stage 4: Assemble ---------------------------------------------------------
def stage_assemble(clean_records=None, analyses=None):
    log.info("=== STAGE 4: ASSEMBLE ===")
    if clean_records is None:
        clean_records = [json.loads(p.read_text())
                         for p in sorted(CLEAN_DIR.glob("*.json"))]
    if analyses is None:
        analyses = [json.loads(p.read_text())
                    for p in sorted(AN_DIR.glob("*.json"))]

    an_lut = {(a["ticker"], a["year"]): a for a in analyses}
    rows   = []

    for rec in clean_records:
        ticker, year = rec["ticker"], rec["year"]
        an = an_lut.get((ticker, year), {})
        themes = an.get("theme_categories") or []

        row = {
            "ticker":            ticker,
            "company_name":      rec["company_name"],
            "sector":            rec["sector"],
            "year":              year,
            "scrape_status":     rec["scrape_status"],
            "missing_reason":    rec.get("missing_reason"),
            "snapshot_ts":       rec.get("snapshot_ts"),
            "snapshot_url":      rec.get("snapshot_url"),
            "cdx_query_url":     rec.get("cdx_query_url"),
            "page_text_clean":   rec.get("page_text_clean") or "",
            "word_count":        rec.get("word_count", 0),
            "changed_from_prior":an.get("changed_from_prior"),
            "change_confidence": an.get("change_confidence"),
            "change_description":an.get("change_description"),
            "theme_categories":  "|".join(sorted(themes)),
            "dominant_theme":    an.get("dominant_theme"),
            "register":          an.get("register"),
            "analyst_notes":     an.get("analyst_notes"),
            "ngram_similarity":  an.get("ngram_similarity"),
            "analysis_method":   an.get("analysis_method"),
        }
        for t in THEMES:
            row[f"theme_{t.lower()}"] = 1 if t in themes else 0

        rows.append(row)

    df = (pd.DataFrame(rows)
            .sort_values(["sector","ticker","year"])
            .reset_index(drop=True))

    df.to_csv(OUT_DIR / "part1_dataset.csv", index=False)
    df.drop(columns=["page_text_clean"]).to_csv(
        OUT_DIR / "part1_dataset_no_text.csv", index=False)
    df.to_json(OUT_DIR / "part1_dataset.json", orient="records", indent=2)

    txt_dir = OUT_DIR / "page_texts"
    txt_dir.mkdir(exist_ok=True)
    for _, row in df.iterrows():
        if row["page_text_clean"]:
            (txt_dir / f"{row['ticker']}_{row['year']}.txt").write_text(
                row["page_text_clean"], encoding="utf-8")

    log.info("Dataset saved: %d rows x %d cols -> %s/", len(df), len(df.columns), OUT_DIR)
    return df


# -- Coverage summary ----------------------------------------------------------
def coverage_report(df: pd.DataFrame):
    total   = len(df)
    ok      = (df["scrape_status"] == "OK").sum()
    bl      = (df["scrape_status"] == "BLOCKED").sum()
    mis     = (df["scrape_status"] == "MISSING").sum()
    w_text  = (df["word_count"] > 0).sum()
    w_an    = (df["analysis_method"].notna() &
               (df["analysis_method"] != "skipped")).sum()

    print(f"\n{'-'*50}")
    print(f"  COVERAGE REPORT")
    print(f"{'-'*50}")
    print(f"  Total records   : {total}")
    print(f"  Scraped OK      : {ok}  ({100*ok/total:.1f}%)")
    print(f"  Blocked/Missing : {bl+mis}")
    print(f"  With text       : {w_text}")
    print(f"  With analysis   : {w_an}")
    print(f"{'-'*50}")

    if ok > 0:
        print(f"\n  By sector:")
        for sec, grp in df.groupby("sector"):
            n = (grp["scrape_status"] == "OK").sum()
            print(f"    {sec:28s} {n:3d}/{len(grp):3d}  ({100*n/len(grp):.0f}%)")

    report = {
        "total": total, "ok": int(ok), "blocked": int(bl),
        "missing": int(mis), "with_text": int(w_text), "with_analysis": int(w_an),
    }
    (OUT_DIR / "coverage_report.json").write_text(json.dumps(report, indent=2))
    return report


# -- CLI -----------------------------------------------------------------------
def main():
    import argparse
    p = argparse.ArgumentParser(description="Part 1 pipeline")
    p.add_argument("--stages", nargs="+",
                   choices=["scrape","extract","analyse","assemble"],
                   help="Stages to run (default: all)")
    p.add_argument("--no-resume", action="store_true")
    args = p.parse_args()

    resume  = not args.no_resume
    stages  = set(args.stages or ["scrape","extract","analyse","assemble"])

    sr = cr = an = None
    if "scrape"   in stages: sr = stage_scrape(resume)
    if "extract"  in stages: cr = stage_extract(sr, resume)
    if "analyse"  in stages: an = stage_analyse(cr, resume)
    if "assemble" in stages:
        df = stage_assemble(cr, an)
        coverage_report(df)

    log.info("Done.")


if __name__ == "__main__":
    main()
