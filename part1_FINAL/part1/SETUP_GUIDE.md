# Setup Guide

## Requirements

| Item | Notes |
|---|---|
| Python 3.11 | Avoid 3.12+ on Windows (build-tool issues for `lxml`/`pandas`) |
| Anthropic API key | Paid account; ~$5-15 total cost for the full 450-record run |
| Internet access to `web.archive.org` | The Wayback Machine must be reachable |

---

## Step 1: Get an Anthropic API key

1. Sign up / log in at https://console.anthropic.com/
2. Go to **API Keys** -> **Create Key**, copy the `sk-ant-api03-...` string
3. Add at least $10 of credit (the full pipeline costs roughly $5-15 in API usage)

---

## Step 2: Create an isolated environment

Using conda (recommended):

```bash
conda create -n part1 python=3.11 -y
conda activate part1
```

Or using venv:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
.venv\Scripts\activate        # Windows
```

---

## Step 3: Install dependencies

On Windows, install packages that need C compilation through conda first:

```bash
conda install numpy pandas lxml -y
pip install requests==2.31.0 trafilatura==1.6.3 beautifulsoup4==4.12.2 anthropic python-dotenv==1.0.0 tqdm==4.66.1
```

On Mac/Linux, a single command works:

```bash
pip install -r requirements.txt
```

---

## Step 4: Configure the API key

```bash
cp .env.example .env
```

Open `.env` in any text editor and set your key:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

No quotes, no spaces around the `=`.

---

## Step 5: Test the setup

Runs MSFT only for three years (2016, 2020, 2024) to verify everything works:

```bash
python run.py --test
```

A successful run prints `Pre-flight checks passed.` and finishes in under a minute.

---

## Step 6: Run the full pipeline

```bash
python run.py
```

Expected runtime: 40-60 minutes total
- Stage 1 (scrape): ~20-30 min
- Stage 2 (extract): ~1-2 min
- Stage 3 (LLM analysis): ~15-25 min
- Stage 4 (assemble): seconds

The pipeline is resumable. If interrupted, run `python run.py` again -- it will skip cached records and continue.

To force a fresh run:

```bash
python run.py --no-resume
```

---

## Step 7: Recover missing records (optional)

After the main run, some company-years may be missing because the URL hint did not find a Wayback snapshot. Two recovery scripts are provided in the same folder:

```bash
python recover.py    # CDX wildcard URL discovery
python recover2.py   # Alternative subdomain / known URL list
python recover3.py   # Cross-year URL reuse (uses URLs that worked in nearby years)
```

After each recovery script, refresh the analysis and final CSV:

```bash
python run.py --stages analyse assemble
```

---

## Outputs

All outputs land in `outputs/`:

```
outputs/
  part1_dataset.csv          -- Full 450-row dataset including page_text_clean
  part1_dataset_no_text.csv  -- Same dataset without the text column
  part1_dataset.json         -- JSON copy of the dataset
  scrape_manifest.json       -- Per-record scrape attempt log
  coverage_report.json       -- Coverage summary
  page_texts/                -- Individual cleaned text files per record
```

---

## Troubleshooting

**`web.archive.org` is unreachable** -- some networks block it. Try a VPN.

**`AuthenticationError: Invalid API Key`** -- check `.env` for stray spaces or duplicated `sk-ant-` prefixes; regenerate the key in the console if needed.

**`Error 402: credit balance too low`** -- add credit at https://console.anthropic.com/settings/billing

**Pipeline crashed mid-run** -- just run `python run.py` again. It resumes from where it stopped.

---

## File reference

| File | Purpose |
|---|---|
| `run.py` | Main entry point |
| `src/companies.py` | The 50-company universe with GICS sectors |
| `src/scraper.py` | Wayback Machine CDX API client |
| `src/extractor.py` | HTML text extraction (trafilatura + BeautifulSoup fallback) |
| `src/analyzer.py` | LLM analysis via Anthropic Messages API |
| `src/pipeline.py` | Four-stage orchestrator |
| `requirements.txt` | Python dependencies |
| `.env.example` | API key configuration template |
