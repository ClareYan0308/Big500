"""
extractor.py  --  Extract clean body text from archived HTML.

Two-stage pipeline:
  1. trafilatura  (ML-based main-content extraction, primary)
  2. BeautifulSoup fallback  (manual boilerplate stripping)

Both stages strip Wayback Machine toolbar elements first.
"""

import re
import unicodedata
from typing import Optional

import trafilatura
from bs4 import BeautifulSoup, Comment

# Wayback toolbar element selectors
_WB_SELECTORS = ["#wm-ipp-base", "#wm-ipp", "#donato", ".WBSearch",
                 "#playback", "#wm-toolbar", ".wb-autocomplete"]

# HTML tags that are always structural boilerplate
_STRIP_TAGS = {"script","style","noscript","iframe","svg","img",
               "nav","header","footer","aside","form","button"}

# Class/ID patterns that identify boilerplate regions
_BP_REGEX = re.compile(
    r"nav|footer|header|menu|cookie|banner|sidebar|breadcrumb|"
    r"pagination|social|share|search|newsletter|popup|modal|toolbar|"
    r"topbar|ribbon|flyout|overlay|skip-to",
    re.I,
)


def _strip_wayback(soup: BeautifulSoup) -> None:
    for sel in _WB_SELECTORS:
        for el in soup.select(sel):
            el.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "wayback" in str(comment).lower():
            comment.extract()


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    for tag in _STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()
    for el in soup.find_all(True):
        attrs = " ".join(
            v for k, v in el.attrs.items()
            if k in ("class", "id")
            for v in ([v] if isinstance(v, str) else v)
        ).lower()
        if _BP_REGEX.search(attrs):
            el.decompose()


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if len(ln) >= 4]
    deduped, prev = [], None
    for ln in lines:
        if ln != prev:
            deduped.append(ln)
        prev = ln
    return "\n".join(deduped).strip()


def extract(html: str) -> Optional[str]:
    """
    Return cleaned visible text, or None if < 30 words extracted.
    """
    if not html or len(html) < 200:
        return None

    # Stage 1: trafilatura
    traf = trafilatura.extract(
        html, include_comments=False, include_tables=True,
        no_fallback=False, favor_recall=False, deduplicate=True,
    )
    if traf and len(traf.split()) >= 40:
        return _clean(traf)

    # Stage 2: BeautifulSoup fallback
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    _strip_wayback(soup)
    _strip_boilerplate(soup)
    raw   = soup.get_text(separator="\n")
    clean = _clean(raw)
    return clean if len(clean.split()) >= 30 else None


def word_count(text: Optional[str]) -> int:
    return len(text.split()) if text else 0
