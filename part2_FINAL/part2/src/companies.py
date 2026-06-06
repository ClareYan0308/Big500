"""
companies.py -- 50-company universe for Part 2 (same as Part 1)

50 companies across 5 GICS sectors. Each entry includes the company's
ticker, name, GICS sector, and SEC CIK (Central Index Key).

CIKs were looked up against SEC's official company_tickers.json
(https://www.sec.gov/files/company_tickers.json). The CIK is the SEC's
permanent identifier and is used in all EDGAR URLs.

For tickers with dashes (BRK-B), we use the underlying company's CIK.
Berkshire Hathaway BRK-B and BRK-A share CIK 1067983.
"""

YEARS = list(range(2016, 2025))   # 2016 .. 2024  (9 years)

COMPANIES = [
    # ---- INFORMATION TECHNOLOGY ----
    {"ticker": "AAPL", "name": "Apple Inc.",                       "sector": "Technology",             "cik": "320193"},
    {"ticker": "MSFT", "name": "Microsoft Corporation",            "sector": "Technology",             "cik": "789019"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation",               "sector": "Technology",             "cik": "1045810"},
    {"ticker": "AVGO", "name": "Broadcom Inc.",                    "sector": "Technology",             "cik": "1730168"},
    {"ticker": "ORCL", "name": "Oracle Corporation",               "sector": "Technology",             "cik": "1341439"},
    {"ticker": "ADBE", "name": "Adobe Inc.",                       "sector": "Technology",             "cik": "796343"},
    {"ticker": "CRM",  "name": "Salesforce Inc.",                  "sector": "Technology",             "cik": "1108524"},
    {"ticker": "AMD",  "name": "Advanced Micro Devices Inc.",      "sector": "Technology",             "cik": "2488"},
    {"ticker": "ACN",  "name": "Accenture plc",                    "sector": "Technology",             "cik": "1467373"},
    {"ticker": "INTU", "name": "Intuit Inc.",                      "sector": "Technology",             "cik": "896878"},

    # ---- FINANCIALS ----
    {"ticker": "BRK-B","name": "Berkshire Hathaway Inc.",          "sector": "Financials",             "cik": "1067983"},
    {"ticker": "JPM",  "name": "JPMorgan Chase & Co.",             "sector": "Financials",             "cik": "19617"},
    {"ticker": "BAC",  "name": "Bank of America Corporation",      "sector": "Financials",             "cik": "70858"},
    {"ticker": "WFC",  "name": "Wells Fargo & Company",            "sector": "Financials",             "cik": "72971"},
    {"ticker": "AXP",  "name": "American Express Company",         "sector": "Financials",             "cik": "4962"},
    {"ticker": "MS",   "name": "Morgan Stanley",                   "sector": "Financials",             "cik": "895421"},
    {"ticker": "GS",   "name": "The Goldman Sachs Group Inc.",     "sector": "Financials",             "cik": "886982"},
    {"ticker": "SPGI", "name": "S&P Global Inc.",                  "sector": "Financials",             "cik": "64040"},
    {"ticker": "BLK",  "name": "BlackRock Inc.",                   "sector": "Financials",             "cik": "1364742"},
    {"ticker": "C",    "name": "Citigroup Inc.",                   "sector": "Financials",             "cik": "831001"},

    # ---- HEALTHCARE ----
    {"ticker": "LLY",  "name": "Eli Lilly and Company",            "sector": "Healthcare",             "cik": "59478"},
    {"ticker": "UNH",  "name": "UnitedHealth Group Incorporated",  "sector": "Healthcare",             "cik": "731766"},
    {"ticker": "JNJ",  "name": "Johnson & Johnson",                "sector": "Healthcare",             "cik": "200406"},
    {"ticker": "ABBV", "name": "AbbVie Inc.",                      "sector": "Healthcare",             "cik": "1551152"},
    {"ticker": "MRK",  "name": "Merck & Co. Inc.",                 "sector": "Healthcare",             "cik": "310158"},
    {"ticker": "TMO",  "name": "Thermo Fisher Scientific Inc.",    "sector": "Healthcare",             "cik": "97745"},
    {"ticker": "ABT",  "name": "Abbott Laboratories",              "sector": "Healthcare",             "cik": "1800"},
    {"ticker": "DHR",  "name": "Danaher Corporation",              "sector": "Healthcare",             "cik": "313616"},
    {"ticker": "PFE",  "name": "Pfizer Inc.",                      "sector": "Healthcare",             "cik": "78003"},
    {"ticker": "AMGN", "name": "Amgen Inc.",                       "sector": "Healthcare",             "cik": "318154"},

    # ---- CONSUMER DISCRETIONARY ----
    {"ticker": "AMZN", "name": "Amazon.com Inc.",                  "sector": "Consumer Discretionary", "cik": "1018724"},
    {"ticker": "TSLA", "name": "Tesla Inc.",                       "sector": "Consumer Discretionary", "cik": "1318605"},
    {"ticker": "HD",   "name": "The Home Depot Inc.",              "sector": "Consumer Discretionary", "cik": "354950"},
    {"ticker": "MCD",  "name": "McDonald's Corporation",           "sector": "Consumer Discretionary", "cik": "63908"},
    {"ticker": "NKE",  "name": "Nike Inc.",                        "sector": "Consumer Discretionary", "cik": "320187"},
    {"ticker": "LOW",  "name": "Lowe's Companies Inc.",            "sector": "Consumer Discretionary", "cik": "60667"},
    {"ticker": "BKNG", "name": "Booking Holdings Inc.",            "sector": "Consumer Discretionary", "cik": "1075531"},
    {"ticker": "SBUX", "name": "Starbucks Corporation",            "sector": "Consumer Discretionary", "cik": "829224"},
    {"ticker": "TJX",  "name": "The TJX Companies Inc.",           "sector": "Consumer Discretionary", "cik": "109198"},
    {"ticker": "ORLY", "name": "O'Reilly Automotive Inc.",         "sector": "Consumer Discretionary", "cik": "898173"},

    # ---- ENERGY ----
    {"ticker": "XOM",  "name": "Exxon Mobil Corporation",          "sector": "Energy",                 "cik": "34088"},
    {"ticker": "CVX",  "name": "Chevron Corporation",              "sector": "Energy",                 "cik": "93410"},
    {"ticker": "COP",  "name": "ConocoPhillips",                   "sector": "Energy",                 "cik": "1163165"},
    {"ticker": "SLB",  "name": "SLB (Schlumberger)",               "sector": "Energy",                 "cik": "87347"},
    {"ticker": "EOG",  "name": "EOG Resources Inc.",               "sector": "Energy",                 "cik": "821189"},
    {"ticker": "MPC",  "name": "Marathon Petroleum Corporation",   "sector": "Energy",                 "cik": "1510295"},
    {"ticker": "PSX",  "name": "Phillips 66",                      "sector": "Energy",                 "cik": "1534701"},
    {"ticker": "OXY",  "name": "Occidental Petroleum Corporation", "sector": "Energy",                 "cik": "797468"},
    {"ticker": "VLO",  "name": "Valero Energy Corporation",        "sector": "Energy",                 "cik": "1035002"},
    {"ticker": "HES",  "name": "Hess Corporation",                 "sector": "Energy",                 "cik": "4447"},
]

COMPANIES_BY_TICKER = {c["ticker"]: c for c in COMPANIES}
COMPANIES_BY_CIK    = {c["cik"]: c for c in COMPANIES}

SECTOR_COMPANIES = {}
for _c in COMPANIES:
    SECTOR_COMPANIES.setdefault(_c["sector"], []).append(_c)
