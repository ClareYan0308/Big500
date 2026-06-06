"""
compute_index.py -- Organizational Authenticity Index for Part 3.

Joins the Part 1 dataset (stated values from About pages) with the Part 2
dataset (ESG disclosure in proxy statements) and produces an Authenticity
Index that measures how aligned what a company SAYS it values is with
what it actually DISCLOSES.

The full methodology is documented in METHODOLOGY.md. This file implements
the calculation.

Inputs (defaults; can be overridden with --part1 and --part2):
    data/part1_dataset_no_text.csv   (bundled snapshot of Part 1's output)
    data/part2_dataset_no_text.csv   (bundled snapshot of Part 2's output)

These files are also produced by Parts 1 and 2 of this project. We bundle
them in part3/data/ so Part 3 is self-contained and can be re-run without
needing Parts 1 and 2 to be sibling directories on disk. To use a
different (e.g., updated) version, pass --part1 <path> and --part2 <path>.

Outputs (written to outputs/):
    authenticity_index.csv     -- per (company, year) detailed scores
    company_summary.csv        -- per-company aggregate over all years
    distributional_stats.json  -- summary statistics for the report
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


# ---- CONSTRUCT DEFINITION --------------------------------------------------
#
# S (Stated):   share of 3 Part 1 ESG-related identity themes present on the
#               company's About page.
# A (Actual):   mean of 4 normalized Part 2 ESG-substance indicators in the
#               company's proxy statement.
#
# Each component is documented in METHODOLOGY.md.
# ---------------------------------------------------------------------------

# The 3 Part 1 themes used for the STATED measure
STATED_THEMES = [
    "theme_esg_sustainability",     # explicit ESG / sustainability framing
    "theme_stakeholder_capitalism", # stakeholder-orientation framing
    "theme_community_impact",       # community / social-responsibility framing
]

# DEI quality is encoded numerically (LOW=0, MEDIUM=0.5, HIGH=1)
DEI_QUALITY_MAP = {"LOW": 0.0, "MEDIUM": 0.5, "HIGH": 1.0}

# Cap density at 30 (the 99th percentile in the dataset) to prevent outliers
# from dominating the actual score
DENSITY_CAP = 30.0

# A gap below this threshold (in percentile points) is treated as ALIGNED
ALIGNMENT_TOLERANCE = 15.0


def load_inputs(part1_path: Path, part2_path: Path) -> tuple:
    """Load and validate the Part 1 and Part 2 datasets."""
    p1 = pd.read_csv(part1_path)
    p2 = pd.read_csv(part2_path)

    # Both must have an analysis_method == "llm" rows we can use
    p1_valid = p1[(p1["scrape_status"] == "OK") & (p1["analysis_method"] == "llm")].copy()
    p2_valid = p2[(p2["scrape_status"] == "OK") & (p2["analysis_method"] == "llm")].copy()

    print(f"  Part 1 valid records: {len(p1_valid)}")
    print(f"  Part 2 valid records: {len(p2_valid)}")
    return p1_valid, p2_valid


def compute_stated(p1: pd.DataFrame) -> pd.DataFrame:
    """
    Compute S, the STATED ESG-orientation score, from Part 1.

    S is the share of the 3 ESG-related Part 1 themes that are present
    on a company's About page in a given year.

    Range: {0, 1/3, 2/3, 1}
    """
    for col in STATED_THEMES:
        if col not in p1.columns:
            raise ValueError(f"Part 1 dataset missing required column: {col}")

    p1["S_stated"] = p1[STATED_THEMES].sum(axis=1) / len(STATED_THEMES)
    return p1[["ticker", "company_name", "sector", "year", "S_stated"]]


def compute_actual(p2: pd.DataFrame) -> pd.DataFrame:
    """
    Compute A, the ACTUAL ESG-substance score, from Part 2.

    A is the unweighted mean of 4 normalized components:
        A_density   = capped esg_keyword_density / 30
        A_explicit  = has_explicit_esg_section (binary)
        A_dei_qual  = LOW/MEDIUM/HIGH encoded as 0/0.5/1
        A_targets   = has_quantitative_targets (binary)

    Range: [0, 1]
    """
    out = p2.copy()

    # Density: cap at 30 (above this, marginal mentions add little real info)
    out["A_density"] = np.minimum(out["esg_keyword_density"].fillna(0), DENSITY_CAP) / DENSITY_CAP

    # Structural: did the company create a dedicated ESG section?
    out["A_explicit"] = out["has_explicit_esg_section"].astype(int)

    # Interpretive: LLM grade of DEI substance
    out["A_dei_qual"] = out["dei_disclosure_quality"].map(DEI_QUALITY_MAP).fillna(0.0)

    # Specificity: are there quantitative ESG targets?
    out["A_targets"] = out["has_quantitative_targets"].astype(int)

    out["A_actual"] = (out["A_density"] + out["A_explicit"]
                       + out["A_dei_qual"] + out["A_targets"]) / 4.0

    return out[["ticker", "year", "A_density", "A_explicit", "A_dei_qual",
                "A_targets", "A_actual"]]


def compute_authenticity(stated: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the per-year percentile ranks and the Authenticity Index.

    Why percentile-rank rather than raw scores:
      S and A live on different scales (S has 4 discrete values; A is
      continuous and skewed toward zero in older years). Comparing raw
      S to raw A would penalize companies for the average level of
      disclosure being lower in their year. Percentile ranking removes
      both the scale issue and the year fixed effect.

    Authenticity Index = 100 - |S_pct - A_pct|
        100 = perfectly aligned (same percentile rank on stated and actual)
        0   = maximally misaligned (e.g., 100th percentile on one, 0th on other)

    Gap = A_pct - S_pct (signed)
        positive  -> under-claim (actual > stated; STEALTH)
        negative  -> over-claim (stated > actual; GREENWASH-RISK)
        near zero -> ALIGNED
    """
    # Inner join: only company-years that have valid data in BOTH datasets
    df = stated.merge(actual, on=["ticker", "year"])

    # Per-year percentile rank for each side
    df["S_pct"] = df.groupby("year")["S_stated"].rank(pct=True) * 100
    df["A_pct"] = df.groupby("year")["A_actual"].rank(pct=True) * 100

    # Signed gap and the index itself
    df["gap"] = df["A_pct"] - df["S_pct"]
    df["authenticity"] = 100 - df["gap"].abs()

    # Three-level categorization for human interpretation
    def categorize(row):
        if abs(row["gap"]) <= ALIGNMENT_TOLERANCE:
            return "ALIGNED"
        if row["gap"] > ALIGNMENT_TOLERANCE:
            return "STEALTH (under-claim)"
        return "GREENWASH-RISK (over-claim)"

    df["alignment_category"] = df.apply(categorize, axis=1)

    # Reorder columns for readability
    cols = ["ticker", "company_name", "sector", "year",
            "S_stated", "A_density", "A_explicit", "A_dei_qual", "A_targets",
            "A_actual", "S_pct", "A_pct", "gap", "authenticity",
            "alignment_category"]
    return df[cols].sort_values(["sector", "ticker", "year"]).reset_index(drop=True)


def summarize_by_company(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-company averages across all available years."""
    g = df.groupby(["ticker", "company_name", "sector"]).agg(
        n_years=("year", "count"),
        S_avg=("S_stated", "mean"),
        A_avg=("A_actual", "mean"),
        S_pct_avg=("S_pct", "mean"),
        A_pct_avg=("A_pct", "mean"),
        gap_avg=("gap", "mean"),
        authenticity_avg=("authenticity", "mean"),
        authenticity_std=("authenticity", "std"),
    ).round(2).reset_index()

    # Dominant alignment category across the company's years
    cat_mode = df.groupby("ticker")["alignment_category"].agg(
        lambda s: s.value_counts().idxmax())
    g = g.merge(cat_mode.rename("dominant_category"),
                left_on="ticker", right_index=True)

    return g.sort_values("authenticity_avg", ascending=False).reset_index(drop=True)


def distributional_stats(df: pd.DataFrame) -> dict:
    """Summary statistics for the report."""
    stats = {
        "n_company_years":  int(len(df)),
        "n_companies":      int(df["ticker"].nunique()),
        "n_years":          int(df["year"].nunique()),
        "authenticity_index": {
            "mean":   round(df["authenticity"].mean(), 1),
            "median": round(df["authenticity"].median(), 1),
            "std":    round(df["authenticity"].std(), 1),
            "min":    round(df["authenticity"].min(), 1),
            "max":    round(df["authenticity"].max(), 1),
            "p25":    round(df["authenticity"].quantile(0.25), 1),
            "p75":    round(df["authenticity"].quantile(0.75), 1),
        },
        "category_counts": df["alignment_category"].value_counts().to_dict(),
        "by_sector": df.groupby("sector")["authenticity"].mean().round(1).to_dict(),
        "by_year":   df.groupby("year")["authenticity"].mean().round(1).to_dict(),
        "gap_signed_by_sector":  df.groupby("sector")["gap"].mean().round(1).to_dict(),
    }
    return stats


def main():
    parser = argparse.ArgumentParser(description="Compute the Authenticity Index")
    parser.add_argument("--part1", default="data/part1_dataset_no_text.csv",
                        help="Path to Part 1 dataset CSV (default: bundled copy in data/)")
    parser.add_argument("--part2", default="data/part2_dataset_no_text.csv",
                        help="Path to Part 2 dataset CSV (default: bundled copy in data/)")
    parser.add_argument("--out",   default="outputs")
    args = parser.parse_args()

    # Base is the part3 root (one level above src/), so relative defaults
    # like "../part1/..." resolve correctly when part1/ and part2/ are
    # siblings of part3/ in the project tree.
    base = Path(__file__).resolve().parent.parent
    out_dir = base / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading inputs...")
    p1, p2 = load_inputs(base / args.part1, base / args.part2)

    print("Computing STATED (S) from Part 1...")
    stated = compute_stated(p1)

    print("Computing ACTUAL (A) from Part 2...")
    actual = compute_actual(p2)

    print("Computing Authenticity Index...")
    df = compute_authenticity(stated, actual)
    print(f"  Joined: {len(df)} company-year pairs")

    print("Writing outputs...")
    df.to_csv(out_dir / "authenticity_index.csv", index=False)
    summarize_by_company(df).to_csv(out_dir / "company_summary.csv", index=False)
    stats = distributional_stats(df)
    (out_dir / "distributional_stats.json").write_text(json.dumps(stats, indent=2))

    # Print a summary
    print()
    print("=" * 60)
    print(f"  AUTHENTICITY INDEX -- {stats['n_company_years']} company-years")
    print("=" * 60)
    ai = stats["authenticity_index"]
    print(f"  Mean   : {ai['mean']}")
    print(f"  Median : {ai['median']}")
    print(f"  Range  : {ai['min']} -- {ai['max']}")
    print()
    print("  Category distribution:")
    for cat, n in stats["category_counts"].items():
        print(f"    {cat:30s}  {n}")
    print()
    print(f"  Outputs written to: {out_dir}/")


if __name__ == "__main__":
    main()
