# Part 4 -- A Surprising Result About Our Own Index
## Written Summary

---

### The Question We Asked

After Part 3, we had a measure that flagged some companies as
**GREENWASH-RISK** (loud marketing about ESG, thin formal disclosure)
and others as **STEALTH** (quiet marketing, substantial formal
disclosure). Part 2 had separately shown that diversity-related
language in proxy statements retreated dramatically between 2021 and
2024, with the June 2023 SCOTUS affirmative-action ruling as the
clearest break point.

These two findings invited an obvious question: were the retreaters
the companies that had previously over-claimed?

We thought we knew which way this would go. We were wrong about that.

---

### What We Found

**The simple prediction did not hold.** Companies that were
GREENWASH-RISK in 2021-2022 did NOT systematically retreat MORE on
DEI between 2021 and 2024. Across three different ways of measuring
"retreat," the relationship was weak and inconsistent (correlations
between -0.21 and +0.03, all in the range of "marginally significant
to nothing").

That on its own was a useful finding. It means the Authenticity Index
from Part 3 is descriptive, not predictive. Knowing a company
greenwashed in 2022 tells you almost nothing about whether it walked
back DEI in 2024.

But there was a more interesting finding hiding underneath.

---

### Why the Prediction Failed: Authenticity Is Not a Stable Trait

We expected companies' authenticity scores to be roughly stable over
time -- to be a property of the organization rather than a property
of any given year. So we measured the within-company stability of
the Authenticity Index three ways.

| Stability check | Result | What it means |
|---|---|---|
| Year-to-year correlation within companies | r = 0.21 | Very weak |
| Share of variance that is between-company (trait) | 18% | Most of the variation is WITHIN companies, not between them |
| Year-over-year category change rate (ALIGNED / GREENWASH / STEALTH) | 52% | Companies move between categories nearly every year |
| Direction (over- vs under-claim) flip rate | 42% | Companies flip from over-claim to under-claim or vice versa about 4 years in 10 |

Authenticity is more of a state than a trait. The same company can be
GREENWASH-RISK in 2021, ALIGNED in 2022, STEALTH in 2023, and back to
GREENWASH-RISK in 2024.

This explains why the prediction failed. Predicting 2024 retreat from
a 2021-2022 status is like predicting next year's weather from last
year's weather: there is some signal, but mostly there is noise.

---

### What This Means for Reading the Authenticity Index

If you take only one thing from this analysis:

> The Authenticity Index works as a snapshot, not as a forecast.

This has three concrete implications:

1. **The right unit of analysis is multi-year averages.** Part 3's
   per-company averages over 9 years are much more stable than any
   single year, and the validity-check companies (Tesla, Berkshire,
   Chevron, NVIDIA, Microsoft) were correctly identified using those
   multi-year averages. Single-year scores are too noisy to trust.

2. **Predicting future behavior from past alignment is not what this
   measure is for.** If you want a forecast of whether a company will
   walk back ESG, you need something more behavioral than a
   text-on-text alignment score.

3. **The category labels are a current diagnosis, not a permanent
   verdict.** A company that scores GREENWASH-RISK this year is being
   accurately described as misaligned this year. It is not being
   accused of being a greenwasher in any deeper sense.

---

### The Honest Caveat

We started thinking we would find one clean answer to one clean
question. We found something messier and more useful: the Part 3
index is moving more within companies than between them. That changes
what we can say with it.

The brief asks for "exploratory" rather than "confirmatory" findings.
This is exploratory: we found a result that should change how the
Part 3 index is used, but we found it by testing a hypothesis that
turned out to be wrong. That is the point of running the test.
