# Part 4 -- A Proposal: Does the Authenticity Index Predict Behavior?

This document is the analytical writeup. The brief asks for "intellectual
curiosity and scientific reasoning," and explicitly says "a well-argued
exploratory finding is worth more than a superficial confirmatory one."
We took that seriously and report a result we did not expect, then
interrogate it.

---

## 1. The question (and why we found it interesting)

Part 3 produced an Authenticity Index that categorizes each
(company, year) as ALIGNED, GREENWASH-RISK (over-claim), or STEALTH
(under-claim). Part 2 showed that diversity-related language in proxy
statements retreated substantially between 2021 and 2024, with the
clearest single break point being the June 2023 SCOTUS affirmative-
action ruling.

These two findings invite an obvious question: **were the retreaters
the loud claimers?**

There are two plausible directions, and neither is obviously right:

- **HC, "cheap talk"**: GREENWASH-RISK companies (whose stated ESG
  exceeded their disclosure substance in 2021-2022) retreated MORE.
  Their public claims were never anchored to disclosed substance, so
  walking them back cost little.
- **HS, "sticky commitment"**: GREENWASH-RISK companies retreated
  LESS. Loud public commitments are expensive to retract; quieter
  STEALTH companies could drop content without anyone noticing.

This is interesting because it tests whether the Authenticity Index
has **predictive validity** -- whether the categorization in 2021-2022
tells you anything about what the company will do in 2023-2024. Part 3
showed only cross-sectional validity (the categorization matched what
we would intuitively expect about specific companies in their own year).
Predictive validity is a stronger test.

---

## 2. Method

**Predictor**: each company's average signed authenticity gap during
2021-2022 (negative = greenwash, positive = stealth). We use a
two-year average rather than 2022 alone to smooth single-year noise --
a choice that turns out to matter for the second part of this analysis.

**Outcomes**: three operationalizations of "DEI retreat" between 2021
and 2024:

1. `delta_diversity_mentions` -- raw 2024 minus 2021 count of diversity
   keywords in the proxy. Most direct but subject to floor effects
   (companies near zero in 2021 cannot retreat much).
2. `delta_workforce_dei` -- 2024 minus 2021 binary presence of the
   workforce-DEI theme. Robust to floor effects.
3. `delta_dei_quality` -- 2024 minus 2021 LLM grade of DEI disclosure
   quality (LOW=0, MEDIUM=1, HIGH=2). Captures qualitative substance.
4. `retreat_composite` -- z-score average of the above three.

We use multiple metrics rather than one because each measures a
different facet of "retreat" and they could give different answers.

**Tests**: Pearson and Spearman correlation between prior gap and each
retreat measure; group-mean comparison by prior category; t-tests
between groups.

---

## 3. Result: the prediction is weak and inconsistent

| Outcome | Pearson r | p-value | Interpretation |
|---|---|---|---|
| delta_diversity_mentions | +0.03 | 0.86 | No relationship |
| delta_workforce_dei | -0.21 | 0.16 | Marginal (sticky-commitment direction) |
| delta_dei_quality | -0.25 | 0.09 | Marginal (sticky-commitment direction) |
| retreat_composite | -0.21 | 0.16 | Marginal (sticky-commitment direction) |

| Prior category | n | diversity delta | workforce_dei delta | dei_quality delta | retreat composite |
|---|---|---|---|---|---|
| GREENWASH-RISK | 16 | -5.7 | -0.06 | -0.06 | +0.20 |
| ALIGNED | 16 | +5.2 | -0.44 | -0.31 | +0.01 |
| STEALTH | 14 | -3.6 | -0.43 | -0.64 | -0.23 |

Three observations:

1. **No metric shows a strong relationship.** The strongest is a
   marginal r = -0.25 (p = 0.09), in the direction of "stickier
   commitments" -- not cheap talk.
2. **The metrics disagree.** Raw diversity-mention counts show
   GREENWASH retreating most (-5.7 vs -3.6); the composite says STEALTH
   retreated most. The qualitative grade (`delta_dei_quality`) is the
   most extreme: STEALTH companies' DEI disclosure quality dropped by
   -0.64, vs only -0.06 for GREENWASH-RISK.
3. **Neither hypothesis wins cleanly.** Cheap talk (HC) predicts a
   positive correlation; sticky commitment (HS) predicts a negative one.
   We see weakly negative correlations -- closer to HS than HC, but
   not strong enough to support either decisively.

The honest report is: **prior alignment status does not robustly
predict subsequent DEI retreat in these data.**

This is itself a meaningful finding. We did NOT successfully validate
the Authenticity Index as a predictor. So what's going on?

---

## 4. The second question we did not plan to ask

A weak predictive correlation has two possible explanations:

- **(a)** Prior alignment really doesn't drive subsequent behavior --
  the theoretical relationship is just absent.
- **(b)** Prior alignment DOES drive behavior, but our measurement of
  "prior alignment" is too noisy to detect the relationship.

Distinguishing (a) from (b) requires knowing how stable the
Authenticity Index actually is within a company over time. If
alignment status flips year-to-year, then any single (or two-year)
window is a noisy proxy for the company's true alignment posture,
and weak predictive correlations are no surprise.

So we measured stability three ways:

**1. AR(1) autocorrelation within companies.** Year-to-year
authenticity scores correlate at r = 0.21 (p < 0.001, n = 344). That
is statistically significant but substantively weak -- only 4% of the
variance in year T+1's authenticity is explained by year T.

**2. Variance decomposition.** Between-company variance in
authenticity is 98.4; within-company variance is 435.0. The
between-company share is just **18%** -- meaning 82% of the variance
in authenticity is companies changing over time, not differences
between companies.

**3. Category transitions.** In any pair of consecutive years for a
given company, the alignment category (ALIGNED / GREENWASH /
STEALTH) **changes 52% of the time**. The direction of any
misalignment (over-claim vs under-claim) flips in 42% of consecutive
years.

These three numbers tell the same story:

> Authenticity is mostly a STATE, not a TRAIT. Companies move in and
> out of alignment categories nearly every year. Only about a fifth
> of the index's variation is a stable characteristic of the company;
> the rest is year-to-year movement.

---

## 5. What this means for the Authenticity Index

The trait-vs-state finding reinterprets the Part 4 main result and
re-frames how the index should be used.

**Implication 1: predicting future behavior from any single year of
authenticity is inherently limited.** With AR(1) = 0.21, a company at
the 90th percentile of greenwash-risk this year has only modest
expected greenwash-risk next year. The category labels are a snapshot
of an organization's current posture, not a stable trait we can use
to forecast its future actions.

**Implication 2: the right unit of analysis is multi-year averages,
not single years.** Part 3's company-level summary table (using
9-year averages) is much more stable than any single year. Our
specific cases (TSLA = greenwash, BRK-B = stealth, CVX = stealth,
NVDA = aligned, MSFT = greenwash) were correctly identified using
multi-year averages -- and they remain stable when we look at the
DOMINANT category across years. But you cannot do this with a single
year.

**Implication 3: the index is best understood as describing a
relationship, not predicting outcomes.** A company that scores as
GREENWASH-RISK this year is telling us something true about the
current disclosure-coherence of its marketing vs. its proxy. It is
NOT telling us how that company is likely to behave in 2 years.

**Implication 4: research questions that need cross-year predictions
need different aggregations.** Future work might use rolling 3-year
windows of authenticity, or model the trajectory shape itself
(rising / falling / oscillating) rather than the level.

---

## 6. Surprises and honest caveats

**The most interesting incidental finding:**
STEALTH companies (low stated, high actual) showed the largest drop
in qualitative DEI disclosure (-0.64 on the LLM-graded scale, vs
-0.06 for GREENWASH-RISK). One possible reading: the companies that
quietly built substantive DEI infrastructure had the most disclosure
substance available to retract. Companies that loudly claimed DEI
without backing it up never had the substance to retreat from -- they
just changed what was on their About page (which we do not measure
here). This would mean the legal disclosures responded to
post-2023 pressure even when public-facing marketing did not.

That is speculation; n = 14 STEALTH companies is small, the result
is barely significant (p = 0.09), and the alternative explanation
(floor effects -- GREENWASH companies had less substance to lose) is
equally plausible. We flag it as worth re-examining in a larger sample.

**Caveats on the trait-vs-state finding:**

1. The variance decomposition treats year-to-year movement as
   "noise." Some of it isn't noise -- it is real company response to
   real events (e.g., the BLM-driven 2021 DEI surge). What looks
   like instability in the company may be stability of the company
   in a changing environment.
2. The per-year percentile rank in Part 3 is what makes movement
   between categories possible. A company with stable raw S and A
   scores can still flip categories if other companies move around
   them. Some of the 52% category-change rate is attributable to
   percentile-rank churn, not to the focal company changing.
3. n = 50 is small. With more companies, between-company variance
   would likely grow as a share of total. Our 18% trait-share is
   probably an under-estimate.

---

## 7. What we would do next

1. **Replicate with a larger sample** (the full S&P 500) to get a
   sharper trait-vs-state ratio. We expect the trait share to grow.
2. **Look at OTHER outcomes besides DEI retreat**: climate language
   pull-back, executive compensation linkage changes, board diversity
   table changes. Predictive validity may exist for some outcomes and
   not others.
3. **Match against external behavioral data** -- ISS controversy
   scores, OSHA citations, EEO-1 filings, regulatory enforcement
   actions. Until then, we are measuring text-on-text alignment.
4. **Test whether AVERAGE multi-year authenticity predicts behavior**
   better than single-year authenticity. Our hypothesis would be yes
   -- multi-year averages should partially solve the trait-vs-state
   noise problem.

---

## 8. The point of this analysis

We started with what looked like a clean hypothesis test: does
prior greenwash status predict DEI retreat? We expected to find a
clean answer in one direction or another. What we found was a weak,
inconsistent relationship -- and then, in investigating WHY, we
discovered something more interesting and more uncomfortable: the
measure we built in Part 3 is more volatile within companies than
we realized.

That is the kind of finding we would not have gotten by running a
confirmatory analysis. It re-frames how the Part 3 index should be
used and what claims it can support. Not what we set out to find,
but more useful than what we set out to find.
