# Part 3 -- Organizational Authenticity Index

A measure of organizational authenticity, defined as the degree of
alignment between what a company says it values (Part 1's About-page
analysis) and what its formal disclosures suggest it actually
prioritizes (Part 2's proxy-statement analysis).

The full construct reasoning is documented in
[METHODOLOGY.md](METHODOLOGY.md). This README covers the standard
five sections required by the brief.

---

## 1. What I did

I built an index that measures, for each (company, year) pair, the
gap between a STATED ESG-identity score derived from Part 1 and an
ACTUAL ESG-substance score derived from Part 2. The index has a
single number on a 0-100 scale plus a signed direction
(over-claim vs. under-claim) and a category (ALIGNED / GREENWASH-RISK /
STEALTH).

The pipeline:

1. **Load** Part 1's CSV (About-page theme analysis) and Part 2's CSV
   (proxy-statement ESG analysis). Filter to records that received
   full LLM analysis in both datasets.
2. **Compute the STATED score (S)** as the share of three Part 1
   ESG-related identity themes present on the company's About page
   that year.
3. **Compute the ACTUAL score (A)** as the unweighted mean of four
   normalized Part 2 substance indicators: ESG keyword density,
   presence of an explicit ESG section, DEI disclosure quality grade,
   and presence of quantitative ESG targets.
4. **Convert** both S and A to within-year percentile ranks (0-100).
5. **Compute** the Authenticity Index as 100 minus the absolute gap
   between the two ranks, and the signed gap separately for direction.
6. **Categorize** rows into ALIGNED, STEALTH, or GREENWASH-RISK based
   on the signed gap, with a 15-percentile-point tolerance.
7. **Validate** by checking five intuitive cases (TSLA, BRK-B, CVX,
   NVDA, MSFT) against the brief's "make intuitive sense" criterion.

Outputs are a per-record CSV, a per-company summary CSV, a JSON
distributional report, and two visualizations.

---

## 2. Why

**Why the chosen construct.** The brief asks for "alignment between
what a company says it values and what its disclosures and behaviors
suggest it actually prioritizes." We can observe two of those three:
public statements (Part 1's About pages) and formal disclosures (Part
2's proxies). Behavior itself -- emissions, hiring numbers, regulatory
actions -- is outside our two datasets. So we deliberately measure
disclosure-disclosure alignment and document this limitation explicitly.

**Why marketing copy vs. legal disclosure as the two sides.** About
pages are marketing -- no SEC liability, no audit, written by
communications teams for the general public. Proxies are legal
disclosures -- SEC-filed, auditable, written by lawyers for
shareholders. The two are written by different teams under different
incentives. If they tell the same story about ESG, that is evidence
of organizational coherence. If they diverge, that divergence is
itself meaningful.

**Why per-year percentile ranks rather than raw scores.** S has four
discrete values; A is continuous and rises across years. Comparing
raw S to raw A would penalize companies in early years (when average
disclosure was lower). Per-year percentile rank removes both the
scale issue and the year drift, letting the index measure relative
alignment within each year.

**Why a bidirectional measure (STEALTH vs. GREENWASH-RISK).** A
company that says big and delivers small is misaligned. A company
that says nothing and delivers a lot is ALSO misaligned, just in the
opposite direction. The signed gap lets analysts separate these two
substantively different stories.

The full reasoning is in [METHODOLOGY.md](METHODOLOGY.md).

---

## 3. Assumptions

1. **Disclosure coherence is a reasonable proxy for authenticity.**
   When marketing and legal disclosure say the same thing, we assume
   that reflects an underlying organizational coherence, not
   coincidence. This is defensible but not provable.

2. **The three Part 1 themes and four Part 2 indicators chosen
   actually map to the same construct.** We chose them carefully but
   the mapping is a research-design choice, not a discovery.

3. **A 15-percentile-point gap is the right alignment threshold.** A
   smaller threshold would call almost everyone misaligned; a larger
   one would call almost everyone aligned. We chose 15 as a defensible
   middle, but it is a judgement call.

4. **Equal weighting of the four ACTUAL components is fair.** We have
   no defensible basis for a particular weighting, and giving more
   weight to any one indicator would amount to building a thesis into
   the methodology.

5. **Per-year normalization is preferable to cross-year.** This is a
   substantive choice: we measure alignment given the prevailing
   norms of disclosure in each year, not against a fixed 2016
   baseline. Researchers wanting absolute change can use the raw
   S_stated and A_actual columns instead.

---

## 4. What I would do differently with more time

1. **Add a third dimension: behavior.** Pair the disclosure-disclosure
   alignment with at least one behavioral measure. Candidates: actual
   emissions data (CDP), workforce demographics (EEO-1 filings),
   regulatory enforcement actions (DOJ/EPA databases). A
   three-way alignment index would more deeply measure
   authenticity in the way the brief implies.

2. **Sensitivity analyses on every methodological choice.** Re-run
   the index using different theme subsets for S, different
   weightings for A, and different alignment thresholds. Report the
   ranking stability under these variations -- our top STEALTH and
   GREENWASH-RISK companies should remain identifiable even when
   methodological choices change.

3. **Time-series modeling of authenticity trajectories.** For each
   company, fit a simple trend (linear, with a possible 2020 break-
   point) to its yearly authenticity scores. Are companies converging
   toward alignment over time, diverging, or moving without pattern?

4. **Industry-event case studies.** For each large misalignment (gap
   > 30 in absolute value), examine whether external events
   (regulatory action, news cycle, executive turnover) preceded or
   followed the misalignment. This would address a key question:
   does authenticity respond to events, or is it a stable trait?

5. **Inter-rater reliability for the underlying theme codings.** Our
   index inherits whatever noise lives in Part 1 and Part 2's LLM
   theme classifications. A second LLM (or human coder) on a sample
   of 50 records would let us estimate how much noise.

---

## 5. Known limitations

1. **Both sides measure language, not behavior.** We compare
   marketing text to legal disclosure text. We do not measure actual
   organizational behavior. A company can score 100 on this index
   while being entirely unsuccessful at acting on either disclosure.

2. **The theme mapping is interpretive.** Three Part 1 themes
   mapped to "ESG identity" and four Part 2 indicators mapped to
   "ESG substance." Different analysts could choose different mappings
   and produce different rankings. We have documented our choice in
   METHODOLOGY.md but cannot prove it is optimal.

3. **The two documents serve different audiences.** About pages
   address customers and the general public; proxies address
   shareholders and regulators. A company that speaks differently to
   different audiences is engaged in normal corporate communication.
   Calling that "inauthentic" is a value judgement the construct
   embeds but does not prove.

4. **Per-year percentile ranking removes absolute information.**
   A company that has steadily increased both its claimed and actual
   ESG language since 2016 will not be flagged as having improved
   its authenticity. The index measures within-year relative
   alignment, not absolute commitment.

5. **The sample is biased toward sophisticated communicators.** Our
   50 companies are the largest in their sectors and have
   professional IR teams. Smaller companies might show more naive
   alignment (or misalignment) than this index can capture.

6. **The index treats over-claim and under-claim symmetrically.**
   A company that talks little and discloses a lot (STEALTH) gets
   the same headline index as one that talks a lot and discloses
   little (GREENWASH-RISK). The signed gap separates these but the
   headline number does not.

The full list with discussion is in METHODOLOGY.md Section 8.

---

## Repository layout

```
part3/
+-- README.md                this file
+-- METHODOLOGY.md           detailed construct reasoning (the key deliverable)
+-- SUMMARY.md               written summary (Markdown)
+-- SUMMARY.docx             written summary (Word, 1 page)
+-- run.py                   entry point (`python run.py`)
+-- requirements.txt
+-- src/
|   +-- compute_index.py     index computation
+-- data/                    bundled inputs (so part3 is self-contained)
|   +-- part1_dataset_no_text.csv    snapshot of Part 1 output
|   +-- part2_dataset_no_text.csv    snapshot of Part 2 output
+-- outputs/
    +-- authenticity_index.csv     393 rows: per-company-per-year scores
    +-- company_summary.csv        50 rows: per-company averages
    +-- distributional_stats.json  summary statistics
    +-- authenticity_scatter.png   S vs A scatter plot with quadrant labels
    +-- authenticity_distribution.png  histogram of the index
```

The pipeline reads from `data/` by default so part3 runs without needing
parts 1 and 2 to be sibling directories on disk. To re-run with updated
inputs from a different location, pass `--part1 <path>` and `--part2 <path>`.

To re-run:

```bash
pip install -r requirements.txt
python run.py
```
