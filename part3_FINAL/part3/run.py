#!/usr/bin/env python3
"""run.py -- Entry point for Part 3. Just calls src/compute_index.py.

Usage:
    python run.py

Inputs (resolved relative to this file):
    ../part1/outputs/part1_dataset_no_text.csv
    ../part2/outputs/part2_dataset_no_text.csv

Outputs (in outputs/):
    authenticity_index.csv
    company_summary.csv
    distributional_stats.json
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from compute_index import main
if __name__ == "__main__":
    main()
