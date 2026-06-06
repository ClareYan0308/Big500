# Large Files (hosted externally)

The two files below exceed GitHub's 100 MB per-file limit and are
hosted on Google Drive instead. They contain the cleaned full text of
each proxy statement; if you only need the analysis output without the
raw text, the `_no_text.csv` version (in this same folder) is sufficient.

## Download

All large files are in this shared Google Drive folder:

**[Big500 -- Large Files (Google Drive)](https://drive.google.com/drive/folders/1uayqTVIiSYLHqUVvXER1LDnE8pMy7K-c?usp=drive_link)**

## Files in the folder

| File | Size | Description |
|---|---|---|
| `part2_dataset.csv` | ~143 MB | Full 45-column dataset including `proxy_text_clean` and `esg_section_text` |
| `part2_dataset.json` | ~146 MB | Same data in JSON format |

## What's in them

Same 45-column schema as `part2_dataset_no_text.csv` plus two large
text columns:

- `proxy_text_clean` -- the full cleaned text of each proxy statement
- `esg_section_text` -- the extracted ESG sub-section sent to the LLM

See `../SCHEMA.md` for the column-by-column documentation.