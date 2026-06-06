# Part 3 -- The Authenticity Index: Saying vs. Disclosing
## Written Summary

---

### What We Built

We took the two datasets we already had -- 50 large U.S. companies'
About pages (Part 1, marketing) and proxy statements (Part 2, SEC
filings) -- and built a single number that measures, for each company
in each year, whether what they SAY they value matches what they
formally DISCLOSE about ESG.

The intuition: About pages are written by marketing teams for the
general public, with no SEC liability. Proxies are written by lawyers
for shareholders, with full SEC liability. The same company writing in
both places can tell two different stories. When the stories match, we
call that ALIGNED. When marketing is louder than disclosure, we call
that GREENWASH-RISK. When disclosure is louder than marketing, we call
that STEALTH ESG.

The Authenticity Index runs from 0 to 100, with 100 being perfect
alignment. We computed it for 393 of the 450 possible company-years
(the rest were missing in one dataset or the other).

---

### What the Validity Check Showed

Before trusting the index, we predicted where five specific companies
SHOULD fall and checked the results:

| Company | We predicted | The index says | Match? |
|---|---|---|---|
| Tesla | High marketing claims, sparse SEC disclosure -- GREENWASH | Score 58, gap -32 -- GREENWASH | YES |
| Berkshire Hathaway | Avoids ESG marketing, but proxy has substance -- STEALTH | Score 44, gap +47 -- STEALTH | YES |
| Chevron | Regulated to disclose, but quiet on consumer-facing pages -- STEALTH | Score 58, gap +32 -- STEALTH | YES |
| NVIDIA | Pure-play chip company, no ESG positioning -- ALIGNED at low end | Score 83, gap -14 -- ALIGNED | YES |
| Microsoft | Famously vocal on ESG publicly -- expect over-claim | Score 73, gap -26 -- GREENWASH | YES |

All five predictions matched.

---

### The Three Findings That Surprised Us

**1. Half of the 50 companies are misaligned by 15 percentile points
   or more in their typical year.**

Only 32% of company-years sit inside the +/- 15-point alignment band.
Roughly equal shares fall on either side: 36% are over-claimers
(GREENWASH-RISK) and 32% are under-claimers (STEALTH). Misalignment is
not a rare edge case; it is the modal outcome.

**2. Tech and Consumer Discretionary lean toward over-claim;
   Energy and Healthcare lean toward under-claim.**

The directional bias by sector is consistent and substantial:

| Sector | Average gap | Reads as |
|---|---|---|
| Technology | -6.1 | More marketing than disclosure |
| Consumer Discretionary | -2.7 | More marketing than disclosure |
| Financials | +0.1 | Balanced |
| Healthcare | +2.1 | Slight under-claim |
| Energy | +6.3 | More disclosure than marketing |

This makes business sense. Tech and consumer brands compete for
purpose-driven customers and need positive ESG framing on their
About pages. Oil majors and pharma face heavy SEC and regulatory
scrutiny and are forced to disclose substantively, but they have
little incentive to lead with sustainability claims on consumer-facing
pages.

**3. The biggest GREENWASH-RISK names include some surprises.**

The companies whose marketing language most exceeds their proxy
substance, in our index, are: Merck (gap -45), Tesla (-32), BlackRock
(-32), Microsoft (-26), Morgan Stanley (-25), Nike (-23), Bank of
America (-21). Some of these are intuitive (Tesla's "save the planet"
positioning is far ahead of its proxy disclosures). Some are less
obvious. BlackRock, despite Larry Fink's high-profile ESG letters,
shows more marketing ESG than legal-filing substance over the 9-year
window. Microsoft's public ESG commitments outpace its proxy
disclosures even though the company has substantial actual ESG
programs -- suggesting the proxy may underdiscloses what Microsoft is
actually doing.

---

### What This Index Is Good For -- and What It Is Not

**Good uses:**

- **Spotting outliers**: a company more than 30 percentile points off
  the diagonal in any year is worth investigating individually.
- **Tracking change over time within a company**: did a specific
  scandal, regulatory action, or new executive shift the company's
  alignment?
- **Cross-sector strategic insight**: the systematic Tech-vs-Energy
  difference is itself an interesting business finding for anyone
  trying to compare disclosure regimes across industries.

**Important things it cannot do:**

- **It cannot rank companies for ESG quality.** A company that says
  nothing AND discloses nothing (low-low) scores the same as one that
  says a lot AND discloses a lot (high-high). They are alignment-
  equivalent but ESG-incomparable.
- **It cannot measure authenticity in any deep sense.** We compare
  two text artifacts, not actual organizational behavior. A company
  could be perfectly aligned in its disclosures while failing entirely
  to act on either.
- **It cannot predict misconduct or future scandals.** We have no
  behavioral validation -- only cross-disclosure coherence.

---

### A Note on What "Authenticity" Means in This Project

We use "authenticity" narrowly and operationally. The construct is
*disclosure-disclosure alignment*: do the marketing department and
the legal department tell the same story about ESG? A company that
passes this test could still be acting badly. A company that fails it
could simply have a more cautious legal team than marketing team.

The index is one piece of evidence in a larger picture, not a verdict.
