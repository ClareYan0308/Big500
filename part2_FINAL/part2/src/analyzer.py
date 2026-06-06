"""
analyzer.py -- LLM-based analysis of proxy statement ESG sections.

Model: claude-sonnet-4-20250514 via Anthropic Messages API.

For each proxy filing, we send the ESG section (or first 8000 chars of the
full proxy if no explicit ESG section was found) and ask Claude to extract
structured information.

Why LLM here (not just classical NLP):
  Classical NLP (in proxy_parser.py) gives us cheap, reproducible counts of
  ESG/diversity/governance keywords. But many of the interesting questions
  cannot be answered by counting: Does the company name a specific climate
  target? Is its DEI disclosure specific or vague? Did the ESG framing
  change from last year? These require reading comprehension that bag-of-
  words cannot provide. We combine both: keyword counts for the
  quantitative signal, LLM for the interpretive judgement.

Returned JSON schema:
  esg_themes              list of theme strings (subset of THEMES)
  climate_commitment      verbatim quote of the climate commitment, or null
  dei_disclosure_quality  "LOW" | "MEDIUM" | "HIGH"
  changed_from_prior      true | false | null
  change_confidence       "HIGH" | "MEDIUM" | "LOW" | null
  change_summary          1-2 sentence summary of what changed
  register                "FORMAL" | "ASPIRATIONAL" | "TECHNICAL" | "COMPLIANCE"
  analyst_notes           2-3 sentences on what is strategically notable
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional
from collections import Counter

log = logging.getLogger("analyzer")

# ---- Theme taxonomy adapted for proxy ESG context ----
THEMES = [
    "CLIMATE_RISK",          # Climate change as risk to the business
    "CLIMATE_OPPORTUNITY",   # Climate transition as business opportunity
    "EMISSIONS_TARGETS",     # Specific GHG / net-zero / carbon targets
    "BOARD_DIVERSITY",       # Board composition diversity disclosure
    "WORKFORCE_DEI",         # Workforce DEI programs and metrics
    "HUMAN_CAPITAL",         # Talent, retention, training, wellbeing
    "ESG_OVERSIGHT",         # Board / committee structures for ESG
    "STAKEHOLDER_ENGAGEMENT",# Stakeholder consultation language
    "EXEC_COMP_LINKAGE",     # Executive comp tied to ESG metrics
    "SUPPLY_CHAIN",          # Supply-chain sustainability / human rights
    "POLITICAL_LOBBYING",    # Political contributions / lobbying disclosure
    "RISK_DISCLOSURE",       # ESG-related risk factors / TCFD framing
]

_SYSTEM = (
    "You are a corporate governance analyst. You analyze SEC DEF 14A proxy "
    "statements, focusing on ESG (environmental, social, governance) disclosures. "
    "Return ONLY valid JSON -- no prose, no markdown fences."
)

_PROMPT = """\
Analyze this DEF 14A proxy statement excerpt focused on ESG content.

Company: {name} ({ticker}) | Sector: {sector} | Filing year: {year}

CURRENT TEXT ({year}):
{current}

PRIOR YEAR TEXT ({prior_year}):
{prior}

Return JSON with EXACTLY these keys:
{{
  "esg_themes": [<theme strings from allowed list>],
  "climate_commitment": "<verbatim climate target quote OR null>",
  "dei_disclosure_quality": "LOW" | "MEDIUM" | "HIGH",
  "changed_from_prior": true | false | null,
  "change_confidence": "HIGH" | "MEDIUM" | "LOW" | null,
  "change_summary": "<1-2 sentences OR 'No material change' OR 'No prior year available'>",
  "register": "FORMAL" | "ASPIRATIONAL" | "TECHNICAL" | "COMPLIANCE",
  "analyst_notes": "<2-3 sentences on what is strategically notable>"
}}

Allowed esg_themes values (use exact strings):
{themes}

Rules:
- dei_disclosure_quality:
    LOW    = vague boilerplate, no specific programs or metrics
    MEDIUM = named programs but few quantitative metrics
    HIGH   = specific programs AND quantitative metrics (% women, % minority, etc.)
- climate_commitment: extract verbatim phrase like "net-zero emissions by 2050"
  or "reduce Scope 1+2 emissions 50% by 2030"; null if no specific commitment.
- changed_from_prior = null when no prior text is provided.
- analyst_notes should surface what is actionable or analytically interesting
  (emphasis, pivot, missing topics, new commitments, retracted commitments).
"""


# Keyword fallback (used when LLM API fails)
_KW_FALLBACK = {
    "CLIMATE_RISK":         ["climate risk", "climate-related risk", "transition risk"],
    "CLIMATE_OPPORTUNITY":  ["clean energy", "renewable", "low-carbon opportunity"],
    "EMISSIONS_TARGETS":    ["net zero", "net-zero", "carbon neutral", "scope 1", "scope 2"],
    "BOARD_DIVERSITY":      ["board diversity", "diverse directors", "% women on", "women director"],
    "WORKFORCE_DEI":        ["workforce diversity", "diversity, equity", "dei", "inclusion"],
    "HUMAN_CAPITAL":        ["human capital", "talent", "employee engagement"],
    "ESG_OVERSIGHT":        ["esg committee", "sustainability committee", "esg oversight"],
    "STAKEHOLDER_ENGAGEMENT":["stakeholder engagement", "investor outreach"],
    "EXEC_COMP_LINKAGE":    ["esg metrics in compensation", "esg-linked", "sustainability-linked"],
    "SUPPLY_CHAIN":         ["supply chain", "supplier code", "human rights"],
    "POLITICAL_LOBBYING":   ["political contribution", "lobbying"],
    "RISK_DISCLOSURE":      ["tcfd", "task force on climate", "climate-related risk"],
}


def ngram_sim(a: Optional[str], b: Optional[str], n: int = 3) -> Optional[float]:
    """Jaccard similarity on character n-grams. Returns None if either input is empty."""
    if not a or not b:
        return None
    def ng(t: str) -> Counter:
        t = t.lower()
        return Counter(t[i:i+n] for i in range(len(t) - n + 1))
    ca, cb = ng(a), ng(b)
    inter = sum(min(ca[k], cb[k]) for k in ca if k in cb)
    union = sum(ca.values()) + sum(cb.values()) - inter
    return round(inter / union, 4) if union else 0.0


def _trunc(text: Optional[str], max_chars: int = 8000) -> str:
    """Truncate text at the last sentence boundary within max_chars."""
    if not text:
        return "NOT AVAILABLE"
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last = max(cut.rfind(". "), cut.rfind("\n"))
    return (cut[:last + 1] if last > int(max_chars * 0.7) else cut) + " ... [truncated]"


def _keyword_fallback(ticker: str, year: int, current: str,
                      prior: Optional[str], sim: Optional[float]) -> dict:
    """Best-effort analysis when the LLM call fails."""
    text_low = current.lower() if current else ""
    found = [theme for theme, kws in _KW_FALLBACK.items()
             if any(kw in text_low for kw in kws)]
    return {
        "ticker": ticker, "year": year,
        "esg_themes": found,
        "climate_commitment": None,
        "dei_disclosure_quality": "LOW",
        "changed_from_prior": (sim is not None and sim < 0.85),
        "change_confidence": "LOW",
        "change_summary": f"Keyword fallback (ngram_sim={sim})",
        "register": "FORMAL",
        "analyst_notes": "LLM unavailable -- keyword heuristic used.",
        "ngram_similarity": sim,
        "analysis_method": "keyword_fallback",
    }


def analyze_one(company: dict, year: int, current: str,
                prior: Optional[str], client, retries: int = 3) -> dict:
    """
    Analyze a single proxy ESG section with the LLM.
    Falls back to keyword heuristic if the API fails.
    """
    ticker = company["ticker"]
    sim    = ngram_sim(current, prior)

    prompt = _PROMPT.format(
        name=company["name"], ticker=ticker, sector=company["sector"], year=year,
        current=_trunc(current, 8000),
        prior_year=year - 1, prior=_trunc(prior, 4000),
        themes=", ".join(THEMES),
    )

    for attempt in range(retries):
        try:
            time.sleep(0.5)
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
            data = json.loads(raw)
            data.update(
                ticker=ticker, year=year,
                ngram_similarity=sim, analysis_method="llm",
            )
            return data

        except json.JSONDecodeError as e:
            log.warning("[%s %d] JSON parse error (attempt %d): %s", ticker, year, attempt + 1, e)
        except Exception as e:
            msg = str(e)
            if "rate_limit" in msg.lower() or "529" in msg:
                wait = 60 * (attempt + 1)
                log.warning("[%s %d] Rate limit; sleeping %ds", ticker, year, wait)
                time.sleep(wait)
            else:
                log.warning("[%s %d] API error (attempt %d): %s", ticker, year, attempt + 1, msg[:120])
                time.sleep(5 * (attempt + 1))

    log.error("[%s %d] All attempts failed -- keyword fallback", ticker, year)
    return _keyword_fallback(ticker, year, current, prior, sim)


def run_all(parsed_records: list, companies_by_ticker: dict,
            analysis_dir: Path, resume: bool = True) -> list:
    """
    Run LLM analysis on all parsed records that have ESG text.
    Skips records with no text (saves a placeholder analysis row).
    """
    import anthropic
    from tqdm import tqdm

    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        log.error("ANTHROPIC_API_KEY is not set. Add it to .env before running.")
        raise SystemExit(1)

    client = anthropic.Anthropic(api_key=key)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Build lookup of {ticker: {year: esg_or_full_text}}
    text_lut: dict = {}
    for r in parsed_records:
        text = r.get("esg_section_text") or r.get("proxy_text_clean") or ""
        text_lut.setdefault(r["ticker"], {})[r["year"]] = text if len(text) >= 200 else None

    results = []
    for rec in tqdm(parsed_records, desc="Analysing", unit="filing"):
        ticker, year = rec["ticker"], rec["year"]
        out_path = analysis_dir / f"{ticker}_{year}.json"
        if resume and out_path.exists():
            results.append(json.loads(out_path.read_text()))
            continue

        current = text_lut.get(ticker, {}).get(year)
        prior   = text_lut.get(ticker, {}).get(year - 1)

        if not current:
            data = {
                "ticker": ticker, "year": year,
                "esg_themes": [], "climate_commitment": None,
                "dei_disclosure_quality": None,
                "changed_from_prior": None, "change_confidence": None,
                "change_summary": "No proxy text available", "register": None,
                "analyst_notes": "No proxy text; analysis skipped.",
                "ngram_similarity": None, "analysis_method": "skipped",
            }
        else:
            company = companies_by_ticker.get(
                ticker, {"ticker": ticker, "name": ticker, "sector": "Unknown"})
            data = analyze_one(company, year, current, prior, client)

        out_path.write_text(json.dumps(data, indent=2))
        results.append(data)

    return results
