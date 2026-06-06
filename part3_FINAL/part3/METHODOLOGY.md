# Part 3 -- Authenticity Index: Construct Reasoning and Methodology

The brief asks us to design a measure of *organizational authenticity*:
the degree of alignment between what a company says it values and what
its disclosures suggest it actually prioritizes. The brief also says
explicitly that the reasoning is being graded as much as the measure
itself.

This document explains every methodological choice. Section 1 defines
the construct. Section 2 chooses the data inputs. Sections 3 and 4
specify the formulas. Section 5 explains the percentile-rank
transformation. Section 6 is the validity check. Section 7 lists
limitations and threats to validity.

---

## 1. What we mean by "authenticity"

We adopt a narrow, operational definition.

> **Organizational authenticity** = the degree to which a company's
> public statements about what it values are matched by the substance
> of its formal disclosures on those same values.

Three things follow from this definition.

**First, we are not measuring behavior.** A genuinely authentic company
in a deep philosophical sense would have its public statements, its
formal disclosures, AND its actual conduct all aligned. We can only
observe two of those three. We are measuring *disclosure-disclosure
alignment*, not *disclosure-behavior alignment*. We return to this in
Section 7.

**Second, alignment is bidirectional.** A company that claims big and
delivers small is misaligned (greenwashing risk). But a company that
claims nothing and delivers a lot is ALSO misaligned -- just in the
opposite direction. We treat both as departures from authenticity, on
the theory that an honest organization tells the public roughly what it
tells the SEC. We separately track the *direction* of misalignment so
the two cases can be examined independently.

**Third, this is an ESG-focused index, not a general one.** Our two
datasets give us strong signal on ESG and stakeholder content, weak
signal on other dimensions. A more general "authenticity index" would
need other inputs (product quality vs. marketing, financial guidance
vs. actual results, etc.). We restrict our claim accordingly.

---

## 2. Choosing the data inputs

The two sides of the alignment construct map naturally onto our two
existing datasets.

| Construct side | Dataset | Rationale |
|---|---|---|
| What the company SAYS it values | Part 1 -- About-page text | About pages are marketing aimed at the general public. They have no SEC liability; companies write what they want to be associated with. |
| What its disclosures suggest it actually PRIORITIZES | Part 2 -- DEF 14A proxy statements | Proxies are SEC-filed governance documents. They carry legal liability for misstatements. Their ESG content reflects what the company can afford to assert under audit. |

This pairing is the entire conceptual basis of the index. Marketing
copy and legal disclosure are written by different teams, for different
audiences, under different incentives. When they tell the same story
about ESG, that is evidence of organizational coherence. When they
diverge, that divergence is itself a meaningful signal.

---

## 3. Operationalizing the STATED side (S)

We need a number for each (company, year) that captures *how much the
company positions itself as ESG-oriented on its About page*.

Part 1's binary `theme_*` columns are the obvious raw material. The
question is which ones to include.

We restrict to three Part 1 themes that map directly onto ESG content:

| Part 1 theme | Why included |
|---|---|
| `theme_esg_sustainability` | Direct mention of ESG / sustainability / climate / DEI as part of the company's identity |
| `theme_stakeholder_capitalism` | Explicit stakeholder-orientation framing (employees, customers, communities AND shareholders), the rhetorical foundation of ESG |
| `theme_community_impact` | Community / social-responsibility framing, the "S" of ESG translated into corporate language |

We deliberately exclude themes that overlap with ESG but are not the
same construct:

- `theme_employee_culture`: many companies discuss culture without any
  ESG framing. Including it would conflate "good employer" with "ESG
  company."
- `theme_ethics_integrity`: highly correlated with formal compliance
  language; would bias the index toward companies in regulated
  industries.
- `theme_mission_purpose`: too general -- nearly every Healthcare
  company hits this regardless of ESG orientation.

**Formula:**

    S = (theme_esg_sustainability + theme_stakeholder_capitalism + theme_community_impact) / 3

S takes one of four discrete values: {0, 1/3, 2/3, 1}. A company at S=0
makes no ESG identity claims; a company at S=1 hits all three ESG-
identity themes simultaneously.

**Limitation we accept here.** Four discrete values is coarse. We could
have used the full 10-theme set with weighting. We chose the cleaner
3-theme set because (a) it is defensible and theory-driven, (b) more
themes would introduce ambiguity about weights, and (c) the percentile-
rank transformation in Section 5 effectively re-distributes the
discrete values across the rank space.

---

## 4. Operationalizing the ACTUAL side (A)

Now the harder side: what does substantive ESG disclosure in a proxy
statement actually look like?

Part 2 gives us many candidate signals. We could pick one and call it
done -- e.g., `esg_keyword_density` is intuitive. But any single signal
captures only one dimension of substance and is exploitable as a
metric (a company can boost density by repeating keywords).

We instead use FOUR components, each capturing a different facet:

| Component | What it captures | Why this dimension matters |
|---|---|---|
| `A_density` | **Volume** of ESG language (normalized) | A proxy that mentions ESG terms 30 times per 1000 words is doing more work than one that mentions them 3 times |
| `A_explicit` | **Structural** disclosure choice (binary) | Creating a dedicated ESG section is a stronger commitment than scattering ESG language across other sections |
| `A_dei_qual` | **Interpretive substance** of DEI disclosure (LOW/MED/HIGH) | "We value diversity" is LOW. "33% women, 28% URM directors, with named programs" is HIGH. This dimension cannot be measured by counting |
| `A_targets` | **Specificity** of commitments (binary) | A proxy with quantitative ESG targets (% reduction by 20XX) makes auditable commitments; one without does not |

The four components measure different things and are not perfectly
correlated. Combining them gives a more robust substance score than
any one alone.

**Formula:**

    A_density   = min(esg_keyword_density, 30) / 30
    A_explicit  = has_explicit_esg_section  (0 or 1)
    A_dei_qual  = LOW -> 0, MEDIUM -> 0.5, HIGH -> 1
    A_targets   = has_quantitative_targets  (0 or 1)
    A = (A_density + A_explicit + A_dei_qual + A_targets) / 4

A is continuous in [0, 1]. The four components are equally weighted
because we have no defensible basis for a particular weighting.

**Why we cap density at 30.** Without a cap, a few very ESG-heavy
proxies (mostly Financials in 2022) would pin A_density to 1.0 for
those rows and inflate their A_actual scores. The 30 cap is roughly
the 99th percentile in the Part 2 data; above that, marginal mentions
add little real signal.

---

## 5. Why per-year percentile rank, not raw S minus A

S and A are on very different scales:

- S has four discrete values in {0, 1/3, 2/3, 1}
- A is continuous and right-skewed (most companies cluster below 0.5)

Comparing raw S to raw A would systematically penalize companies in
years when average disclosure is lower (early years 2016-2018) and
flatter advantages in companies whose actual disclosure happens to be
above the discrete-value boundaries of S.

To remove both the scale and the year effects, we convert each side
to its **within-year percentile rank** before computing the gap.

**Why per-year rather than across the whole dataset:** ESG disclosure
language has been rising over the whole 9-year window. A company at
A=0.4 in 2016 was probably above average; a company at A=0.4 in 2024
is probably below average. Percentile rank within year corrects for
this drift. The index measures relative alignment WITHIN each year,
not absolute alignment across years.

**Cost of this choice:** the index cannot detect a company that
sincerely caught up with the field over time. If everyone moves
together, percentile ranks stay constant. We accept this as a feature,
not a bug: we are measuring alignment *given the prevailing norms*,
not absolute commitment.

---

## 6. Computing the Authenticity Index

For each (company, year):

    S_pct      = percentile rank of S among that year's records, 0-100
    A_pct      = percentile rank of A among that year's records, 0-100
    gap        = A_pct - S_pct                      [signed]
    AI         = 100 - |gap|                        [the index, range 0-100]
    category   = STEALTH      if  gap >  +15
                 ALIGNED      if  |gap| <= 15
                 GREENWASH    if  gap <  -15

The 15-percentile-point tolerance is a substantive choice: we treat
companies whose stated and actual percentile ranks differ by 15 points
or less as effectively aligned. A 15-point gap in a 50-company sample
is roughly 7-8 ranks of difference, which we consider noise. A
20-point gap is real signal.

**Why a signed gap as well as an absolute index:** the signed gap
lets us distinguish two qualitatively different forms of misalignment:

- `gap > +15`: actual substance > stated identity. The company
  discloses more than it markets. We call this STEALTH (under-claim).
- `gap < -15`: stated identity > actual substance. The company
  markets more than it discloses. We call this GREENWASH-RISK
  (over-claim).

Both are scored as low authenticity by the index, but they are
substantively different stories.

---

## 7. Validity check: do the results match intuition?

Before trusting the index, we predict where five specific companies
SHOULD fall and check whether they do.

| Company | Pre-registered prediction | Result | Match? |
|---|---|---|---|
| TSLA | Famous "save the planet" mission but minimal SEC ESG disclosure -> GREENWASH-RISK | gap = -32, GREENWASH-RISK | YES |
| BRK-B | Buffett famously avoids ESG marketing; expect STEALTH if proxy has substance | gap = +47, STEALTH | YES |
| CVX | Oil major; expect dense proxy ESG (regulatory requirement) but quiet About page | gap = +32, STEALTH | YES |
| NVDA | Pure-play chip company, no ESG positioning; expect ALIGNED at LOW end | gap = -14, ALIGNED (low) | YES |
| MSFT | Famously vocal on ESG publicly; expect over-claim relative to proxy substance | gap = -26, GREENWASH-RISK | YES |

All five predictions matched.

**Distributional properties of the index:**

| Statistic | Value |
|---|---|
| N (company-years) | 393 |
| Mean | 69.2 |
| Median | 73.1 |
| Standard deviation | 22.0 |
| Range | 3.3 to 100.0 |
| 25th / 75th percentile | 53.4 / 87.8 |

| Category | Count | Share |
|---|---|---|
| ALIGNED | 125 | 32% |
| STEALTH (under-claim) | 127 | 32% |
| GREENWASH-RISK (over-claim) | 141 | 36% |

The three categories are roughly balanced, which is what we would
expect by construction (per-year percentile-ranks mean any year's
median company has an authenticity score of 50 by definition, but
because the index is bounded above at 100 and below at 0, the mean
sits near 70).

**Direction by sector (mean signed gap):**

| Sector | Mean gap | Direction |
|---|---|---|
| Energy | +6.3 | leans STEALTH (oil majors disclose more than they market) |
| Healthcare | +2.1 | leans STEALTH |
| Financials | +0.1 | balanced |
| Consumer Discretionary | -2.7 | leans GREENWASH-RISK |
| Technology | -6.1 | leans GREENWASH-RISK |

Both sector-level patterns are sensible: oil majors face SEC pressure
to disclose climate and have detailed proxy ESG sections, but they do
not lead with ESG on their consumer-facing About pages. Tech and
Consumer Discretionary companies put ESG on their About pages
prominently but have less of it in their proxies.

---

## 8. Limitations and threats to validity

The brief asks for at least two. We list six in order of severity.

**T1 -- Both sides measure language, not behavior.** This is the most
fundamental limitation. We compare what a company writes on its About
page to what it writes in its proxy. We do not measure actual
emissions, actual workforce diversity, actual community spending. A
company can be "authentic" in our sense while being entirely
unsuccessful at translating either disclosure into action. The index
measures disclosure coherence, which is a necessary but not sufficient
condition for behavioral authenticity.

**T2 -- The theme mapping between S and A is interpretive.** Part 1's
themes (mission, customer, innovation, etc.) and Part 2's themes
(climate risk, board diversity, etc.) come from different taxonomies.
We mapped three Part 1 themes to "ESG identity" and four Part 2
indicators to "ESG substance," but reasonable analysts could choose
different mappings. We have documented our choice but cannot prove
it is the best mapping.

**T3 -- The two documents serve different audiences.** About pages are
written for customers, journalists, and the public. Proxies are
written for shareholders, ISS/Glass Lewis, and the SEC. A company
that talks differently to different audiences is doing what every
organization does. Calling that "inauthentic" is a value judgment our
construct embeds but does not prove.

**T4 -- Per-year percentile ranking removes absolute information.** A
company that has steadily increased both its stated and actual ESG
language since 2016 will not be flagged as having improved its
authenticity, because we compute everything relative to peers in the
same year. Researchers interested in absolute change should use the
raw S and A columns we provide, not the percentile-ranked authenticity
index.

**T5 -- Sample bias toward sophisticated communicators.** Our 50
companies are the largest in their sectors. They have professional
investor-relations and corporate-communications staff. Smaller
companies, lacking that polish, might have About pages that more
naively reflect actual priority. This index would over-state alignment
for sophisticated communicators (because their statements are crafted
to match their disclosures) and under-state it for naive ones.

**T6 -- The index treats over-claim and under-claim symmetrically.**
A company that says nothing and discloses substantial ESG (STEALTH)
gets the same authenticity score as one that says everything and
discloses little (GREENWASH-RISK). Many readers will find the latter
much more problematic than the former. The signed `gap` column allows
analysts to weight these differently; the headline `authenticity`
column does not.

---

## What this index is good for

Reasonable uses include:

- **Spotting outliers**: companies whose A is dramatically higher or
  lower than their S in a given year warrant individual investigation.
- **Tracking change over time** within a company: did Wells Fargo's
  authenticity score improve after its 2016 scandal?
- **Cross-sector contrasts**: the systematic difference between
  Tech (over-claim) and Energy (under-claim) is itself an interesting
  finding.

What this index is NOT good for:

- Ranking companies for ESG quality. A LOW-LOW alignment (NVDA, ORLY)
  scores the same as a HIGH-HIGH alignment (HD, WFC), but they are
  entirely different from an ESG performance standpoint.
- Predicting future ESG misconduct. We have no behavioral validation,
  only cross-disclosure coherence.
- Replacing third-party ESG ratings. This is a disclosure-coherence
  measure, not an ESG-quality measure.
