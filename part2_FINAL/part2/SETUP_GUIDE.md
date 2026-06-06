# Part 2 -- Setup Guide

## Requirements

| Item | Notes |
|---|---|
| Python 3.11 | Same as Part 1; you can reuse the `part1` conda env |
| Anthropic API key | Same key you used for Part 1 |
| Internet access to `data.sec.gov` | SEC EDGAR is free and unrestricted |

Note: You do NOT need any SEC API key. EDGAR is free and open. The only API
key needed is for Anthropic (used by the LLM analysis stage).

---

## Step 1: Open the project in Cursor

```
Desktop/
+-- part1_deliverable/
|   +-- part1/             <-- Part 1 (already done)
+-- part2_deliverable/
    +-- part2/             <-- Open this folder in Cursor
```

---

## Step 2: Activate environment

You can reuse the Part 1 conda environment:

```bash
conda activate part1
```

Or create a separate one for Part 2:

```bash
conda create -n part2 python=3.11 -y
conda activate part2
conda install pandas lxml -y
```

---

## Step 3: Install dependencies

```bash
cd part2
pip install -r requirements.txt
```

If you reused the `part1` env, you may only need to upgrade `anthropic`:

```bash
pip install -U anthropic
```

---

## Step 4: Configure API key

```bash
cp .env.example .env
notepad .env       # Windows
# or
nano .env          # Mac/Linux
```

Set your key inside `.env`:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

No quotes, no spaces around the `=`.

---

## Step 5: Test the setup

Test on MSFT only for three years:

```bash
python run.py --test
```

A successful test takes about a minute and prints something like:

```
[ok]  Pre-flight checks passed.
[TEST MODE]  MSFT only, years 2016/2020/2024
=== STAGE 1: FETCH from SEC EDGAR ===
...
[MSFT 2016] OK -- ...
[MSFT 2020] OK -- ...
[MSFT 2024] OK -- ...
=== STAGE 2: PARSE proxy HTML ===
...
=== STAGE 3: LLM ANALYSIS ===
...
=== STAGE 4: ASSEMBLE dataset ===
[OK]  Done. Outputs in: outputs/
```

---

## Step 6: Run the full pipeline

```bash
python run.py
```

Expected runtime:

- Stage 1 (fetch from EDGAR): ~10-15 min (450 filings, polite rate)
- Stage 2 (parse HTML): ~5 min
- Stage 3 (LLM analysis): ~15-25 min (~450 API calls)
- Stage 4 (assemble): seconds
- **Total: 30-50 minutes**

The pipeline is resumable. If interrupted, just run `python run.py` again
and it will skip cached records.

To force a fresh run from scratch:

```bash
python run.py --no-resume
```

To run only specific stages:

```bash
python run.py --stages fetch parse        # only download and parse
python run.py --stages analyse assemble   # only analyze and build CSV
```

---

## Step 7: Inspect the output

```
outputs/
+-- part2_dataset.csv          full dataset with proxy text and ESG section
+-- part2_dataset_no_text.csv  same dataset without the text columns
+-- part2_dataset.json         JSON format of the dataset
+-- coverage_report.json       per-sector coverage summary
+-- fetch_manifest.json        log of every SEC EDGAR fetch attempt
+-- esg_sections/              individual .txt files per record
    +-- AAPL_2016.txt
    +-- AAPL_2017.txt
    ...
```

The main deliverable is `part2_dataset.csv`. The `_no_text` version is
useful when you want to open the file in Excel without it being slow.

---

## Troubleshooting

**`AuthenticationError: Invalid API Key`** -- check `.env` for stray
spaces or duplicated `sk-ant-` prefixes; regenerate the key in the
Anthropic console if needed.

**`Error 402: credit balance too low`** -- top up at
https://console.anthropic.com/settings/billing

**Pipeline crashed mid-run** -- run `python run.py` again. It resumes
from where it stopped, skipping anything already cached.

**EDGAR returns HTTP 403** -- you forgot the User-Agent header. The code
sets one automatically (`Part2 Research Bot research@example.com`), but
if you want to use your own, edit the constant `USER_AGENT` at the top
of `src/edgar_fetcher.py`.

**A specific company has no DEF 14A in a specific year** -- this is
expected for newer companies (e.g., Booking Holdings before its rename)
and is recorded with `scrape_status=MISSING` and a reason code.

---

## File reference

| File | Purpose |
|---|---|
| `run.py` | Main entry point |
| `src/companies.py` | The 50-company universe with CIK mapping |
| `src/edgar_fetcher.py` | SEC EDGAR client (downloads DEF 14A filings) |
| `src/proxy_parser.py` | HTML cleaner + ESG section detector + NLP signals |
| `src/analyzer.py` | LLM analysis via Anthropic Messages API |
| `src/pipeline.py` | Four-stage orchestrator |
| `requirements.txt` | Python dependencies |
| `.env.example` | API key configuration template |
