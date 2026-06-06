"""
analyzer.py  --  LLM-based analysis of About-page snapshots.

Model  :  claude-sonnet-4-20250514  (via Anthropic Messages API)
Key    :  read from ANTHROPIC_API_KEY environment variable

For each snapshot the model returns JSON with:
  changed_from_prior   bool | null
  change_confidence    HIGH | MEDIUM | LOW | null
  change_description   str
  theme_categories     list[str]   (subset of THEMES below)
  theme_evidence       dict        {theme: "verbatim phrase <=8 words"}
  dominant_theme       str
  register             ASPIRATIONAL | FORMAL | TECHNICAL | CONVERSATIONAL
  analyst_notes        str  (2-3 sentences; what is strategically notable)
"""

import json
import logging
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Optional

log = logging.getLogger("analyzer")

THEMES = [
    "MISSION_PURPOSE",        # explicit reason-for-being language
    "CUSTOMER_CENTRICITY",    # customer satisfaction as primary value
    "INNOVATION_TECHNOLOGY",  # R&D, AI, digital transformation
    "STAKEHOLDER_CAPITALISM", # multiple-stakeholder obligations (post-BRT 2019)
    "SHAREHOLDER_VALUE",      # shareholder returns as primary goal
    "ESG_SUSTAINABILITY",     # climate, DEI, net-zero, governance
    "EMPLOYEE_CULTURE",       # workplace culture, belonging, talent
    "ETHICS_INTEGRITY",       # trust, transparency, compliance
    "GLOBAL_SCALE",           # international reach / worldwide operations
    "COMMUNITY_IMPACT",       # philanthropy, local/social investment
]

_SYSTEM = (
    "You are a corporate communications analyst. "
    "Analyse About Us / mission / values pages from large public companies. "
    "Return ONLY valid JSON -- no prose, no markdown fences."
)

_PROMPT = """\
Analyse this corporate About Us / mission / values page snapshot.

Company : {name} ({ticker}) | Sector : {sector} | Year : {year}

CURRENT TEXT ({year}):
{current}

PRIOR YEAR TEXT ({prior_year}):
{prior}

Return this exact JSON structure (no extra keys):
{{
  "changed_from_prior"  : true | false | null,
  "change_confidence"   : "HIGH" | "MEDIUM" | "LOW" | null,
  "change_description"  : "<1-2 sentences: what changed, or 'No material change', or 'No prior year available'>",
  "theme_categories"    : ["<THEME>", ...],
  "theme_evidence"      : {{"<THEME>": "<verbatim phrase <=8 words>", ...}},
  "dominant_theme"      : "<single most prominent theme>",
  "register"            : "ASPIRATIONAL" | "FORMAL" | "TECHNICAL" | "CONVERSATIONAL",
  "analyst_notes"       : "<2-3 sentences: what is strategically notable about this page>"
}}

Allowed themes (use exact strings only):
{themes}

Rules:
- changed_from_prior=null when no prior text is available
- theme_categories must be a subset of the allowed list
- analyst_notes should surface emphasis, omissions, pivots, or values-washing risk
"""

# Keyword fallback (used when API is unavailable)
_KEYWORDS = {
    "MISSION_PURPOSE":        ["mission","purpose","why we exist","reason for being"],
    "CUSTOMER_CENTRICITY":    ["customer","client","user experience"],
    "INNOVATION_TECHNOLOGY":  ["innovat","technolog","digital","artificial intelligence"," ai "],
    "STAKEHOLDER_CAPITALISM": ["stakeholder","society","all people","employees and"],
    "SHAREHOLDER_VALUE":      ["shareholder return","financial performance","earnings"],
    "ESG_SUSTAINABILITY":     ["sustainab","environmental","climate","net zero","esg","diversity"],
    "EMPLOYEE_CULTURE":       ["employee","talent","culture","belonging","team member"],
    "ETHICS_INTEGRITY":       ["integrit","ethics","transparenc","trust","accountability"],
    "GLOBAL_SCALE":           ["global","worldwide","international","countries"],
    "COMMUNITY_IMPACT":       ["community","philanthrop","social impact","giving"],
}


def ngram_sim(a: Optional[str], b: Optional[str], n: int = 3) -> Optional[float]:
    if not a or not b:
        return None
    def ng(t):
        t = t.lower()
        return Counter(t[i:i+n] for i in range(len(t)-n+1))
    ca, cb = ng(a), ng(b)
    inter = sum(min(ca[k], cb[k]) for k in ca if k in cb)
    union = sum(ca.values()) + sum(cb.values()) - inter
    return round(inter/union, 4) if union else 0.0


def _trunc(text: Optional[str], max_c: int = 4000) -> str:
    if not text:
        return "NOT AVAILABLE"
    if len(text) <= max_c:
        return text
    cut  = text[:max_c]
    last = max(cut.rfind(". "), cut.rfind("\n"))
    return (cut[:last+1] if last > int(max_c*0.7) else cut) + " ... [truncated]"


def _keyword_fallback(ticker, year, text, prior, sim):
    tl     = text.lower()
    found  = [t for t, kws in _KEYWORDS.items() if any(k in tl for k in kws)]
    return {
        "ticker": ticker, "year": year,
        "changed_from_prior": (sim is not None and sim < 0.85),
        "change_confidence":  "LOW",
        "change_description": f"Keyword fallback (ngram_sim={sim})" if sim else "No prior",
        "theme_categories": found, "theme_evidence": {},
        "dominant_theme": found[0] if found else None,
        "register": "FORMAL",
        "analyst_notes": "LLM unavailable -- keyword heuristic used.",
        "ngram_similarity": sim, "analysis_method": "keyword_fallback",
    }


def analyse_one(company: dict, year: int,
                current: str, prior: Optional[str],
                client, retries: int = 3) -> dict:
    ticker = company["ticker"]
    sim    = ngram_sim(current, prior)

    prompt = _PROMPT.format(
        name=company["name"], ticker=ticker, sector=company["sector"], year=year,
        current=_trunc(current, 4000),
        prior_year=year-1, prior=_trunc(prior, 3000),
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
            an  = json.loads(raw)
            an.update(ticker=ticker, year=year,
                      ngram_similarity=sim, analysis_method="llm")
            return an

        except json.JSONDecodeError as e:
            log.warning("[%s %d] JSON parse error (attempt %d): %s", ticker, year, attempt+1, e)
        except Exception as e:
            msg = str(e)
            if "rate_limit" in msg.lower() or "529" in msg:
                wait = 60 * (attempt+1)
                log.warning("[%s %d] Rate limit -- sleeping %ds", ticker, year, wait)
                time.sleep(wait)
            else:
                log.warning("[%s %d] API error (attempt %d): %s", ticker, year, attempt+1, msg[:120])
                time.sleep(5 * (attempt+1))

    log.error("[%s %d] All attempts failed -- keyword fallback", ticker, year)
    return _keyword_fallback(ticker, year, current, prior, sim)


def run_all(clean_records: list, companies_by_ticker: dict,
            analysis_dir: Path, resume: bool = True) -> list:
    """Run LLM analysis over all records that have page text."""
    import anthropic as ant_sdk

    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        log.error("ANTHROPIC_API_KEY is not set. "
                  "Add it to .env or export it before running.")
        raise SystemExit(1)

    client = ant_sdk.Anthropic(api_key=key)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Build text lookup {ticker: {year: text}}
    text_lut: dict = {}
    for r in clean_records:
        text_lut.setdefault(r["ticker"], {})[r["year"]] = r.get("page_text_clean")

    from tqdm import tqdm
    results = []

    with tqdm(clean_records, desc="Analysing", unit="record") as bar:
        for rec in bar:
            ticker, year = rec["ticker"], rec["year"]
            bar.set_postfix(company=ticker, year=year)
            out_path = analysis_dir / f"{ticker}_{year}.json"

            if resume and out_path.exists():
                results.append(json.loads(out_path.read_text()))
                continue

            current = text_lut.get(ticker, {}).get(year)
            prior   = text_lut.get(ticker, {}).get(year - 1)

            if not current:
                an = {
                    "ticker": ticker, "year": year,
                    "changed_from_prior": None, "change_confidence": None,
                    "change_description": "No text -- snapshot missing or blocked.",
                    "theme_categories": [], "theme_evidence": {},
                    "dominant_theme": None, "register": None,
                    "analyst_notes": "No text; analysis skipped.",
                    "ngram_similarity": None, "analysis_method": "skipped",
                }
            else:
                company = companies_by_ticker.get(
                    ticker, {"ticker": ticker, "name": ticker, "sector": "Unknown"})
                an = analyse_one(company, year, current, prior, client)

            out_path.write_text(json.dumps(an, indent=2))
            results.append(an)

    return results
