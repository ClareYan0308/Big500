#!/usr/bin/env python3
"""run.py -- entry point for Part 4."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from compute import main
if __name__ == "__main__":
    main()
