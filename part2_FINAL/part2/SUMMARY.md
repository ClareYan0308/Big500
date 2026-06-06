# Part 2 -- Lived Values: ESG Disclosure in DEF 14A Proxy Statements
## Written Summary

---

### What We Did

We collected the SEC-filed annual proxy statement (DEF 14A) for each of
the same 50 large U.S. companies analyzed in Part 1, for every year from
2016 to 2024. We downloaded the documents directly from SEC EDGAR,
isolated the ESG / sustainability / human capital section using regex
heading detection, and combined two analytical methods: classical NLP
(keyword counts, regex-based extraction of net-zero years and board-
diversity percentages) and LLM analysis (Claude Sonnet 4) for theme
classification, change detection, and disclosure-quality grading.

**Final coverage**: 442 / 450 filings retrieved (98.2%); 442 with proxy
text; 396 (90% of those with text) contained an explicit ESG-related
section; 441 records received full LLM analysis.

---

### Key Findings

**1. The ESG retreat is visible in legally-filed disclosures, not just
   marketing language.**

ESG keyword density (climate + diversity + governance mentions per
1000 words) follows an inverted-U pattern: 6.3 in 2016, rising to a
peak of 14.8 in 2022, then declining to 11.6 in 2024. This is the
same arc Part 1 found in About-page marketing copy -- but it is
sharper and harder to deny when measured in SEC filings, where
companies have a legal duty of accuracy. The 2022 peak coincides with
the SEC's proposed climate disclosure rule and TCFD adoption push;
the 2024 decline coincides with the rise of state-level anti-ESG
legislation (Texas SB 13, Florida HB 3) and broader political pressure.

**2. The DEI retreat is concentrated in two sectors, and one sector
   bucked it.**

Diversity-language mentions per filing fell sharply from 2021 to 2024
in Consumer Discretionary (-27.6 mentions per record) and Energy
(-12.6), declined modestly in Financials (-2.8), barely moved in
Healthcare (+0.5), and rose substantially in Technology (+12.6).
Technology was the only sector where diversity language increased
from the 2021 peak through 2024. This split tracks the legal exposure
landscape: Consumer-facing brands and oil majors had the most public
DEI commitments to roll back; Tech, under continued regulatory
scrutiny over workforce composition, did the opposite. The SCOTUS
affirmative-action ruling of June 2023 appears to mark a clear pivot
point: by the 2024 proxies, 17 fewer companies received a "HIGH" DEI
quality grade than in 2021.

**3. Energy companies' climate language rose four-fold by 2022, then
   collapsed back to 2016 levels by 2024.**

Energy proxies averaged 6.4 climate mentions per filing in 2016. That
rose to 22 by 2021 and peaked at 25.8 in 2022. Then it dropped to
13.3 in 2023 and 2.7 in 2024 -- effectively back to the pre-2020
baseline. Yet net-zero commitments did NOT disappear: 7 of the 10
Energy companies still carry a net-zero target year on the books in
their 2024 proxies. The shift is not that Energy abandoned its
commitments; it is that Energy stopped TALKING about them. The
language pulled back faster than the underlying policies did.

**4. Net-zero commitments are now mainstream, and most settle on 2050.**

Across the corpus, 30 of 50 companies (60%) have at some point
disclosed a specific net-zero or carbon-neutral target year in a
proxy. Of those, the modal target year is 2050 (17 companies),
followed by 2040 (2), 2035 (2), and 2030 (2). Financials lead by
sector with 10 of 10 having made such a commitment at some point;
Energy follows with 7 of 10. Healthcare is the laggard with only 3 of 10.

**5. Board-level ESG oversight has become the standard floor of disclosure.**

Across every sector except Technology, more than 80% of 2024 proxies
explicitly disclose board-level ESG oversight structures (an ESG
committee, sustainability committee, or named board oversight
responsibility). Even Technology, the laggard, rose from 22% in 2016
to 80% in 2024. This is the one form of ESG disclosure that did NOT
retreat after 2022. Once a board ESG committee exists, it is awkward
to abolish it; the structure stays even when the language softens.

**6. The "human capital" disclosure rule of November 2020 produced a
   measurable surge.**

The proportion of proxies discussing human capital management rose
from 16% in 2016 to 57% in 2021, the first full year after the SEC's
human capital disclosure rule took effect. This is the cleanest
example in the dataset of a specific regulatory action producing a
specific language shift across all sectors simultaneously.

---

### Comparison with Part 1

Part 1 found that on companies' own "About" pages, ESG language rose
from 27% (2016) to 51% (2022), then fell -- with Financials retreating
furthest, back to 20% by 2024. Part 2 finds the same arc in SEC
filings, but two important differences:

1. **The retreat is smaller in proxies.** Financials proxies dropped
   from 27.4 to 17.6 in ESG keyword density (2022 to 2024) -- a 36%
   reduction. About-page language dropped roughly 60% in the same
   sector and window. Legal disclosures are stickier than marketing.

2. **Structural disclosures stay even when narrative language fades.**
   Board ESG oversight, named committees, and specific net-zero target
   years remain in 2024 proxies even as the surrounding narrative
   language thins. The architecture of ESG disclosure has outlasted
   the rhetoric.

---

### Limitations

- 8 filings could not be retrieved (mostly newer companies' early-year
  filings) and are documented row-by-row in the dataset.
- 46 of 442 retrieved proxies (10%) have no explicit ESG section that
  our regex could find; these tend to be older (2016-2017) and from
  Technology companies, where ESG content was sometimes scattered
  across the document rather than dedicated to a single section.
- Keyword counts do not distinguish substantive disclosure from
  passing mention. We use the LLM's `dei_disclosure_quality` grade and
  the regex-extracted quantitative targets as complementary signals.
- The 2024 data point is the most recent year; some of the 2024
  patterns (especially the DEI retreat) may extend or reverse in 2025
  filings not yet available.
