# Part 2 -- Dataset Schema

This document is the column-by-column reference for `outputs/part2_dataset.csv`.
For each column we record:

- **Type**: the data type (str / int / float / bool / list)
- **Source**: where the value comes from (SEC EDGAR API / HTML parse / regex / LLM)
- **What it contains**: the literal contents
- **Why included**: the analytical purpose this column serves

The dataset has **45 columns** organized into 6 groups. Each row represents
one (company, filing year) pair. The full dataset is 450 rows (50 companies
x 9 years, 2016-2024).

Design principle: we capture three things in parallel for every record --
the raw text, classical-NLP signals computed from that text, and LLM
interpretive judgement. The three layers are kept separate so any
downstream user can decide which to trust for which question.

---

## Group 1: Identifiers (4 columns)

These four columns uniquely identify each row and provide the keys for
joining with external data (financial returns, ESG ratings, regulatory
actions).

### `ticker`
- **Type**: str (e.g., "AAPL")
- **Source**: hand-coded in `companies.py`
- **What it contains**: the company's stock ticker symbol
- **Why included**: This is the standard primary key for any join with
  financial market data. Using ticker (not company name) allows joining
  to CRSP, Compustat, FactSet, or any market-data product.

### `company_name`
- **Type**: str (e.g., "Apple Inc.")
- **Source**: hand-coded in `companies.py`
- **What it contains**: the company's legal name
- **Why included**: Human readability when inspecting rows. Avoids the
  cognitive load of looking up ticker abbreviations during analysis.

### `sector`
- **Type**: str (one of five GICS sectors)
- **Source**: hand-coded in `companies.py`
- **What it contains**: the company's GICS sector classification as of
  January 2024 (Technology, Financials, Healthcare, Consumer
  Discretionary, or Energy)
- **Why included**: Sector-level aggregation is one of the project's
  central analytical lenses. Many of our findings only make sense as
  sector contrasts (e.g., Energy companies' climate-language collapse,
  Tech bucking the DEI retreat).

### `year`
- **Type**: int (2016 through 2024)
- **Source**: derived from `filing_date`
- **What it contains**: the calendar year in which the proxy was filed
  with the SEC
- **Why included**: The primary time dimension. We use filing year (not
  fiscal year) because the proxy reflects the company's CURRENT
  disclosure posture as of when it was filed, even if the financials
  it covers are from the prior fiscal year.

---

## Group 2: Filing metadata (6 columns)

These columns document the provenance of each row -- which SEC filing it
came from, when it was filed, and where it can be re-verified.

### `cik`
- **Type**: str (e.g., "320193")
- **Source**: hand-coded in `companies.py`
- **What it contains**: the SEC's Central Index Key, the permanent
  identifier the SEC uses for the filing entity
- **Why included**: The CIK is more stable than the ticker (it survives
  name changes, ticker symbol changes, and class-share splits). It is
  the join key for any direct SEC dataset and for our `fetch_manifest.json`.

### `accession_number`
- **Type**: str (e.g., "0000320193-24-000001")
- **Source**: SEC EDGAR submissions API
- **What it contains**: the SEC's unique ID for this specific filing
- **Why included**: An accession number plus a CIK uniquely identifies
  a filing across all of EDGAR. Including it lets any reviewer go back
  to the original SEC document and verify what we read.

### `filing_date`
- **Type**: str (ISO date, e.g., "2024-04-15")
- **Source**: SEC EDGAR submissions API
- **What it contains**: the date the filing was submitted to the SEC
- **Why included**: Different from `year` (which is just the year part).
  The full date lets us test event-driven hypotheses -- e.g., do
  proxies filed within 90 days after the June 2023 SCOTUS affirmative-
  action decision differ from earlier 2023 filings?

### `filing_url`
- **Type**: str (full HTTPS URL)
- **Source**: constructed from CIK + accession + primary document name
- **What it contains**: a direct link to the SEC EDGAR document
- **Why included**: Anyone reviewing the dataset can click through to
  the original PDF/HTML. This is essential for verifiability and for
  resolving disputes about what the document actually says.

### `scrape_status`
- **Type**: str (one of: "OK", "MISSING", "FAILED", "HTTP_XXX")
- **Source**: the fetcher's success/failure tracking
- **What it contains**: whether the filing was successfully downloaded
- **Why included**: Enables clean filtering during analysis. Missing
  rows are kept (not dropped) so that the dataset has 450 rows
  unconditionally, and `scrape_status != "OK"` is the filter you apply
  for analytical work. Documenting failures is itself a deliverable.

### `missing_reason`
- **Type**: str (e.g., "no_def14a_in_year", "HTTP_403", "download_failed")
- **Source**: the fetcher's error logging
- **What it contains**: when `scrape_status != "OK"`, a short reason code
- **Why included**: Different reasons have different analytical
  implications. A company that simply did not file a DEF 14A that year
  is genuinely missing; a download that failed once for network reasons
  could be re-tried. The reason code preserves that distinction.

---

## Group 3: Document content (6 columns)

These columns capture the cleaned text and basic measurements of size.
The raw text columns enable any future re-analysis (different keyword
lists, different LLM prompts).

### `doc_size_bytes`
- **Type**: int
- **Source**: file size of the downloaded HTML
- **What it contains**: size in bytes of the raw filing HTML
- **Why included**: A rough proxy for filing complexity / page count.
  Useful as a sanity-check (zero bytes means the download failed
  silently) and as a covariate when interpreting keyword counts
  (a doc that grew from 200KB to 2MB will mechanically have more
  mentions of everything).

### `total_word_count`
- **Type**: int
- **Source**: word count of `proxy_text_clean` after HTML cleaning
- **What it contains**: total words in the cleaned proxy text
- **Why included**: The denominator for normalized keyword frequencies.
  Companies file proxies of vastly different lengths (15,000 to 150,000
  words). To compare two proxies fairly we must normalize counts to
  mentions per 1000 words, and this column is that denominator.

### `esg_section_word_count`
- **Type**: int
- **Source**: word count of `esg_section_text` if found, else 0
- **What it contains**: words in the extracted ESG sub-section
- **Why included**: The growth of this number from 2016 to 2024 IS one
  of the key findings -- ESG sections went from typically zero to
  typically thousands of words. Tracking the section's size over time
  is itself a research finding.

### `has_explicit_esg_section`
- **Type**: bool
- **Source**: whether `find_esg_section()` returned a non-empty result
- **What it contains**: True if our regex found a dedicated ESG /
  sustainability / human-capital / DEI section in the proxy
- **Why included**: This boolean is the single cleanest indicator in
  the dataset of whether a company chose to give ESG a labeled,
  dedicated section. Its transition from FALSE to TRUE across the
  2016-2024 window is itself a disclosure event worth analyzing.

### `proxy_text_clean`
- **Type**: str (potentially very long; can be 100K+ characters)
- **Source**: HTML cleaning of the raw filing
- **What it contains**: the full visible text of the proxy, cleaned of
  HTML markup, scripts, and table-layout artifacts
- **Why included**: This is the raw material for any future re-analysis.
  We anticipate that other researchers may want to apply different
  keyword lists, different sentiment scoring, or different LLM prompts.
  Storing the cleaned text in-row keeps the dataset self-contained.

### `esg_section_text`
- **Type**: str (capped at ~8000 characters)
- **Source**: the ESG sub-section extracted by `find_esg_section()`
- **What it contains**: just the ESG / sustainability section, or null
  if `has_explicit_esg_section` is False
- **Why included**: This is the exact text that was sent to the LLM
  for analysis. Reproducibility requires that anyone can see what the
  LLM saw and judge its analytical output accordingly.

---

## Group 4: Classical NLP signals (7 columns)

These columns are computed from `esg_section_text` (or `proxy_text_clean`
when no ESG section is found) using objective, reproducible rules --
keyword counts and regex pattern extraction. They are kept separate from
the LLM analysis so users can trust them for any question where
reproducibility is paramount.

### `climate_mention_count`
- **Type**: int
- **Source**: case-insensitive count of keywords from `CLIMATE_KEYWORDS`
  list in `proxy_parser.py`
- **What it contains**: total number of climate-related keyword
  occurrences (climate, carbon, emissions, net-zero, TCFD, Scope 1/2/3,
  etc.)
- **Why included**: An objective, reproducible measure of climate
  emphasis that complements the LLM's theme judgement. If the LLM says
  "this proxy is climate-focused" but this number is 1, we have a
  conflict worth investigating; if both signals agree, our confidence
  is higher.

### `diversity_mention_count`
- **Type**: int
- **Source**: case-insensitive count of keywords from `DIVERSITY_KEYWORDS`
- **What it contains**: total occurrences of diversity / inclusion /
  equity / DEI / pay-equity / underrepresented-minority terms
- **Why included**: Same logic as climate. We need a measure of DEI
  emphasis that is not subject to LLM non-determinism. The dramatic
  2021-to-2024 collapse in this number for Consumer Discretionary and
  Energy is one of the clearest signals in the entire dataset.

### `governance_mention_count`
- **Type**: int
- **Source**: case-insensitive count of `GOVERNANCE_KEYWORDS`
- **What it contains**: occurrences of ESG-oversight-specific
  governance terms (ESG committee, sustainability committee,
  human-capital management, etc.)
- **Why included**: Captures the STRUCTURAL dimension of ESG (committees,
  oversight, named board responsibilities) separately from the
  RHETORICAL dimension (climate language, DEI language). One of our
  key findings is that the structural dimension stayed stable even as
  rhetoric retreated.

### `esg_keyword_density`
- **Type**: float (mentions per 1000 words)
- **Source**: 1000 * (climate + diversity + governance mentions) /
  (esg_section_word_count or total_word_count)
- **What it contains**: a normalized measure of overall ESG emphasis
- **Why included**: Raw counts confound emphasis with document length.
  A long proxy has more of every keyword by default. The density
  normalizes for length, making cross-company and cross-year comparisons
  meaningful. This is the column we use for the headline "inverted-U"
  finding (6.3 -> 14.8 -> 11.6).

### `net_zero_target_year`
- **Type**: int or null (e.g., 2050)
- **Source**: regex extraction from `proxy_text_clean`
- **What it contains**: the first year mentioned in a net-zero or
  carbon-neutral target commitment, or null if none found
- **Why included**: A topic MENTION ("we care about climate") is much
  weaker evidence of commitment than a specific target year ("net zero
  by 2050"). This column captures the strong-commitment signal. The
  distribution of target years (most companies cluster at 2050) is itself
  a finding.

### `pct_women_board`
- **Type**: int (10-80) or null
- **Source**: regex extraction looking for patterns like "X% of
  directors are women" or "X% women"
- **What it contains**: an extracted percentage of female board members
- **Why included**: Board diversity is a tangible, quantifiable
  disclosure that we can compare across companies and years. We
  constrain extraction to plausible values (10-80%) to avoid false
  positives from unrelated percentages in the document.

### `has_quantitative_targets`
- **Type**: bool
- **Source**: at least 3 matches of `\d+%` or `by 20XX` patterns within
  the ESG section
- **What it contains**: whether the ESG section contains specific
  quantitative ESG targets
- **Why included**: Quantitative commitments are auditable in a way
  vague language is not. A company that says "we are committed to
  reducing emissions" has said almost nothing; a company that says
  "reduce Scope 1+2 emissions 50% by 2030" has made an auditable
  promise. This flag separates the two.

---

## Group 5: LLM analysis (10 columns)

These columns come from sending the ESG section to Claude Sonnet 4 with
a structured prompt. They capture interpretive judgements that classical
NLP cannot make: was the disclosure substantive or vague? Did the
language meaningfully change from last year? What is analytically
notable here?

### `esg_themes`
- **Type**: str (pipe-separated list of theme codes)
- **Source**: LLM
- **What it contains**: which of the 12 predefined themes the LLM
  identified as present in this proxy (e.g.,
  "BOARD_DIVERSITY|EMISSIONS_TARGETS|HUMAN_CAPITAL")
- **Why included**: A multi-label classification of ESG content.
  Multi-label rather than single-label because proxies routinely
  emphasize several themes simultaneously. Stored as a pipe-separated
  string for CSV friendliness; expand with `.str.split("|")` for
  analysis.

### `climate_commitment`
- **Type**: str (verbatim quote) or null
- **Source**: LLM
- **What it contains**: the literal text of the company's most specific
  climate commitment in this proxy, or null if none stated
- **Why included**: Captures the company's exact phrasing. "Net zero by
  2050" reads differently from "net zero across our financing activities
  and operations by 2050" -- both are net-zero commitments, but they
  cover very different scopes. The verbatim quote preserves that nuance.

### `dei_disclosure_quality`
- **Type**: str (one of: "LOW", "MEDIUM", "HIGH", null)
- **Source**: LLM
- **What it contains**: LLM's three-level grade of DEI disclosure
  substance, where LOW = vague boilerplate, MEDIUM = named programs but
  few metrics, HIGH = specific programs AND quantitative metrics
- **Why included**: Distinguishing real DEI disclosure from boilerplate
  is the kind of judgement that requires reading comprehension. The
  grade gives us a coherent 3-level scale to track over time. The
  collapse of HIGH grades from 5 (2021) to 1 (2023) is one of the
  cleanest signals of the post-SCOTUS DEI retreat.

### `changed_from_prior`
- **Type**: bool or null
- **Source**: LLM (comparing current year's ESG section to prior year's)
- **What it contains**: whether the LLM judges that the ESG content
  meaningfully changed from the prior year's proxy
- **Why included**: 100% of 2016-2024 proxies are technically different
  from year to year (companies edit them annually). The question is
  whether the change is substantive -- new commitments, retracted
  language, new emphasis. The LLM is much better at this comparison
  judgement than any character-distance metric.

### `change_confidence`
- **Type**: str (one of: "HIGH", "MEDIUM", "LOW", null)
- **Source**: LLM
- **What it contains**: the LLM's confidence in its own
  `changed_from_prior` judgement
- **Why included**: Lets users filter the dataset to high-confidence
  signals only. Excluding LOW-confidence rows is a defensible way to
  reduce noise in change-detection analyses.

### `change_summary`
- **Type**: str (1-2 sentences) or null
- **Source**: LLM
- **What it contains**: a brief description of what changed from the
  prior year, or "No material change" or "No prior year available"
- **Why included**: The boolean `changed_from_prior` says THAT it
  changed; this column says WHAT changed. Crucial for qualitative case
  studies and for any human-in-the-loop validation.

### `register`
- **Type**: str (one of: "FORMAL", "ASPIRATIONAL", "TECHNICAL",
  "COMPLIANCE")
- **Source**: LLM
- **What it contains**: the dominant rhetorical register of the ESG
  section
- **Why included**: Captures HOW companies are talking about ESG,
  independent of WHAT they are talking about. A proxy can be ESG-heavy
  in COMPLIANCE mode (legal-defensive) or ASPIRATIONAL mode
  (aspirational marketing-style), and the difference matters for
  interpretation.

### `analyst_notes`
- **Type**: str (2-3 sentences) or null
- **Source**: LLM
- **What it contains**: the LLM's free-text observation about what is
  strategically or analytically notable in this proxy
- **Why included**: A non-structured field captures observations that
  do not fit the structured schema. Notable additions, retracted
  commitments, unusual phrasings, sector outliers -- these emerge in
  the free-text analyst notes and would be lost if we restricted
  ourselves to typed fields only.

### `ngram_similarity`
- **Type**: float (0.0 to 1.0) or null
- **Source**: Jaccard similarity on character trigrams between current
  and prior year's ESG section
- **What it contains**: how textually similar this year's ESG section is
  to last year's (1.0 = identical, 0.0 = entirely different)
- **Why included**: A quantitative complement to the binary
  `changed_from_prior`. The LLM might judge a paragraph as "changed"
  even when 90% of the text is identical; this column lets users
  filter to high-similarity ("paragraph-edit") vs low-similarity
  ("rewrite") cases.

### `analysis_method`
- **Type**: str (one of: "llm", "keyword_fallback", "skipped")
- **Source**: the analyzer's success/failure tracking
- **What it contains**: which analysis method actually produced this
  row's LLM-analysis columns
- **Why included**: When the Anthropic API fails (rate limit, network
  error, malformed JSON output), the pipeline falls back to a keyword
  heuristic. This column lets downstream users filter to LLM-quality
  rows only.

---

## Group 6: Binary theme flags (12 columns)

For every theme in our taxonomy, we add a binary column indicating its
presence. This is a redundant encoding -- the same information is in
`esg_themes` as a pipe-separated string -- but it makes the data far
easier to use in pandas (no string parsing) and in Excel.

The 12 themes were chosen because they collectively cover the main
ESG disclosure areas common to U.S. proxy statements. They emerged from
reviewing the SEC's human-capital and climate disclosure rules, the
TCFD framework, and a representative sample of 2022-2024 proxies before
defining the taxonomy.

### `theme_climate_risk`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy treats climate change as a
  business risk
- **Why included**: TCFD-aligned framing. "Climate as risk" is the
  defensive corporate position and tracks regulatory pressure.

### `theme_climate_opportunity`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy treats the climate transition as
  a business opportunity
- **Why included**: The forward-looking, growth-positive framing.
  Companies that pivot from "risk" to "opportunity" language are
  signaling strategic repositioning, not just defensive disclosure.

### `theme_emissions_targets`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy mentions specific GHG/net-zero/
  carbon targets
- **Why included**: Distinguishes proxies that name specific commitments
  from those that only discuss climate at the topic level.

### `theme_board_diversity`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy discusses board composition
  diversity
- **Why included**: Board diversity is the highest-visibility component
  of corporate DEI. Its rise and fall in disclosure language is one of
  our key findings.

### `theme_workforce_dei`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy discusses workforce-wide DEI
  programs and metrics
- **Why included**: Workforce DEI (below the board level) is the more
  operational dimension of diversity disclosure. The sharp 2021-to-2024
  decline in this theme for Consumer Discretionary and Energy is the
  clearest signal of the post-SCOTUS retreat.

### `theme_human_capital`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy discusses human-capital
  management (retention, training, wellbeing)
- **Why included**: Human capital became a required disclosure under
  the SEC's November 2020 rule. The rise of this theme is the cleanest
  cause-and-effect in the dataset.

### `theme_esg_oversight`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy describes board / committee
  structures for ESG oversight
- **Why included**: This is the STRUCTURAL dimension of ESG. Our
  finding that this stayed stable while RHETORICAL ESG retreated is one
  of the key insights of the project.

### `theme_stakeholder_engagement`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy describes shareholder /
  stakeholder engagement processes
- **Why included**: Tracks the rise of "stakeholder capitalism" language
  in proxy filings; comparable to Part 1's stakeholder-vs-shareholder
  finding.

### `theme_exec_comp_linkage`
- **Type**: int (0 or 1)
- **What it contains**: 1 if executive compensation is tied to ESG
  metrics in some form
- **Why included**: ESG-linked pay is the strongest signal of how
  seriously a company integrates ESG into its incentive structure.

### `theme_supply_chain`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy discusses supply-chain
  sustainability or human-rights diligence
- **Why included**: A specific operational dimension of ESG; tracks the
  rise of supply-chain due-diligence disclosure rules in EU and US.

### `theme_political_lobbying`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy discloses political contributions
  or lobbying activity
- **Why included**: A historically separate ESG dimension that
  shareholder proposals have repeatedly tried to expand; tracking its
  prevalence is itself a research question.

### `theme_risk_disclosure`
- **Type**: int (0 or 1)
- **What it contains**: 1 if the proxy explicitly frames ESG matters
  using TCFD or similar climate-related risk frameworks
- **Why included**: Distinguishes proxies that use formal frameworks
  (TCFD, SBTi) from those that discuss ESG in ad-hoc language.

---

## Why this schema is structured the way it is

Three design principles drove the schema:

1. **Keep the raw text in the dataset.** Including `proxy_text_clean`
   and `esg_section_text` makes each row self-contained: any future
   researcher can re-run any analysis on the same text we saw, without
   having to re-scrape EDGAR. This adds storage cost (~150 MB) but
   eliminates the dependency on SEC and on our scraping success.

2. **Keep classical and LLM analysis separate.** Columns 17-23 are
   computed by deterministic rules; columns 24-33 are LLM judgements.
   Each set is recoverable on its own. A user who does not trust the
   LLM can rely only on classical signals; a user who does not trust
   keyword counts can rely on LLM themes. The two layers
   cross-validate each other.

3. **Provide both list and binary encodings of themes.** `esg_themes`
   gives the multi-label list; `theme_*` columns give the binary
   matrix. Binary columns are easier in pandas
   (`df.groupby("year")[theme_cols].mean()`) and easier in Excel
   (no string splitting). The list form is easier when the analyst
   wants to count themes per row or join across themes.

The combination produces a dataset that is easy to filter, easy to
aggregate, fully provenanced, and possible to verify back to the
original SEC document.
