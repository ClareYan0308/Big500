# Part 1 -- Stated Values: Scraping "About Us" Pages via the Wayback Machine
## Written Summary

---

### What We Did

We built a four-stage data pipeline that collected and analysed the "About Us"
pages of 50 large public companies -- the 10 biggest by market capitalisation
in each of five S&P 500 sectors (Technology, Financials, Healthcare, Consumer
Discretionary, and Energy) -- across nine years from 2016 to 2024.

For each company-year we queried the Wayback Machine's CDX API, selected the
snapshot closest to July 1, extracted clean body text from the archived HTML
using a two-stage pipeline (trafilatura with a BeautifulSoup fallback), and
analysed each page with Claude Sonnet 4 for thematic content, year-over-year
change, and linguistic register.

**Final coverage**: 431/450 snapshots scraped successfully (95.8%); 410
records yielded enough clean text for analysis; 400 received full LLM
analysis (the remaining 10 fell back to keyword heuristics due to API
errors on a small handful of long pages).

---

### Key Findings

**1. The shareholder-to-stakeholder transition is visible in the text.**

Shareholder-value language fell from 27% of pages in 2016 to just 11% in 2024
-- a 15-point drop. The decline appears in every sector, but it is sharpest in
Financials (25% -> 10%) and Healthcare (20% -> 0%). Over the same period,
employee-culture language rose from 37% to 55%, mission-purpose language rose
from 27% to 45%, and ethics-integrity language rose from 15% to 25%. These
movements are consistent with the rhetorical shift announced by the Business
Roundtable's August 2019 "Statement on the Purpose of a Corporation."

**2. ESG language became near-universal -- then began retreating in Financials.**

Sustainability/ESG language rose from 27% of pages in 2016 to a peak of 51% in
2022. The largest single-sector gains were in Healthcare (30% -> 71%) and Energy
(43% -> 67%). Notably, Financials moved opposite the trend in 2024: ESG language
fell from 50% in 2022-2023 back down to 20%. This reversal -- visible in our
data before it became widely reported -- is consistent with banks softening DEI
and climate commitments under post-2023 political and regulatory pressure.

**3. Healthcare anchors its identity in mission-purpose; Technology, in innovation.**

Across all analysed years, mission-purpose was the dominant theme on 49 of 86
Healthcare records, by far the highest concentration of any sector -- a finding
driven heavily by Johnson & Johnson's Credo, Pfizer's "Purpose," and Eli Lilly's
explicit mission framing. Technology pages, by contrast, were dominated by
innovation-technology language (34 of 76 records), with mission-purpose a
distant second. The two sectors are also the only ones where mission-purpose
language never fell below 30% in any year.

**4. Energy companies pivoted twice: into ESG by 2022, then back toward
   "energy security" by 2024.**

Energy is the only sector that maintained substantial shareholder-value
language throughout (22% in 2024, the highest of any sector). It also shows
the cleanest example of two distinct rhetorical pivots: ESG language jumped
from 33% in 2018 to 67% in 2022, accelerated by net-zero commitments from
ExxonMobil, Chevron, and ConocoPhillips. Post-Ukraine-war (2022 onward),
global-scale and energy-security framing returned while ESG language stayed
elevated, producing pages that simultaneously emphasise both reliability and
sustainability.

**5. Pages change substantially every year -- but the change is mostly
   incremental.**

86% of year-over-year comparisons were flagged as "changed" by the LLM, and
average character-trigram similarity between consecutive years was 0.42 -- well
below the 0.85 threshold for "substantially identical." But most of this is
incremental editing rather than wholesale rewrites: only a small minority of
records (notably AMZN 2022, JNJ 2020, XOM 2022) show similarity below 0.10,
indicating a true rewrite. Companies with the most dramatic year-over-year
changes are typically those with new CEOs (Wells Fargo under Scharf,
ExxonMobil's Low Carbon Solutions launch) or major strategic pivots (Amazon's
"Earth's Best Employer" addition, Microsoft's AI repositioning).

**6. Linguistic register splits roughly 35% Aspirational / 35% Formal /
    16% Conversational / 14% Technical.**

Aspirational register dominates Consumer Discretionary and Healthcare; Formal
register dominates Financials and Energy; Technical register is
disproportionately present in Technology pages discussing AI capabilities.
This sectoral split mirrors the underlying communication strategies: regulated
industries (finance, energy) write to investors and regulators; consumer-facing
firms write to aspirational consumers.

---

### Limitations and Caveats

**Coverage gaps (19 records, 4.2%).** Nineteen company-year combinations could
not be recovered even after three rounds of URL discovery -- typically very
early years (2016-2018) for companies that hadn't yet established a stable
About page URL (Phillips 66, Booking Holdings) or very recent years for
companies that rebranded their corporate sites (UnitedHealth Group 2023-2024).
All gaps are documented row-by-row with the CDX query URL that was tried, so
future researchers can verify.

**Text quality varies.** Some "About" pages are 50 words of marketing copy;
others are 6,000-word strategy documents. The LLM's theme detection is more
reliable on the longer pages. Records with fewer than 30 words were excluded
from analysis.

**Text is aspirational, not behavioural.** What companies write on their
About pages is corporate communication, not policy. The disappearance of
shareholder-value language does not establish that companies actually
deprioritised shareholders -- only that they chose not to lead with that
framing.

---

### How the Analysis Could Be Extended

The most informative next step would be to pair this corporate self-description
data with outcome measures -- ESG ratings, employee-satisfaction surveys, SEC
enforcement actions, or stock-return patterns -- to test whether language shifts
predict, lag, or are independent of behavioural change. The 30-column dataset
is structured to support exactly that kind of join: every row has a ticker,
sector, year, and Wayback timestamp suitable for matching against financial
and regulatory data.
