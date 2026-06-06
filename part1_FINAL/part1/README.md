# Part 1 -- Stated Values: Scraping "About Us" Pages via the Wayback Machine

A pipeline that collects nine years of corporate "About Us" page snapshots
(2016-2024) for 50 large U.S. public companies, extracts clean body text,
and uses an LLM to identify themes, year-over-year change, and linguistic
register.

**Final coverage**: 431 / 450 snapshots scraped (95.8%); 410 records with
clean text; 400 with full LLM analysis.

---

## 1. What I did

I built a four-stage pipeline:

1. **Scrape** -- query the Wayback Machine CDX API for one snapshot per
   company per year, closest to July 1, and download the raw archived HTML.
2. **Extract** -- strip Wayback toolbar overlays, navigation, footers, and
   boilerplate, then extract clean body text using `trafilatura` (primary)
   with a `BeautifulSoup` fallback for sparse pages.
3. **Analyse** -- send each cleaned page to Claude Sonnet 4 via the
   Anthropic Messages API, along with the prior year's text, and ask for
   a JSON-structured judgement of theme categories, change-from-prior, and
   linguistic register.
4. **Assemble** -- combine all per-record JSON into a 30-column CSV dataset
   covering all 450 company-year pairs.

When the first pass left 156 records missing (because URL hints did not
match what was actually archived for some companies), I added three
recovery scripts that re-queried CDX with progressively broader strategies:

- `recover.py` -- CDX wildcard search to discover About-page paths on the
  main domain.
- `recover2.py` -- hand-curated alternative URLs (subdomains such as
  `about.bankofamerica.com`, `corporate.homedepot.com`, etc.) for the
  companies the first round could not find.
- `recover3.py` -- for the remaining gaps, reuse URLs that succeeded in
  adjacent years for the same company.

Together these brought coverage from 65% to 96%.

---

## 2. Why

The task is fundamentally about how large companies *describe themselves*
over time -- a record that no single source tracks systematically. The
Wayback Machine is the only public archive that captures dated snapshots
of corporate web pages going back to 2016, and its CDX API is the only
practical way to enumerate those snapshots in bulk. Using an LLM (rather
than keyword matching or a topic model) was a deliberate choice for three
reasons:

1. About-page language is dense and rhetorical -- short phrases like
   "stakeholder capitalism" or "net zero by 2050" carry meaning that
   bag-of-words approaches lose.
2. The change-detection task requires comparing two passages and
   summarizing what changed, which is exactly what generative models
   are good at.
3. Themes can co-occur (a page can emphasize both ESG and shareholder
   value), which an LLM handles cleanly and a single-label classifier
   does not.

Sector selection follows the GICS standard as of January 2024, ranked by
free-float market capitalization. Two corrections vs. naive groupings are
documented in `src/companies.py`:

- Alphabet (GOOGL) and Meta (META) are GICS *Communication Services*,
  not Information Technology -- so they are excluded from the Tech list.
- Visa (V) and Mastercard (MA) are GICS *Information Technology* (Data
  Processing sub-industry), not Financials -- so they are excluded from
  the Financials list.

---

## 3. Assumptions

1. **The mid-year snapshot is representative.** I select the snapshot
   whose timestamp is closest to July 1 of each calendar year. This
   avoids annual-report season (Q1/Q2) when companies may temporarily
   emphasize financial-results language, and avoids year-end refresh
   cycles. If a company changed its About page twice in a calendar
   year, only one version is captured.

2. **The first reachable URL hint is the About page.** Each company in
   `companies.py` has a priority-ordered list of URL hints; the scraper
   tries them in order and accepts the first one that yields a 200-status
   Wayback snapshot with at least 50 words of extracted text. I do not
   verify that the page is semantically an "About" page beyond this
   threshold.

3. **Trafilatura's main-content extraction is reliable.** I treat
   trafilatura's output as the clean body text whenever it returns at
   least 40 words. For sparser pages, I fall back to a manual
   BeautifulSoup pipeline that strips structural boilerplate by tag and
   by class/ID keyword.

4. **The LLM's judgement is the ground truth.** Theme classification and
   change detection have no human-coded reference set. I trust the LLM's
   output but record confidence scores for every judgement so downstream
   users can filter.

5. **Pages with fewer than 30 words after cleaning have no usable text.**
   Forty records hit this threshold and are excluded from analysis.

---

## 4. What I would do differently with more time

1. **Validate URL hints against a manual sample.** Before running 450
   scrapes, I would open one snapshot per company in a Wayback browser
   session and confirm that the URL hint targets the intended page. This
   would have saved the recovery work I had to do later.

2. **Pre-discover URLs with CDX wildcards by default.** Rather than
   hand-coding hints, the first pass could itself use a CDX domain-level
   search to discover the most-archived About-page path for each
   company per year. The `recover.py` script demonstrates this approach
   and could replace the hint table entirely.

3. **Replace binary change detection with a semantic diff.** Currently
   `changed_from_prior` is a Boolean plus a confidence level. A more
   useful signal would be a sentence-level diff: what claims were added,
   what were removed, what were rephrased. The structured prompt could
   be extended to produce this.

4. **Human-rater calibration on a 50-record sample.** Two or three
   independent annotators labelling the same sample would give me an
   inter-rater reliability score and an estimate of LLM accuracy versus
   human consensus. This is the single most important missing piece
   for academic credibility.

5. **Temporal embeddings, not just theme codes.** Embedding each snapshot
   with a sentence-transformer would let me track semantic drift
   trajectories continuously, not just as 0/1 theme flags. This would
   surface drift patterns the current theme set cannot capture (e.g.,
   the shift from "cloud-first" to "AI-first" within Technology).

6. **Cross-validate with the SEC EDGAR proxy statements.** The same
   companies file annual proxy statements that contain "Mission and
   Values" language. Comparing the About page to the proxy statement
   for the same year would reveal which themes are consumer-facing
   spin versus investor-facing commitments.

---

## 5. Known limitations

1. **19 records still missing (4.2%).** Despite three rounds of URL
   recovery, 19 company-year combinations could not be retrieved.
   These are concentrated in: (a) early years (2016-2018) for companies
   that had not yet established a stable About page URL -- Phillips 66,
   Booking Holdings, S&P Global, BlackRock; (b) very recent years
   (2023-2024) for companies that rebranded their corporate sites --
   UnitedHealth Group, Nike. All 19 are documented row-by-row in the
   dataset with the CDX query URL that was attempted.

2. **Wayback coverage is uneven across companies.** Smaller energy
   companies (HES, VLO) and consumer companies that use third-party
   platforms (BKNG) have sparser Wayback indexing than the megacaps,
   which means their snapshots come from less-ideal dates (sometimes
   November or January, not July).

3. **JavaScript-heavy pages may be empty in Wayback.** Wayback captures
   the served HTML, not the rendered DOM. Sites that use client-side
   rendering (some Salesforce pages, modern Adobe pages) archive as
   sparse HTML shells. Trafilatura handles many but not all of these;
   the 40 records with no usable text are mostly JS-heavy captures.

4. **LLM non-determinism.** The same page submitted twice to the model
   can produce slightly different theme codings. I cache analysis
   results to disk after the first run to ensure reproducibility within
   a single execution, but a fresh `--no-resume` run may yield small
   differences.

5. **Theme boundary fuzziness.** The boundary between
   STAKEHOLDER_CAPITALISM and COMMUNITY_IMPACT is not perfectly sharp;
   the model sometimes applies one where the other might fit equally
   well. I did not formally measure inter-prompt reliability.

6. **Sample frame is anchored to January 2024.** A company that was in
   the top 10 of its sector in 2024 but was much smaller in 2016 may
   have had a very different About page when it was a smaller company.
   The dataset captures the trajectory of *current giants*, not of
   companies that were giants in 2016.

7. **English text only.** Some companies have multilingual sites
   (Accenture, Schlumberger, Broadcom). I only collect the
   English-language version (`/us-en/`, `/en-us/`, or domain root),
   even when a non-English version may be the more canonical About
   page in the company's home market.

---

## Repository layout

```
part1/
+-- README.md             this file
+-- SUMMARY.md            written summary (Markdown)
+-- SUMMARY.docx          written summary (Word, 2 pages)
+-- SETUP_GUIDE.md        installation and run instructions
+-- run.py                main entry point (`python run.py`)
+-- requirements.txt
+-- .env.example          template for the API key
+-- src/
|   +-- companies.py      50-company universe with GICS sector mapping
|   +-- scraper.py        Wayback Machine CDX API client + HTML fetcher
|   +-- extractor.py      Trafilatura + BeautifulSoup text extractor
|   +-- analyzer.py       Anthropic Messages API client + theme analysis
|   +-- pipeline.py       Four-stage orchestrator
+-- outputs/
    +-- part1_dataset.csv          450 rows x 30 cols, includes page_text_clean
    +-- part1_dataset_no_text.csv  Same dataset, page_text_clean removed
    +-- coverage_report.json       Coverage summary
```

See `SETUP_GUIDE.md` for installation instructions and how to re-run.
