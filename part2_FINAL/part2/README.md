# Part 2 -- Lived Values: ESG Disclosure Analysis in DEF 14A Proxy Statements

A pipeline that collects DEF 14A (proxy statement) filings from SEC EDGAR
for the same 50 large U.S. public companies as Part 1, across 2016-2024,
then text-mines them for ESG disclosure content. Combines classical NLP
(keyword frequency, regex extraction) with LLM analysis (theme detection,
change summarization, register classification) to produce a structured
dataset of ESG disclosure evolution.

---

## 1. What I did

I built a four-stage pipeline that:

1. **Fetch** -- Queries the SEC EDGAR submissions API for each company,
   filters for `DEF 14A` filings between 2016 and 2024, picks the one
   filing per year closest to July 1, and downloads the primary HTML
   document.
2. **Parse** -- Cleans the proxy HTML to extract visible text, then uses
   regex pattern matching to locate the ESG / sustainability / human
   capital section within the proxy. Computes classical-NLP signals:
   counts of climate, diversity, and governance keywords; extracts
   numeric quantitative targets (net-zero years, percentage women on
   board).
3. **Analyse** -- Sends the ESG section (or first 8000 characters of the
   full proxy) to Claude Sonnet 4 along with the prior year's text. The
   model returns structured JSON containing theme classifications,
   change detection, climate-commitment extraction, DEI disclosure
   quality grade, and analyst notes.
4. **Assemble** -- Combines all per-record outputs into a 35-column CSV
   dataset, one row per company-year.

The same 50 companies and same 2016-2024 window as Part 1 enable direct
side-by-side comparison: Part 1 captures what companies *say* about
themselves on their public-facing About pages; Part 2 captures what they
*disclose* to the SEC in legally-filed governance documents.

Three documents accompany the code:

- **[SUMMARY.docx / SUMMARY.md](SUMMARY.md)** -- a 2-page non-technical
  written summary of headline findings
- **[SCHEMA.md](SCHEMA.md)** -- column-by-column documentation of the
  45-column dataset with the rationale for every column
- **[ANALYSIS.md](ANALYSIS.md)** -- methodology justification and the
  full text-mining analysis covering within-company change,
  cross-sector variation, and correlations with external events

---

## 2. Why

**Why proxy statements?**

The task allows ESG reports, sustainability reports, DEI reports, or
proxy statements. I chose proxy statements for four reasons:

1. **Coverage is guaranteed at 100%.** Every U.S. public company is
   legally required to file a DEF 14A annually. Voluntary ESG and
   sustainability reports have huge coverage gaps -- many companies in
   our sample didn't begin publishing standalone ESG reports until
   2019-2021.
2. **The source is free, official, and programmatic.** SEC EDGAR
   provides a clean JSON submissions API with documented endpoints, no
   API key required, no rate-limit fees.
3. **ESG content in proxies is itself a useful research signal.** The
   growth of dedicated ESG sections within proxy statements --
   from zero or one paragraph in 2016 to multi-page disclosures by
   2022 -- IS a key finding rather than a problem to work around.
4. **Side-by-side comparison with Part 1.** Part 1 captured
   marketing-style "stated values." Proxy statements capture
   legally-filed disclosures to a regulator. Comparing the two for the
   same 50 companies in the same 9 years lets us ask: do companies
   *say* the same things to their customers and to their shareholders?

**Why a hybrid classical + LLM approach?**

Classical NLP (keyword counts, regex extraction, n-gram similarity) is
fast, free, and reproducible -- I can rerun keyword counts on the same
text and get identical results. It's well-suited to objective questions
like "How many times does the word 'climate' appear?"

LLM analysis (Claude Sonnet 4) is better at interpretive questions
that classical methods cannot answer reliably: "Is this DEI disclosure
specific enough to be meaningful?", "What changed between this year's
proxy and last year's?", "Does this paragraph describe a real
commitment or boilerplate language?"

I use them together: classical signals are recorded as fact columns
(`climate_mention_count`, `pct_women_board`, etc.), while the LLM's
judgement appears alongside but separately (`dei_disclosure_quality`,
`change_summary`). Downstream users can filter or weight either
signal type independently.

---

## 3. Assumptions

1. **The filing year is the year that matters.** A DEF 14A filed in
   March 2024 covers fiscal-year 2023 events but reflects the company's
   *current* disclosure posture as of early 2024. We index by filing
   calendar year, not fiscal year.

2. **One proxy per year per company.** When EDGAR returns multiple DEF
   14A filings in a single calendar year (rare; happens for merger
   proxies), we pick the one whose filing date is closest to July 1.
   Amendments (DEFA14A) and preliminary proxies (PRE 14A) are excluded.

3. **The first matching ESG heading is the ESG section.** Section
   detection uses regex over a list of common heading patterns:
   "Environmental, Social and Governance", "Sustainability", "Human
   Capital Management", "Diversity, Equity and Inclusion", etc. We take
   the first match and read forward until the next major heading
   (e.g., "Compensation Discussion and Analysis") or 8000 characters,
   whichever comes first.

4. **Companies with no detected ESG section have no explicit ESG
   disclosure.** `has_explicit_esg_section` is a meaningful binary
   signal in itself: in 2016, many companies did not have any dedicated
   ESG section; by 2024, nearly all do.

5. **Quantitative target language is detectable via regex.** We use
   patterns like `net[\s-]?zero.*?(20\d{2})` to extract net-zero target
   years. This catches the standard formulations but will miss creative
   phrasings ("achieve carbon neutrality within the decade").

6. **The LLM's theme classifications are the analytical ground truth.**
   We trust the LLM's judgement of which themes are present, but record
   keyword counts in parallel as a sanity check.

---

## 4. What I would do differently with more time

1. **Add a proxy-statement-specific text extractor.** Many proxy HTML
   filings use legacy table-based layouts with hidden formatting
   metadata. A custom extractor that understands SEC document
   structure (e.g., the `<TABLE>` patterns used for board diversity
   matrices) would extract more structured data than BeautifulSoup's
   general-purpose parsing.

2. **Extract structured board diversity tables.** Recent proxies often
   contain explicit board-diversity matrices (skills x director,
   demographics x director). I extract only an aggregate
   `pct_women_board` percentage; with more time I would parse the
   full skills-and-demographics matrix into structured columns.

3. **Compare to standalone ESG/sustainability reports.** A natural
   extension is to fetch each company's standalone ESG report (where
   it exists) and compare the language to the proxy ESG section. Are
   the proxy disclosures a subset, a superset, or a different framing
   of the same content?

4. **Topic modeling across the full corpus.** I focus on per-record
   theme classification. A complementary lens would be LDA or BERTopic
   over the entire 9-year corpus to discover topics empirically rather
   than confirming pre-defined ones.

5. **Sentiment scoring of ESG sections.** I capture `register`
   (formal/aspirational/technical/compliance) but not sentiment.
   A VADER or finBERT score per ESG section would surface whether
   the tone of ESG disclosure becomes more cautious or more confident
   over time.

6. **Anchor the analysis to external events.** Identify proxies filed
   shortly after major external events (BRT 2019, Floyd 2020, SCOTUS
   affirmative-action 2023, anti-ESG legislation 2022-2024) and test
   whether ESG language responds differently across sectors.

---

## 5. Known limitations

1. **Proxy ESG sections are heterogeneous.** Some companies dedicate
   a multi-page section with sub-headings; others bury ESG content in
   the audit committee report or governance section. Our regex picks up
   the first match, which may not be the most substantive ESG content.

2. **HTML parsing of older proxies (2016-2017) is noisier.** Earlier
   filings used older HTML conventions with more nested tables; some
   text fragments may be lost or reordered during extraction.

3. **Year coverage is bounded by company existence.** Companies that
   went public after 2016 (e.g., Tesla was public but had limited
   filings history at SEC's electronic system level; Booking Holdings
   renamed mid-period) may have fewer than 9 records.

4. **`pct_women_board` extraction is heuristic.** We accept any "X% of
   directors are women" or "X% women" pattern between 10 and 80, which
   may catch false positives in unrelated contexts. We treat this as
   suggestive rather than authoritative.

5. **LLM non-determinism.** The same proxy submitted twice may yield
   slightly different theme codings. Results are cached after the first
   run for reproducibility within a single execution, but a
   `--no-resume` rerun may produce small differences.

6. **The "ESG section" can extend beyond what we extract.** Our 8000
   character cap is designed to keep LLM input bounded. Companies
   whose ESG section is longer than 8000 characters (some Tech and
   Financials companies) get truncated; the truncation point is
   chosen at a sentence boundary but does cut off later content.

7. **SEC EDGAR has small but real gaps for older filings.** Filings
   prior to 2017 occasionally have malformed primary-document
   references in the submissions index; in those cases the record is
   marked MISSING with the reason recorded in `missing_reason`.

---

## Dataset schema

Every one of the 45 columns is documented with its purpose and analytical
justification in [SCHEMA.md](SCHEMA.md). Brief summary by group:

| Group | Columns | Count |
|---|---|---|
| Identifiers | ticker, company_name, sector, year | 4 |
| Filing metadata | cik, accession_number, filing_date, filing_url, scrape_status, missing_reason | 6 |
| Document content | doc_size_bytes, total_word_count, esg_section_word_count, has_explicit_esg_section, proxy_text_clean, esg_section_text | 6 |
| Classical-NLP signals | climate_mention_count, diversity_mention_count, governance_mention_count, esg_keyword_density, net_zero_target_year, pct_women_board, has_quantitative_targets | 7 |
| LLM analysis | esg_themes, climate_commitment, dei_disclosure_quality, changed_from_prior, change_confidence, change_summary, register, analyst_notes, ngram_similarity, analysis_method | 10 |
| Binary theme flags | theme_climate_risk, ... theme_risk_disclosure (12 themes) | 12 |

See SCHEMA.md for the full column-by-column documentation with rationale.

---

## Repository layout

```
part2/
+-- README.md             this file
+-- SUMMARY.md            written summary (Markdown)
+-- SUMMARY.docx          written summary (Word, 2 pages)
+-- SCHEMA.md             column-by-column schema with justifications
+-- ANALYSIS.md           methodology justification + within-company / cross-sector / external-event analysis
+-- SETUP_GUIDE.md        installation and run instructions
+-- run.py                main entry point (`python run.py`)
+-- requirements.txt
+-- .env.example          template for the API key
+-- src/
|   +-- companies.py      50-company universe with CIK mapping
|   +-- edgar_fetcher.py  SEC EDGAR client for DEF 14A filings
|   +-- proxy_parser.py   HTML cleaner + ESG-section detector + NLP signals
|   +-- analyzer.py       Anthropic API client + theme analysis
|   +-- pipeline.py       Four-stage orchestrator
+-- outputs/
    +-- part2_dataset.csv          ~450 rows x 35 cols, includes texts
    +-- part2_dataset_no_text.csv  Same without proxy_text_clean / esg_section_text
    +-- coverage_report.json       Coverage summary
    +-- fetch_manifest.json        Per-filing fetch log
    +-- esg_sections/              Individual .txt files per record
```

See `SETUP_GUIDE.md` for installation and run instructions.

## Note on large files

Two of the output files exceed GitHub's 100 MB per-file limit and are
hosted on Google Drive instead:

- `outputs/part2_dataset.csv` (~143 MB) -- full dataset with proxy text
- `outputs/part2_dataset.json` (~146 MB) -- JSON version

See [outputs/LARGE_FILES.md](outputs/LARGE_FILES.md) for download links.
The smaller `outputs/part2_dataset_no_text.csv` (in this repo, ~400 KB)
contains all 45 columns except the two large text columns, and is
sufficient for most analyses.
