"""
companies.py  --  50-company universe for Part 1.

GICS sector assignments as of January 2024 (S&P 500).

Key corrections vs. naive groupings:
  * Alphabet (GOOGL) and Meta (META) -> Communication Services, NOT IT
  * Visa (V) and Mastercard (MA)     -> IT (Data Processing), NOT Financials
"""

YEARS = list(range(2016, 2025))   # 2016 ... 2024  (9 years)

COMPANIES = [
    # -- INFORMATION TECHNOLOGY ------------------------------------------------
    # Ranked by free-float market cap, S&P 500 GICS IT sector, 2024-01-02
    {"ticker":"AAPL","name":"Apple Inc.","sector":"Technology",
     "domain":"apple.com","url_hints":["/about/","/leadership/"]},
    {"ticker":"MSFT","name":"Microsoft Corporation","sector":"Technology",
     "domain":"microsoft.com","url_hints":["/en-us/about","/about"]},
    {"ticker":"NVDA","name":"NVIDIA Corporation","sector":"Technology",
     "domain":"nvidia.com","url_hints":["/en-us/about-nvidia/","/about/"]},
    {"ticker":"AVGO","name":"Broadcom Inc.","sector":"Technology",
     "domain":"broadcom.com","url_hints":["/company/about-broadcom","/about/"]},
    {"ticker":"ORCL","name":"Oracle Corporation","sector":"Technology",
     "domain":"oracle.com","url_hints":["/corporate/","/us/corporate/index.htm"]},
    {"ticker":"ADBE","name":"Adobe Inc.","sector":"Technology",
     "domain":"adobe.com","url_hints":["/about/","/about-adobe.html"]},
    {"ticker":"CRM","name":"Salesforce Inc.","sector":"Technology",
     "domain":"salesforce.com","url_hints":["/company/","/about/"]},
    {"ticker":"AMD","name":"Advanced Micro Devices Inc.","sector":"Technology",
     "domain":"amd.com","url_hints":["/en/corporate/about-amd.html","/about/"]},
    {"ticker":"ACN","name":"Accenture plc","sector":"Technology",
     "domain":"accenture.com","url_hints":["/us-en/about/company-index","/about/"]},
    {"ticker":"INTU","name":"Intuit Inc.","sector":"Technology",
     "domain":"intuit.com","url_hints":["/company/","/about/"]},

    # -- FINANCIALS ------------------------------------------------------------
    {"ticker":"BRK-B","name":"Berkshire Hathaway Inc.","sector":"Financials",
     "domain":"berkshirehathaway.com","url_hints":["/"]},
    {"ticker":"JPM","name":"JPMorgan Chase & Co.","sector":"Financials",
     "domain":"jpmorganchase.com","url_hints":["/about","/corporate/About-JPMC/about-jpmorgan-chase.htm"]},
    {"ticker":"BAC","name":"Bank of America Corporation","sector":"Financials",
     "domain":"bankofamerica.com","url_hints":["/about/","/about-bank-of-america/"]},
    {"ticker":"WFC","name":"Wells Fargo & Company","sector":"Financials",
     "domain":"wellsfargo.com","url_hints":["/about/","/about-us/"]},
    {"ticker":"AXP","name":"American Express Company","sector":"Financials",
     "domain":"americanexpress.com","url_hints":["/us/about-american-express/","/about-us/"]},
    {"ticker":"MS","name":"Morgan Stanley","sector":"Financials",
     "domain":"morganstanley.com","url_hints":["/about-us/","/about/"]},
    {"ticker":"GS","name":"The Goldman Sachs Group Inc.","sector":"Financials",
     "domain":"goldmansachs.com","url_hints":["/about-us/","/who-we-are/"]},
    {"ticker":"SPGI","name":"S&P Global Inc.","sector":"Financials",
     "domain":"spglobal.com","url_hints":["/en/about/","/about/"]},
    {"ticker":"BLK","name":"BlackRock Inc.","sector":"Financials",
     "domain":"blackrock.com","url_hints":["/corporate/about-us","/us/individual/about-blackrock"]},
    {"ticker":"C","name":"Citigroup Inc.","sector":"Financials",
     "domain":"citigroup.com","url_hints":["/about/","/about-citi/"]},

    # -- HEALTHCARE ------------------------------------------------------------
    {"ticker":"LLY","name":"Eli Lilly and Company","sector":"Healthcare",
     "domain":"lilly.com","url_hints":["/about-lilly","/about/"]},
    {"ticker":"UNH","name":"UnitedHealth Group Incorporated","sector":"Healthcare",
     "domain":"unitedhealthgroup.com","url_hints":["/about/","/who-we-are/"]},
    {"ticker":"JNJ","name":"Johnson & Johnson","sector":"Healthcare",
     "domain":"jnj.com","url_hints":["/about-jnj/","/about/"]},
    {"ticker":"ABBV","name":"AbbVie Inc.","sector":"Healthcare",
     "domain":"abbvie.com","url_hints":["/about-us.html","/about/"]},
    {"ticker":"MRK","name":"Merck & Co. Inc.","sector":"Healthcare",
     "domain":"merck.com","url_hints":["/about/","/en/about.html"]},
    {"ticker":"TMO","name":"Thermo Fisher Scientific Inc.","sector":"Healthcare",
     "domain":"thermofisher.com","url_hints":["/us/en/home/about-us.html","/about-us/"]},
    {"ticker":"ABT","name":"Abbott Laboratories","sector":"Healthcare",
     "domain":"abbott.com","url_hints":["/about-abbott.html","/about/"]},
    {"ticker":"DHR","name":"Danaher Corporation","sector":"Healthcare",
     "domain":"danaher.com","url_hints":["/about/","/our-company/"]},
    {"ticker":"PFE","name":"Pfizer Inc.","sector":"Healthcare",
     "domain":"pfizer.com","url_hints":["/about/","/about-pfizer/","/purpose/"]},
    {"ticker":"AMGN","name":"Amgen Inc.","sector":"Healthcare",
     "domain":"amgen.com","url_hints":["/about/","/about-amgen/"]},

    # -- CONSUMER DISCRETIONARY ------------------------------------------------
    {"ticker":"AMZN","name":"Amazon.com Inc.","sector":"Consumer Discretionary",
     "domain":"aboutamazon.com","url_hints":["/","/about-amazon"],
     "domain_alt":"amazon.com","url_hints_alt":["/about/"]},
    {"ticker":"TSLA","name":"Tesla Inc.","sector":"Consumer Discretionary",
     "domain":"tesla.com","url_hints":["/about/","/en_us/about/"]},
    {"ticker":"HD","name":"The Home Depot Inc.","sector":"Consumer Discretionary",
     "domain":"homedepot.com","url_hints":["/c/about-us","/corporate/"]},
    {"ticker":"MCD","name":"McDonald's Corporation","sector":"Consumer Discretionary",
     "domain":"corporate.mcdonalds.com","url_hints":["/corpmcd/about-us.html","/about-us/"],
     "domain_alt":"aboutmcdonalds.com","url_hints_alt":["/content/us/en-us/home.html","/"]},
    {"ticker":"NKE","name":"Nike Inc.","sector":"Consumer Discretionary",
     "domain":"nike.com","url_hints":["/a/about-nike","/us/en_us/c/about-nike"]},
    {"ticker":"LOW","name":"Lowe's Companies Inc.","sector":"Consumer Discretionary",
     "domain":"corporate.lowes.com","url_hints":["/about-lowes/"],
     "domain_alt":"lowes.com","url_hints_alt":["/l/about/"]},
    {"ticker":"BKNG","name":"Booking Holdings Inc.","sector":"Consumer Discretionary",
     "domain":"bookingholdings.com","url_hints":["/about/","/who-we-are/"]},
    {"ticker":"SBUX","name":"Starbucks Corporation","sector":"Consumer Discretionary",
     "domain":"starbucks.com","url_hints":["/about-us/","/responsibility/"]},
    {"ticker":"TJX","name":"The TJX Companies Inc.","sector":"Consumer Discretionary",
     "domain":"tjx.com","url_hints":["/about/","/our-company/"]},
    {"ticker":"ORLY","name":"O'Reilly Automotive Inc.","sector":"Consumer Discretionary",
     "domain":"oreillyauto.com","url_hints":["/about/","/corporate/"]},

    # -- ENERGY ----------------------------------------------------------------
    {"ticker":"XOM","name":"Exxon Mobil Corporation","sector":"Energy",
     "domain":"corporate.exxonmobil.com","url_hints":["/about-us","/"],
     "domain_alt":"exxonmobil.com","url_hints_alt":["/en/about-exxonmobil","/about/"]},
    {"ticker":"CVX","name":"Chevron Corporation","sector":"Energy",
     "domain":"chevron.com","url_hints":["/about-chevron","/about/"]},
    {"ticker":"COP","name":"ConocoPhillips","sector":"Energy",
     "domain":"conocophillips.com","url_hints":["/company/","/about/"]},
    {"ticker":"SLB","name":"SLB (Schlumberger)","sector":"Energy",
     "domain":"slb.com","url_hints":["/about/","/who-we-are/"],
     "domain_alt":"schlumberger.com","url_hints_alt":["/about/"]},
    {"ticker":"EOG","name":"EOG Resources Inc.","sector":"Energy",
     "domain":"eogresources.com","url_hints":["/company.html","/about/","/"]},
    {"ticker":"MPC","name":"Marathon Petroleum Corporation","sector":"Energy",
     "domain":"marathonpetroleum.com","url_hints":["/About/","/about/"]},
    {"ticker":"PSX","name":"Phillips 66","sector":"Energy",
     "domain":"phillips66.com","url_hints":["/about/","/who-we-are/"]},
    {"ticker":"OXY","name":"Occidental Petroleum Corporation","sector":"Energy",
     "domain":"oxy.com","url_hints":["/about/","/who-we-are/"]},
    {"ticker":"VLO","name":"Valero Energy Corporation","sector":"Energy",
     "domain":"valero.com","url_hints":["/about/","/about-valero/"]},
    {"ticker":"HES","name":"Hess Corporation","sector":"Energy",
     "domain":"hess.com","url_hints":["/about/","/company/about-hess"]},
]

COMPANIES_BY_TICKER = {c["ticker"]: c for c in COMPANIES}

SECTOR_COMPANIES = {}
for _c in COMPANIES:
    SECTOR_COMPANIES.setdefault(_c["sector"], []).append(_c)
