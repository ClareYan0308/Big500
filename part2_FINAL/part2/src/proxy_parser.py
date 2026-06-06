"""
proxy_parser.py -- Parse DEF 14A HTML filings.

Tasks:
  1. Extract clean visible text from SEC HTML (which is messy, full of
     tables, font tags, and inline styles from older filings).
  2. Identify the ESG / sustainability / human-capital / DEI section(s)
     using regex on common headings.
  3. Compute classical-NLP signals from the cleaned text:
       - Climate keyword frequency
       - Diversity keyword frequency
       - Governance keyword frequency
       - Net-zero target presence
       - Quantitative-target presence
       - Board diversity table presence

Why these signals:
  These are objective, reproducible measures that complement the LLM's
  judgement. Keyword counts are cheap (no API calls) and can be used to
  validate or sanity-check the LLM's theme classifications. The presence
  of a board-diversity table is itself a meaningful disclosure choice.
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


# ---- Keyword groups (lowercased, matched case-insensitively) ----
CLIMATE_KEYWORDS = [
    "climate", "carbon", "emissions", "greenhouse gas", "ghg", "net zero",
    "net-zero", "decarboniz", "tcfd", "renewable energy", "scope 1", "scope 2",
    "scope 3", "paris agreement", "1.5 degree", "science-based target", "sbti",
    "low carbon", "climate change", "climate risk", "climate-related",
]

DIVERSITY_KEYWORDS = [
    "diversity", "inclusion", "equity", "dei", "de&i", "deib",
    "underrepresented", "women in leadership", "gender", "racial", "ethnic",
    "lgbtq", "belonging", "pay equity", "minority", "diverse workforce",
    "diverse talent", "underrepresented minorities",
]

GOVERNANCE_KEYWORDS = [
    "esg oversight", "sustainability committee", "esg committee",
    "esg-linked compensation", "esg metrics in compensation",
    "board oversight of esg", "nominating and governance",
    "human capital management", "board diversity",
]

# Patterns that extract specific quantitative commitments
NET_ZERO_PATTERN = re.compile(
    r"net[\s-]?zero[\s\w]{0,30}?(20\d{2})", re.IGNORECASE
)
CARBON_NEUTRAL_PATTERN = re.compile(
    r"carbon[\s-]?neutral[\s\w]{0,30}?(20\d{2})", re.IGNORECASE
)
PCT_WOMEN_BOARD_PATTERN = re.compile(
    r"(\d{1,2})\s?%\s?(?:of\s+(?:our\s+)?(?:directors|board)|women|female)",
    re.IGNORECASE
)
QUANTITATIVE_TARGET_PATTERN = re.compile(
    r"\b(\d{1,3}\s?%|by\s+20[2-5]\d)\b", re.IGNORECASE
)

# ---- ESG section heading patterns ----
ESG_SECTION_HEADINGS = [
    r"environmental,?\s+social,?\s+(?:and\s+)?governance",
    r"esg\s+matters",
    r"esg\s+oversight",
    r"sustainability",
    r"corporate\s+(?:social\s+)?responsibility",
    r"human\s+capital(?:\s+management)?",
    r"diversity,?\s+equity,?\s+(?:and\s+)?inclusion",
    r"our\s+approach\s+to\s+esg",
    r"climate\s+(?:change|strategy|risk)",
]

# Tags to strip wholesale
_STRIP_TAGS = {"script", "style", "noscript", "iframe", "img", "svg",
               "head", "meta", "link", "title"}


def html_to_text(html: str) -> str:
    """
    Convert proxy HTML to clean visible text.

    Proxy statements often have heavy table-based layouts. We:
      - Remove scripts/styles/images/etc.
      - Convert <br>, <p>, <div>, <tr> to newlines
      - Get_text with newline separators
      - Normalize unicode and whitespace
      - Drop very short lines (likely table cells with single numbers)
    """
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for tag in _STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Convert structural tags to newlines so get_text preserves layout
    for tag in soup.find_all(["br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4"]):
        tag.append("\n")

    raw = soup.get_text(separator=" ")
    # Normalize unicode (smart quotes, em-dash, etc.)
    raw = unicodedata.normalize("NFKC", raw)
    # Replace non-breaking spaces and similar
    raw = raw.replace("\xa0", " ").replace("\u2028", "\n").replace("\u2029", "\n")
    # Collapse runs of whitespace within lines but preserve line breaks
    lines = []
    for ln in raw.split("\n"):
        ln = re.sub(r"\s+", " ", ln).strip()
        if len(ln) >= 4:
            lines.append(ln)
    # Deduplicate consecutive identical lines (table layout artifacts)
    deduped = []
    prev = None
    for ln in lines:
        if ln != prev:
            deduped.append(ln)
        prev = ln
    return "\n".join(deduped).strip()


def find_esg_section(text: str) -> Optional[str]:
    """
    Locate the ESG / sustainability / human-capital section in the proxy text
    by searching for known heading patterns.

    Strategy: find the FIRST occurrence of any ESG-related heading, then
    extract text until the next major heading OR ~8000 characters, whichever
    comes first. This gives a focused but bounded ESG passage for LLM analysis.
    """
    if not text:
        return None

    # Find earliest match across all heading patterns
    best_start = None
    best_pattern = None
    for pat in ESG_SECTION_HEADINGS:
        m = re.search(r"(?i)\b" + pat + r"\b", text)
        if m and (best_start is None or m.start() < best_start):
            best_start = m.start()
            best_pattern = pat

    if best_start is None:
        return None

    # Extract up to 8000 chars (or until next major section heading)
    section = text[best_start: best_start + 8000]

    # Try to cut at the next major heading (e.g., "compensation discussion",
    # "audit committee report") to avoid bleeding into unrelated sections
    cut_patterns = [
        r"\bcompensation\s+discussion\s+and\s+analysis\b",
        r"\baudit\s+committee\s+report\b",
        r"\bsecurity\s+ownership\b",
        r"\bcertain\s+relationships\s+and\s+related\s+transactions\b",
        r"\bratification\s+of\s+(?:the\s+)?appointment\b",
        r"\bproposal\s+\d+",
    ]
    earliest_cut = len(section)
    for cp in cut_patterns:
        m = re.search(r"(?i)" + cp, section[200:])  # don't cut at the very start
        if m:
            cut_pos = 200 + m.start()
            if cut_pos < earliest_cut:
                earliest_cut = cut_pos
    section = section[:earliest_cut].strip()

    return section if len(section.split()) >= 30 else None


def count_keyword_mentions(text: str, keywords: list) -> int:
    """Count case-insensitive occurrences of any keyword in the text."""
    if not text:
        return 0
    lower = text.lower()
    total = 0
    for kw in keywords:
        # Use word boundaries where the keyword is a simple word; otherwise
        # plain substring (e.g., "decarboniz" matches "decarbonization")
        if kw.isalpha() and " " not in kw and "-" not in kw and "&" not in kw:
            total += len(re.findall(r"\b" + re.escape(kw) + r"\b", lower))
        else:
            total += lower.count(kw)
    return total


def extract_net_zero_year(text: str) -> Optional[str]:
    """Extract the first net-zero / carbon-neutral target year mentioned."""
    if not text:
        return None
    for pat in (NET_ZERO_PATTERN, CARBON_NEUTRAL_PATTERN):
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def extract_pct_women_board(text: str) -> Optional[int]:
    """
    Extract the first reasonable percentage women/female on board.
    Returns an integer 0-100 or None.
    Heuristic: only returns values between 10 and 80 (avoids matching
    irrelevant percentages elsewhere in the document).
    """
    if not text:
        return None
    for m in PCT_WOMEN_BOARD_PATTERN.finditer(text):
        try:
            pct = int(m.group(1))
            if 10 <= pct <= 80:
                return pct
        except (ValueError, IndexError):
            continue
    return None


def has_quantitative_target(esg_text: Optional[str]) -> bool:
    """Boolean: does the ESG section contain any quantitative target language?"""
    if not esg_text:
        return False
    matches = QUANTITATIVE_TARGET_PATTERN.findall(esg_text)
    # At least 3 matches to indicate genuine quantitative substance,
    # not just a single passing reference
    return len(matches) >= 3


def parse_proxy(html: str) -> dict:
    """
    Top-level parsing function.
    Returns a dict with the cleaned text, ESG section, and all NLP signals.
    """
    full_text     = html_to_text(html)
    esg_section   = find_esg_section(full_text)

    text_for_count = esg_section or full_text  # signals from ESG section if found

    return {
        "proxy_text_clean":        full_text,
        "esg_section_text":        esg_section,
        "esg_section_word_count":  len(esg_section.split()) if esg_section else 0,
        "has_explicit_esg_section":esg_section is not None,
        "total_word_count":        len(full_text.split()),
        # Classical-NLP signals (computed from ESG section if present, else whole doc)
        "climate_mention_count":   count_keyword_mentions(text_for_count, CLIMATE_KEYWORDS),
        "diversity_mention_count": count_keyword_mentions(text_for_count, DIVERSITY_KEYWORDS),
        "governance_mention_count":count_keyword_mentions(text_for_count, GOVERNANCE_KEYWORDS),
        "net_zero_target_year":    extract_net_zero_year(full_text),
        "pct_women_board":         extract_pct_women_board(full_text),
        "has_quantitative_targets":has_quantitative_target(esg_section),
    }
