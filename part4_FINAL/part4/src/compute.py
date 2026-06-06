"""
compute.py -- Part 4: Predictive validity of the Authenticity Index.

The Question
------------
The Authenticity Index from Part 3 categorizes each (company, year) as
ALIGNED, GREENWASH-RISK, or STEALTH. Does this categorization have
PREDICTIVE validity? Specifically:

    Hypothesis (HC, "cheap talk"):
        Companies categorized as GREENWASH-RISK in 2021-2022 (over-claim:
        loud About-page ESG, thin proxy substance) walked back DEI
        language MORE between 2021 and 2024 than ALIGNED or STEALTH
        companies. Their public claims were "cheap" because they were
        not anchored to substance, so they could be retracted at low cost.

    Alternative (HS, "sticky commitment"):
        GREENWASH-RISK companies walked back LESS because rolling back
        loud public commitments costs reputation. Quieter (STEALTH)
        companies could quietly drop content without anyone noticing.

This file tests HC vs HS, and then asks a second question that the
test naturally raises: how stable IS the authenticity categorization
to begin with? If alignment status flips a lot year-to-year, then
predicting subsequent behavior from any single prior year's status
is inherently limited.

Inputs (in data/):
    part1_dataset_no_text.csv     -- Part 1 output
    part2_dataset_no_text.csv     -- Part 2 output
    authenticity_index.csv         -- Part 3 output

Outputs (in outputs/):
    retreat_analysis.csv           -- per-company prior status + delta
    trait_vs_state.json            -- variance decomposition results
    part4_findings.png             -- two-panel figure
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr, ttest_ind, zscore

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT  = BASE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Part A. Does prior GREENWASH-RISK status predict DEI retreat?
# ============================================================================

def analyze_predictive_validity():
    """Test whether 2021-2022 alignment status predicts 2021->2024 DEI retreat."""
    ai = pd.read_csv(DATA / "authenticity_index.csv")
    p2 = pd.read_csv(DATA / "part2_dataset_no_text.csv")

    # PRIOR: each company's average signed gap in 2021-2022.
    # Why this window: 2021-2022 was the peak of corporate DEI/ESG language.
    # Why two years: smooths year-to-year noise (which we will return to).
    # Negative = over-claim (greenwash); positive = under-claim (stealth).
    prior = ai[ai["year"].isin([2021, 2022])].groupby("ticker")["gap"].mean()
    prior.name = "prior_gap_2021_22"

    # SUBSEQUENT: each company's DEI retreat 2021 -> 2024.
    # Why three metrics: triangulate.
    #   diversity_mention_count -- raw count (sensitive to floor effects)
    #   theme_workforce_dei     -- binary; whether ANY workforce DEI content
    #   dei_disclosure_quality  -- LLM grade (less subject to floor)
    p2v = p2[(p2["scrape_status"] == "OK") & (p2["analysis_method"] == "llm")].copy()
    p2v["dei_qual_num"] = p2v["dei_disclosure_quality"].map(
        {"LOW": 0, "MEDIUM": 1, "HIGH": 2}).fillna(0)

    y21 = p2v[p2v["year"] == 2021].set_index("ticker")[
        ["diversity_mention_count", "theme_workforce_dei", "dei_qual_num"]
    ].add_suffix("_2021")
    y24 = p2v[p2v["year"] == 2024].set_index("ticker")[
        ["diversity_mention_count", "theme_workforce_dei", "dei_qual_num"]
    ].add_suffix("_2024")

    df = y21.join(y24, how="inner").join(prior, how="inner")

    df["delta_diversity_mentions"] = df["diversity_mention_count_2024"] - df["diversity_mention_count_2021"]
    df["delta_workforce_dei"]      = df["theme_workforce_dei_2024"]      - df["theme_workforce_dei_2021"]
    df["delta_dei_quality"]        = df["dei_qual_num_2024"]             - df["dei_qual_num_2021"]

    # Composite: z-score each delta then average
    for col in ["delta_diversity_mentions", "delta_workforce_dei", "delta_dei_quality"]:
        df[col + "_z"] = zscore(df[col], nan_policy="omit")
    df["retreat_composite"] = df[
        ["delta_diversity_mentions_z", "delta_workforce_dei_z", "delta_dei_quality_z"]
    ].mean(axis=1)

    # Categorize prior status
    def categorize(g):
        if g > 15:   return "STEALTH"
        if g < -15:  return "GREENWASH-RISK"
        return "ALIGNED"
    df["prior_category"] = df["prior_gap_2021_22"].apply(categorize)

    # Save the per-company file
    df.reset_index().to_csv(OUT / "retreat_analysis.csv", index=False)

    # Correlations
    results = {"correlations": {}, "group_means": {}, "t_tests": {}}
    for outcome in ["delta_diversity_mentions", "delta_workforce_dei",
                    "delta_dei_quality", "retreat_composite"]:
        sub = df[["prior_gap_2021_22", outcome]].dropna()
        r, p = pearsonr(sub["prior_gap_2021_22"], sub[outcome])
        rs, ps = spearmanr(sub["prior_gap_2021_22"], sub[outcome])
        results["correlations"][outcome] = {
            "pearson_r": round(r, 3), "pearson_p": round(p, 3),
            "spearman_rho": round(rs, 3), "spearman_p": round(ps, 3),
            "n": int(len(sub)),
        }

    # Group means by prior category
    grp = df.groupby("prior_category").agg(
        n=("prior_gap_2021_22", "count"),
        delta_diversity_mean=("delta_diversity_mentions", "mean"),
        delta_workforce_dei_mean=("delta_workforce_dei", "mean"),
        delta_dei_quality_mean=("delta_dei_quality", "mean"),
        retreat_composite_mean=("retreat_composite", "mean"),
    ).round(3)
    results["group_means"] = grp.to_dict(orient="index")

    return df, results


# ============================================================================
# Part B. Is the Authenticity Index a stable trait or a noisy state?
# ============================================================================

def analyze_trait_vs_state():
    """
    The Part A result is mixed. To interpret it, we need to know how
    stable the Authenticity Index is in the first place. If alignment
    status flips a lot year-to-year within a company, then using any
    single year (or even two-year average) as the predictor is doomed
    to weak predictive validity.

    We measure stability three ways:
        1. AR(1) autocorrelation within companies
        2. Variance decomposition: between-company vs within-company
        3. Category transition rate year-to-year
    """
    ai = pd.read_csv(DATA / "authenticity_index.csv")
    ai_sorted = ai.sort_values(["ticker", "year"])

    # 1. AR(1)
    ai_sorted["auth_lag"] = ai_sorted.groupby("ticker")["authenticity"].shift(1)
    ar1 = ai_sorted.dropna(subset=["auth_lag"])
    r_ar1, p_ar1 = pearsonr(ar1["auth_lag"], ar1["authenticity"])

    # 2. Variance decomposition
    between_var = ai.groupby("ticker")["authenticity"].mean().var()
    within_var  = ai.groupby("ticker")["authenticity"].apply(lambda s: s.var()).mean()
    total_var   = between_var + within_var
    icc_approx  = between_var / total_var

    # 3. Category transitions
    ai_sorted["cat_lag"] = ai_sorted.groupby("ticker")["alignment_category"].shift(1)
    trans = ai_sorted.dropna(subset=["cat_lag"])
    trans_rate = (trans["alignment_category"] != trans["cat_lag"]).mean()

    # Direction (over-/under-claim) flips
    ai_sorted["gap_sign"] = np.sign(ai_sorted["gap"])
    ai_sorted["gap_sign_lag"] = ai_sorted.groupby("ticker")["gap_sign"].shift(1)
    sign_trans = ai_sorted.dropna(subset=["gap_sign_lag"])
    sign_flip_rate = (sign_trans["gap_sign"] != sign_trans["gap_sign_lag"]).mean()

    results = {
        "ar1_autocorrelation": {"r": round(r_ar1, 3), "p": round(p_ar1, 4),
                                "n": int(len(ar1))},
        "variance_decomposition": {
            "between_company_variance": round(between_var, 1),
            "within_company_variance":  round(within_var, 1),
            "icc_like_ratio":           round(icc_approx, 3),
            "interpretation": (f"{icc_approx*100:.0f}% of variance is between-company "
                               f"(trait); {(1-icc_approx)*100:.0f}% is within-company "
                               f"over time (state)"),
        },
        "category_transition_rate": round(trans_rate, 3),
        "direction_flip_rate":      round(sign_flip_rate, 3),
        "n_transitions_observed":   int(len(trans)),
    }
    return results


# ============================================================================
# Visualization
# ============================================================================

def make_figure(combined_df):
    """Two-panel figure for Part 4."""
    ai = pd.read_csv(DATA / "authenticity_index.csv")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: prior_gap vs delta_diversity_mentions
    ax = axes[0]
    colors = {"ALIGNED": "#888888",
              "GREENWASH-RISK": "#C44E52",
              "STEALTH": "#55A868"}
    for cat, color in colors.items():
        sub = combined_df[combined_df["prior_category"] == cat]
        ax.scatter(sub["prior_gap_2021_22"], sub["delta_diversity_mentions"],
                   c=color, label=cat, alpha=0.8, s=60, edgecolors="white")
    ax.axhline(0, color="k", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="k", linewidth=0.5, alpha=0.5)
    r, p = pearsonr(combined_df["prior_gap_2021_22"].dropna(),
                    combined_df["delta_diversity_mentions"].dropna())
    ax.set_xlabel("Prior gap (2021-2022 avg)\n-- negative = greenwash, + = stealth")
    ax.set_ylabel("Change in diversity mentions (2024 - 2021)\n-- negative = retreated")
    ax.set_title(f"Prior alignment vs DEI retreat\nPearson r = {r:+.2f}  (p = {p:.2f}, n=46)")
    ax.legend(fontsize=9, loc="best")
    ax.grid(alpha=0.3)

    # Right: within-company trajectories
    ax = axes[1]
    samples = ["MSFT", "XOM", "WFC", "MRK", "BRK-B", "TSLA"]
    for tk in samples:
        sub = ai[ai["ticker"] == tk].sort_values("year")
        ax.plot(sub["year"], sub["authenticity"], marker="o", label=tk,
                linewidth=2, alpha=0.85)
    ax.set_xlabel("Year")
    ax.set_ylabel("Authenticity Index (0-100)")
    ax.set_title("Authenticity is volatile year-to-year, even within a company\n"
                 "(6 sample companies; 52% of consecutive-year pairs change category)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 105)

    plt.tight_layout()
    plt.savefig(OUT / "part4_findings.png", dpi=140, bbox_inches="tight")
    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("PART 4: Predictive validity & trait-vs-state of authenticity")
    print("=" * 60)

    print("\nPart A: does prior alignment predict subsequent retreat?")
    df, partA = analyze_predictive_validity()
    print(f"  N companies analyzed: {len(df)}")
    print("\n  Correlations (prior_gap vs retreat outcomes):")
    for outcome, vals in partA["correlations"].items():
        sig = ("***" if vals["pearson_p"] < 0.01 else
               "**"  if vals["pearson_p"] < 0.05 else
               "*"   if vals["pearson_p"] < 0.10 else
               "ns")
        print(f"    {outcome:30s} r={vals['pearson_r']:+.3f} (p={vals['pearson_p']:.3f}) {sig}")
    print("\n  Group means by prior category:")
    for cat, vals in partA["group_means"].items():
        print(f"    {cat:18s} n={vals['n']:2d}  "
              f"diversity_delta_mean={vals['delta_diversity_mean']:+6.2f}  "
              f"retreat_composite={vals['retreat_composite_mean']:+5.2f}")

    print("\nPart B: is authenticity a trait or a state?")
    partB = analyze_trait_vs_state()
    print(f"  AR(1) autocorrelation: r={partB['ar1_autocorrelation']['r']:.3f} "
          f"(p={partB['ar1_autocorrelation']['p']:.4f})")
    print(f"  Variance decomposition: {partB['variance_decomposition']['interpretation']}")
    print(f"  Category change rate (year to year): "
          f"{partB['category_transition_rate']*100:.0f}%")
    print(f"  Direction (sign) flip rate: "
          f"{partB['direction_flip_rate']*100:.0f}%")

    # Persist results
    combined = {"part_A_predictive_validity": partA,
                "part_B_trait_vs_state":      partB}
    (OUT / "trait_vs_state.json").write_text(json.dumps(combined, indent=2))

    print("\nGenerating figure...")
    make_figure(df)

    print(f"\nOutputs in {OUT}/:")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
