# Part 4 -- A Proposal: Does the Authenticity Index Predict Behavior?

A follow-up analysis on the Part 3 Authenticity Index. We tested whether
prior greenwash-risk status predicts subsequent DEI retreat (it doesn't,
robustly), then asked why -- and found that the Index itself is more of a
state than a trait. The full analytical writeup is in
[FINDINGS.md](FINDINGS.md). This README covers the standard 5 sections.

---

## 1. What I did

I picked one substantive question that the Authenticity Index from Part
3 raises naturally:

> When DEI-related language retreated in proxy statements between
> 2021 and 2024 (a Part 2 finding), were the retreaters the companies
> that had previously over-claimed (GREENWASH-RISK in Part 3)?

The pipeline:

1. **Predictor**: For each company, computed the average signed gap
   in 2021-2022 (where negative = over-claim, positive = under-claim).
2. **Outcomes**: For each company, computed 2021 -> 2024 deltas in
   three DEI signals: raw diversity-keyword count, binary
   workforce-DEI theme presence, LLM-graded DEI disclosure quality.
3. **Tested** the relationship using Pearson and Spearman
   correlations and group-mean comparisons.
4. **Result**: weak and inconsistent. No metric showed a strong
   relationship; the strongest was a marginal r = -0.25 (p = 0.09) in
   the "sticky commitment" direction, but the picture differs across
   metrics.
5. **Follow-up**: investigated why prediction was weak by measuring
   the within-company stability of the Authenticity Index itself.
   Found that it is mostly a state (82% of variance is within-company
   year-to-year), not a trait (18% is between-company).
6. **Reframed** the implications for how the Part 3 index should be
   used.

---

## 2. Why

**Why this question.** The brief asks for something "genuinely
interesting." After Part 3 produced an index that worked
cross-sectionally (companies we expected to flag as GREENWASH or
STEALTH did get flagged), the obvious next question was whether the
index works predictively. If a 2021-2022 GREENWASH-RISK label tells
you nothing about 2023-2024 behavior, the index is descriptive
rather than predictive. We did not know the answer before running it.

**Why DEI retreat specifically.** It is the cleanest natural
experiment in our data. Part 2 documented the retreat. The
June 2023 SCOTUS affirmative-action ruling is a well-defined break
point. The 2021 and 2024 proxies are 3 years apart and bracket the
ruling. We have the same companies in both periods.

**Why a hybrid hypothesis frame.** "Cheap talk" and "sticky
commitment" are both plausible. By specifying both up front, we
forced the analysis to be exploratory -- whatever direction the data
moved, we would learn something. If we had only specified one
hypothesis, we would have biased ourselves toward finding it.

**Why three retreat metrics.** Each captures something different
(raw count, binary presence, qualitative grade) and is subject to
different biases (floor effects, categorical coarseness, LLM
non-determinism). Triangulating reduces the chance that any one
metric is misleading us. As it turned out, the three metrics did
give somewhat different pictures -- which is itself a useful
finding.

---

## 3. Assumptions

1. **2021-2022 is a fair "prior" window.** This was the peak of
   corporate ESG language in our data (Part 2 finding) and predates
   the most acute pressure on DEI disclosure. We average two years
   to smooth single-year noise.

2. **2024 is a fair "post-retreat" measurement point.** It is the
   most recent year we have, and it is the first full proxy cycle
   after both the June 2023 SCOTUS ruling and the broader 2023
   anti-DEI political wave.

3. **Composite z-score retreat is a meaningful summary of three
   different metrics.** This is a methodological convenience; the
   three individual metrics are also reported and tell different
   stories, which we discuss in FINDINGS.md.

4. **AR(1) autocorrelation is a reasonable summary of within-company
   persistence.** With 9 observations per company, more sophisticated
   time-series models would be over-fit. AR(1) is the simplest
   defensible thing.

5. **The Authenticity Index from Part 3 is the right input.** We
   inherit all of Part 3's methodological choices (3 themes for S, 4
   indicators for A, per-year percentile rank, 15-point alignment
   tolerance). If those choices are wrong, this analysis is wrong
   downstream.

---

## 4. What I would do differently with more time

1. **Replicate with the full S&P 500.** Our n = 50 is small for
   correlation analysis. The trait-vs-state variance decomposition,
   in particular, is likely under-estimating the trait share at n =
   50. A 500-company replication would probably show the trait share
   above 30%.

2. **Match against external behavioral data.** ISS controversy
   scores, EEO-1 demographic filings, OSHA citations, DOJ/EPA
   enforcement actions. Until then, this is text-on-text alignment,
   not text-on-behavior alignment. The "DEI retreat" we measure is a
   text retreat; whether actual workforce diversity programs were
   wound down is a separate question.

3. **Test other potential outcomes.** Climate-language retreat,
   executive-comp ESG linkage changes, board diversity table
   changes. The relationship between prior authenticity and
   subsequent retreat might exist for some outcomes and not others.

4. **Model the trajectory shape, not just the level.** Some
   companies' authenticity oscillates around a stable mean; others
   show a clean trend; others have a single jump in a specific year.
   Categorizing trajectory SHAPES might surface patterns that
   level-based analyses miss.

5. **Cross-validate the 2021-2022 -> 2024 finding with placebo
   windows.** Does 2017-2018 predict 2020? Does 2019-2020 predict
   2022? Running the same analysis on multiple windows would tell
   us whether the (null) result we found is reliable or window-
   specific.

---

## 5. Known limitations

1. **Small sample.** n = 46 companies for the prediction test (50
   minus 4 that lacked 2021 or 2024 proxies). With 3 predictor
   categories, the per-group n is 14-16. Statistical power is
   modest.

2. **Three retreat metrics disagree.** This is honestly reported
   but does limit how much weight to put on any one number. The
   composite is what we use for headline reporting, but the
   underlying metrics give different stories.

3. **The trait-vs-state finding may be partly an artifact.** Per-year
   percentile ranking (in Part 3) means a company with stable raw
   scores can still cross category boundaries if other companies
   move. Some of the 52% year-to-year category-change rate is
   percentile-rank churn, not focal-company change.

4. **No external benchmark.** Neither the predictive test nor the
   stability test has external validation. We are measuring an
   internal property of our own dataset.

5. **The SCOTUS ruling is one event, not a clean treatment.** The
   2023 ruling did not affect all sectors equally. We did not
   stratify the analysis by sector exposure to affirmative-action
   litigation risk. A more careful study would.

---

## Repository layout

```
part4/
+-- README.md                this file
+-- FINDINGS.md              full analytical writeup (the main deliverable)
+-- SUMMARY.md               1-page non-technical summary
+-- run.py                   entry point (`python run.py`)
+-- requirements.txt
+-- src/
|   +-- compute.py           analysis code
+-- data/                    bundled inputs
|   +-- part1_dataset_no_text.csv
|   +-- part2_dataset_no_text.csv
|   +-- authenticity_index.csv   (Part 3 output)
+-- outputs/
    +-- retreat_analysis.csv     per-company prior status + retreat metrics
    +-- trait_vs_state.json      variance decomposition and stability results
    +-- part4_findings.png       two-panel figure
```

To re-run:

```bash
pip install -r requirements.txt
python run.py
```

The pipeline is fully self-contained.
