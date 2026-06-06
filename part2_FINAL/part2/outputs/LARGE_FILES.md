# Large Files (hosted externally)

The two files below exceed GitHub's 100 MB per-file limit and are
hosted on Google Drive instead. They contain the cleaned full text of
each proxy statement; if you only need the analysis output without the
raw text, the `_no_text.csv` version (in this same folder) is sufficient.

## Files

| File | Size | Download |
|---|---|---|
| `part2_dataset.csv` | ~143 MB | [Google Drive link](PASTE_LINK_1_HERE) |
| `part2_dataset.json` | ~146 MB | [Google Drive link](PASTE_LINK_2_HERE) |

## What's in them

Same 45-column schema as `part2_dataset_no_text.csv` plus two large
text columns:
- `proxy_text_clean` -- the full cleaned text of each proxy statement
- `esg_section_text` -- the extracted ESG sub-section

See `../SCHEMA.md` for the column-by-column documentation.