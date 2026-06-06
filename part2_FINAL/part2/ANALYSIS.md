# Part 2 -- Text Mining Analysis and Methodology

This document is the analytical companion to `part2_dataset.csv`. It
addresses three required analytical dimensions:

1. **Within-company changes** in language, tone, and topic emphasis over time
2. **Cross-company and cross-sector variation** in ESG disclosure
3. **Shifts that coincide with external events**

Before presenting findings, Section 1 explains and justifies every
methodological choice -- which classical NLP techniques we used, which
LLM tasks we delegated to the model, and why we use them in combination
rather than one or the other.

---

## 1. Methodology: what we did and why

### 1.1 Why a hybrid classical + LLM approach (and not either alone)

We use TWO independent analytical pipelines on every proxy and record
their outputs as separate columns in the dataset.

**Pipeline A -- classical NLP** (columns `climate_mention_count`,
`diversity_mention_count`, `governance_mention_count`,
`esg_keyword_density`, `net_zero_target_year`, `pct_women_board`,
`has_quantitative_targets`):

- Three keyword lists (~20 terms each) covering climate, diversity,
  and governance vocabulary
- Regex extraction of specific quantitative commitments (net-zero
  target years, percentages of women on board)
- Character-trigram Jaccard similarity for measuring text change

**Pipeline B -- LLM analysis** (columns `esg_themes`,
`climate_commitment`, `dei_disclosure_quality`, `changed_from_prior`,
`change_summary`, `register`, `analyst_notes`):

- Each proxy's ESG section is sent to Claude Sonnet 4 along with the
  prior year's text
- The model returns a JSON object with theme classifications, change
  judgments, quality grades, and free-text observations

We use BOTH because each fails where the other succeeds:

| Question | Classical NLP | LLM | Best signal |
|---|---|---|---|
| "How many times does 'climate' appear?" | Reliable, reproducible | Non-deterministic | Classical |
| "Does this proxy mention net-zero by a specific year?" | Reliable (regex) | Could miss creative phrasings | Classical |
| "Is this DEI disclosure substantive or boilerplate?" | Cannot tell | Trained on human judgment | LLM |
| "What changed since last year?" | Can compute similarity | Can name what changed | LLM (with classical sanity check) |
| "Is climate framed as risk or opportunity?" | Cannot distinguish | Can read the distinction | LLM |
| "Are there quantitative ESG targets?" | Yes (regex for %, "by 20XX") | Yes (interpretive) | Both -- cross-validate |

When the two pipelines disagree, that disagreement IS analytically
interesting. For example, in 23 records the LLM marked
`theme_emissions_targets=1` but the regex found no `net_zero_target_year`
-- these are cases where the company committed to "emissions reductions"
or "Scope 1 reductions" without naming a specific net-zero year. The
two-signal architecture surfaces these nuances; a single-method
approach would miss them.

### 1.2 Why these specific keywords

The keyword lists in `proxy_parser.py` were not generated from training
data; they were assembled by reading a representative sample of 20
proxies from 2018, 2021, and 2024 (one early, one mid, one recent) and
listing every distinct climate-, diversity-, and governance-related
term that appeared. The lists deliberately cover both:

- **Lexical core** (climate, carbon, emissions, diversity, inclusion,
  governance)
- **Technical / regulatory vocabulary** (TCFD, Scope 1/2/3, SBTi, DEI,
  pay equity, ESG-linked compensation)

We deliberately do NOT include very general words ("environment,"
"social") because they generate too many false positives (e.g., "social
media") without adding signal. Each keyword was checked against at
least 5 sampled proxies to confirm it appears in context.

### 1.3 Why these 12 themes (and not more or fewer)

The theme taxonomy in `analyzer.py` emerged from three sources:

1. **SEC disclosure rules**: human capital (Nov 2020 rule), climate
   (March 2022 proposal, March 2024 final rule), and board diversity
   (Nasdaq 2021 rule) each map to a theme
2. **Major frameworks**: TCFD, SASB, and SBTi each map to a theme or
   sub-theme
3. **Sample reading**: the same 20-proxy sample used to build keywords
   was reviewed for recurrent content categories not covered by the
   above

We chose 12 themes rather than a larger taxonomy (e.g., the 26
SASB categories) because at higher granularity the LLM's coding became
inconsistent (Cohen's-kappa style reliability dropped in pilot
testing). Twelve themes give enough resolution to track sectoral
patterns without making every record sparse across many columns.

### 1.4 Why Claude Sonnet 4 (and what we asked it to do)

We use `claude-sonnet-4-20250514` for three tasks:

- **Multi-label theme classification** (which of 12 themes are present)
- **Year-over-year change detection** (given current and prior text,
  did the disclosure meaningfully change?)
- **Quality grading** (LOW / MEDIUM / HIGH for DEI disclosure)
- **Verbatim extraction** (specific climate commitment quotes)
- **Free-text observation** (analyst notes)

Why this model rather than a smaller/cheaper one (e.g., Haiku) or a
larger one (e.g., Opus): we ran the same 30 records through Haiku,
Sonnet, and Opus during pilot testing. Haiku produced inconsistent
JSON output (~15% malformed) and missed subtle distinctions like
"net-zero in operations" vs "net-zero across financing activities"
(the latter being much more meaningful for a bank). Opus produced
output very similar to Sonnet 4 at roughly 5x the per-record cost.
Sonnet 4 was the cost/quality sweet spot.

Why we send the **ESG section only**, not the full proxy: full proxies
average 50,000-100,000 words; sending all of them would cost ~$50-100
in API fees and dilute the model's attention with executive-comp tables
and audit reports. We extract the ESG sub-section (capped at 8000
characters) so the LLM focuses on the analytically relevant content.

Why we provide the **prior year's text** in the same prompt: change
detection is the core analytical task, and the LLM does it far better
when shown both years simultaneously than when asked to remember and
compare across separate calls.

### 1.5 What we are NOT doing (and why)

- **Topic modeling (LDA, BERTopic)**: would have produced bottom-up
  topics, but with N=450 documents and no labeled training set, the
  topics would have been hard to interpret without doing exactly the
  same heading-based section detection we already use. We chose a
  theory-driven (predefined themes) approach because the analytical
  question is "do these specific dimensions of disclosure change?"
  not "what topics emerge?"
- **Sentiment scoring (VADER, FinBERT)**: would have produced a
  positive/negative score per proxy, but DEF 14A language is so
  uniformly formal that sentiment scores cluster tightly around
  neutral. We instead use the LLM's `register` classification
  (FORMAL / ASPIRATIONAL / TECHNICAL / COMPLIANCE) which is
  domain-appropriate.
- **TF-IDF**: we considered using TF-IDF to identify each company's
  most distinctive terms, but with proxies that share 95%+ of their
  vocabulary (corporate-governance boilerplate), TF-IDF surfaced mainly
  proper nouns (company names, executive names, director names) rather
  than analytically interesting language.

---

## 2. Within-company changes over time

### 2.1 Aggregate: how much do proxies change year-over-year?

Character-trigram Jaccard similarity between consecutive years' ESG
sections averages **0.42 across the dataset** (1.0 = identical text;
0.0 = entirely different). This number tells us that companies retain
roughly 42% of their ESG section vocabulary year over year and rewrite
or replace the rest.

Crucially, similarity dipped sharply in 2020 (0.33) -- meaning proxies
filed in 2020 retained less of their 2019 language than usual. This
is the COVID year, when companies were adding human-capital language
under SEC pressure (see Section 4.1) and also reacting to the early
2020 BLM protests in their workforce disclosures.

It also rose in 2023-2024 (0.49-0.50), meaning proxies in those years
retained MORE of the prior year's language. After the rapid editing
of 2020-2022, companies appear to have settled on stable ESG language
and changed less of it -- consistent with the broader thesis that the
ESG architecture has solidified even as the broader rhetoric softens.

### 2.2 Which companies change the most?

The five companies with the LOWEST average year-over-year similarity
(i.e., the most-rewritten proxies) are:

| Ticker | Avg ngram sim | Note |
|---|---|---|
| PSX | 0.13 | Phillips 66, very different proxy structure across years |
| OXY | 0.19 | Occidental, post-Anadarko acquisition rewrites |
| SBUX | 0.22 | Starbucks, large CEO-driven narrative shifts |
| NVDA | 0.24 | NVIDIA, accommodating rapidly growing ESG section as company size grew |
| MPC | 0.25 | Marathon Petroleum |

These five are companies where reading the proxy in 2017 vs 2024 tells
a substantially different story. The Energy sector is over-represented
here, consistent with the broader finding that Energy companies are
the most volatile in their ESG framing.

The five companies with the HIGHEST average similarity (the
most-templated proxies) are:

| Ticker | Avg ngram sim | Note |
|---|---|---|
| EOG | 0.68 | EOG Resources, very stable formal disclosure pattern |
| NKE | 0.68 | Nike, mature templated ESG sections |
| UNH | 0.67 | UnitedHealth Group |
| MSFT | 0.62 | Microsoft, refines language but stable structure |
| ADBE | 0.60 | Adobe |

These are companies where the ESG language is highly formulaic --
edited but not rewritten year-over-year.

### 2.3 Within-company case studies

**Microsoft (MSFT) -- the slow rise of DEI followed by the 2024 fade**

| Year | Climate mentions | Diversity mentions | DEI quality | Register |
|---|---|---|---|---|
| 2016 | 0 | 2 | LOW | FORMAL |
| 2018 | 7 | 7 | MEDIUM | ASPIRATIONAL |
| 2021 | 3 | 7 | MEDIUM | ASPIRATIONAL |
| 2024 | 0 | 2 | LOW | FORMAL |

Microsoft's proxy ESG language rose substantially through 2021 and
collapsed by 2024 back to 2016 levels. The 2018 ASPIRATIONAL register
(under Satya Nadella's "growth mindset" framing) faded to formal
compliance language by 2024.

**ExxonMobil (XOM) -- the climate-language rollercoaster**

| Year | Climate mentions | Diversity mentions | Register |
|---|---|---|---|
| 2016 | 2 | 0 | COMPLIANCE |
| 2020 | 16 | 0 | FORMAL |
| 2023 | 17 | 0 | TECHNICAL |
| 2024 | 5 | 0 | TECHNICAL |

ExxonMobil's climate mentions surged 8-fold from 2016 to 2020 (during
the Engine No. 1 proxy fight that won three Exxon board seats) and
peaked again in 2023, then fell sharply in 2024. Yet diversity
mentions stayed flat at zero throughout -- Exxon never engaged in
DEI language. The register shifted from COMPLIANCE to TECHNICAL --
moving toward engineering-style language about emissions math rather
than narrative climate framing.

**Wells Fargo (WFC) -- the post-scandal recovery and post-2022 retreat**

| Year | Climate mentions | Diversity mentions | DEI quality | Register |
|---|---|---|---|---|
| 2016 | 0 | 8 | MEDIUM | COMPLIANCE |
| 2020 | 6 | 6 | MEDIUM | COMPLIANCE |
| 2021 | 8 | 11 | MEDIUM | FORMAL |
| 2024 | 0 | 4 | LOW | COMPLIANCE |

Wells Fargo's 2021 proxy was its high water mark in both climate and
diversity disclosure -- coming the year after its $3 billion fake-accounts
settlement, in clear "we are reformed" framing. By 2024, both signals
have substantially retreated, with DEI quality dropping from MEDIUM
back to LOW for the first time since 2016.

---

## 3. Cross-company and cross-sector variation

### 3.1 The five themes where sectors diverge by 30+ percentage points in 2024

The 2024 proxies show striking sectoral divergence on five themes:

| Theme | High sector | Low sector | Spread |
|---|---|---|---|
| CLIMATE_OPPORTUNITY | Energy (40%) | Consumer Discretionary (0%) | 40pp |
| WORKFORCE_DEI | Healthcare (50%) | Energy (10%) | 40pp |
| HUMAN_CAPITAL | Financials (60%) | Technology (20%) | 40pp |
| STAKEHOLDER_ENGAGEMENT | Healthcare (70%) | Energy (40%) | 30pp |
| POLITICAL_LOBBYING | Healthcare (30%) | Consumer Discretionary (0%) | 30pp |

A few of these are counterintuitive and worth interpretation:

- **CLIMATE_OPPORTUNITY** is HIGH in Energy: oil majors are reframing
  climate as a business opportunity (low-carbon products, CCS) rather
  than just a risk. Consumer Discretionary, by contrast, treats climate
  as essentially absent from the proxy (zero opportunity language).
- **HUMAN_CAPITAL** is HIGH in Financials, LOW in Technology: this
  inverts the popular narrative. Banks discuss workforce management
  extensively in proxies (talent retention, succession), while Tech
  companies say less about human capital despite their public
  "people-first" branding. The proxy is for SEC-required disclosure,
  not for marketing.
- **WORKFORCE_DEI** is HIGH in Healthcare, LOW in Energy: Healthcare
  retains DEI language even into 2024 (50% of records), while Energy
  has effectively abandoned it (10%).

### 3.2 The DEI retreat by sector (2021 -> 2024)

Diversity-keyword mentions per proxy peaked in 2021 and have since
declined in three sectors and risen in one:

| Sector | 2021 avg | 2024 avg | Delta |
|---|---|---|---|
| Consumer Discretionary | 29.7 | 2.1 | -27.6 (-93%) |
| Energy | 12.9 | 0.3 | -12.6 (-98%) |
| Financials | 4.7 | 1.9 | -2.8 (-60%) |
| Healthcare | 3.2 | 3.7 | +0.5 (+16%) |
| Technology | 5.1 | 17.7 | +12.6 (+247%) |

Three observations:

1. **Consumer Discretionary's collapse is the dataset's most extreme
   single-sector retreat.** The decline is not just statistical: it
   tracks the wave of high-profile rollbacks at Tractor Supply,
   Harley-Davidson, Lowe's (in our sample), and others.
2. **Healthcare barely budged.** Healthcare companies, which depend on
   a diverse patient base and a regulated workforce, have neither
   accelerated nor retreated.
3. **Technology BUCKED the trend.** Tech is the only sector where
   diversity mentions per proxy ROSE substantially from the 2021 peak
   through 2024. This is consistent with continued EEOC and state-level
   scrutiny of Tech-sector hiring, but it is the opposite of what
   superficial media coverage of "the DEI retreat" would suggest.

### 3.3 The proxy is "stickier" than marketing on ESG

Comparing Part 1 (About pages) and Part 2 (proxy statements) for the
same companies and years lets us measure how much faster marketing
language moves than legal disclosure language.

Financial-sector ESG language fell from 50% of records (peak) to 20%
(2024) on About pages (Part 1) -- a 60% decline. The same companies'
proxy-statement ESG keyword density fell from 27.4 to 17.6 over the
same window -- a 36% decline. **Legal-disclosure language is roughly
40% stickier than marketing language**, consistent with the fact
that proxies carry SEC liability for misstatements while About pages
do not.

---

## 4. External events: what coincides with what

For each external event, we predict an expected language signature
BEFORE looking at the data, then check whether it appears.

### 4.1 SEC Human Capital disclosure rule (effective November 9, 2020)

**Prediction**: human-capital language should surge in 2021 proxies
(the first full filing cycle after the rule took effect) and stay
elevated thereafter.

**Evidence**:

| Year | `theme_human_capital` % |
|---|---|
| 2019 | 40% |
| 2020 | 40% |
| 2021 | 57% |
| 2022 | 53% |

**Match**: clear +17 percentage-point jump from 2020 to 2021, with
elevated levels sustained. This is the cleanest cause-and-effect in
the dataset because the rule is precisely dated, applies to all
companies, and addresses one specific disclosure area.

### 4.2 George Floyd murder and BLM protests (May/June 2020)

**Prediction**: DEI / diversity language should surge in 2021 proxies
(the first cycle after the summer 2020 events) and may retreat later.

**Evidence**:

| Year | `theme_workforce_dei` % |
|---|---|
| 2019 | 26% |
| 2020 | 32% |
| 2021 | 53% |
| 2022 | 43% |

**Match**: +21 percentage-point jump from 2020 to 2021 -- the largest
single-year theme shift in the entire dataset. Subsequent retreat is
discussed in 4.5 below.

### 4.3 SEC climate disclosure proposal (March 21, 2022)

**Prediction**: climate language should rise in 2022 proxies and 2023
proxies (anticipating the rule), then potentially soften as the rule
faced legal challenges.

**Evidence**:

| Year | Avg climate mentions | `theme_climate_risk` % |
|---|---|---|
| 2020 | 3.3 | 12% |
| 2021 | 7.2 | 20% |
| 2022 | 8.1 | 18% |
| 2023 | 5.7 | 14% |
| 2024 | 2.7 | 14% |

**Match**: climate mentions roughly tripled from 2020 to 2021/2022,
then declined to below 2020 levels by 2024. The decline coincides
with the legal challenges and political pushback that ultimately
weakened the SEC's final climate rule (March 2024).

### 4.4 SCOTUS *Students for Fair Admissions* ruling (June 29, 2023)

**Prediction**: DEI language and explicit demographic-disclosure
language should retreat in 2024 proxies (the first cycle after the
ruling), particularly in sectors most exposed to disparate-impact
litigation.

**Evidence**:

| Year | `theme_workforce_dei` % | Avg diversity mentions |
|---|---|---|
| 2021 | 53% | 11.1 |
| 2022 | 43% | 7.1 |
| 2023 | 36% | 6.1 |
| 2024 | 25% | 5.2 |

**Match**: workforce-DEI theme prevalence dropped from 53% (2021) to
25% (2024) -- a 28 percentage-point decline, more than half. The
LLM-assigned "HIGH" DEI disclosure-quality grade dropped from 5
companies in 2021 to 1 in 2023 and 2024. The retreat began before the
2023 SCOTUS ruling (gradual decline 2021->2023) but accelerated
sharply in 2024 (-11pp single-year drop).

### 4.5 Anti-ESG state legislation (Texas SB 13, 2021; Florida HB 3, 2023)

**Prediction**: Financial-sector ESG language should retreat after
2022, since this legislation specifically targets banks and asset
managers that "discriminate" against fossil-fuel and firearms
companies.

**Evidence (Financials sector only)**:

| Year | ESG keyword density | `theme_climate_risk` % | `theme_workforce_dei` % |
|---|---|---|---|
| 2021 | 17.0 | 20% | 50% |
| 2022 | 27.4 | 30% | 40% |
| 2023 | 21.4 | 20% | 40% |
| 2024 | 17.6 | 20% | 30% |

**Partial match**: ESG density in Financials peaked in 2022 and has
declined steadily since, with workforce-DEI declining most. Climate-
risk theme actually held steady at 20% (banks have specific
TCFD-aligned disclosures they must maintain regardless). The decline
is real but not total -- consistent with our broader finding that
structural ESG disclosures are stickier than rhetorical ESG language.

### 4.6 Net-zero commitments did NOT retreat

A useful counter-example: when one expects language to retreat but it
does not.

**Prediction**: net-zero commitments might have been quietly withdrawn
during the 2023-2024 ESG retreat.

**Evidence**: 88 records mention a specific net-zero target year.
By filing year:

| Year | Records with net-zero year |
|---|---|
| 2020 | 3 |
| 2021 | 15 |
| 2022 | 24 |
| 2023 | 21 |
| 2024 | 23 |

**No retreat**: the count is essentially unchanged from 2022 to 2024.
Companies stopped TALKING about climate as much but kept the specific
commitments on the books. This is consistent with our broader thesis:
narrative ESG retreats; structural ESG (committees, target years,
oversight) persists.

---

## 5. What the two pipelines together let us claim

The hybrid classical + LLM architecture lets us make claims of three
strength levels:

1. **Strong claims** (both pipelines agree): the DEI retreat, the
   climate-language peak in 2022, the HCM surge in 2021. For these,
   both objective counts AND LLM judgment move in the same direction.

2. **Moderate claims** (LLM-supported, classical mute): the
   architectural stability of board ESG oversight, the
   COMPLIANCE-vs-ASPIRATIONAL register split. Classical methods cannot
   detect these distinctions; LLM judgment is the primary evidence.

3. **Suggestive claims** (one signal, not the other): if classical
   keyword counts move but the LLM doesn't see thematic change, we
   may be capturing template editing rather than substantive change.
   If the LLM sees change but counts don't move, we may be capturing
   rhetorical reframing of the same vocabulary. Both are interesting
   but neither is conclusive on its own.

The dataset records all three layers so any downstream user can
calibrate confidence appropriately.
