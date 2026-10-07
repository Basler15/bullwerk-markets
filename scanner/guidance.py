# Bullwerk Markets - Guidance Modul
# Basierend auf der getesteten Guidance V7 Gegenprobe

import json
import re
import urllib.request
from html import unescape


USER_AGENT = (
    "Bullwerk Markets "
    "contact: bullwerkmarkets@gmail.com"
)


# ============================================================
# HTTP
# ============================================================

def request_bytes(url, accept="*/*"):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=30,
    ) as response:
        return response.read()


def get_json(url):
    return json.loads(
        request_bytes(
            url,
            "application/json",
        ).decode(
            "utf-8",
            errors="replace",
        )
    )


def get_text(url):
    return request_bytes(
        url,
        "text/html,*/*",
    ).decode(
        "utf-8",
        errors="replace",
    )


# ============================================================
# HTML -> TEXT
# ============================================================

def html_to_text(html):
    html = re.sub(
        r"(?is)<script.*?>.*?</script>",
        " ",
        html,
    )

    html = re.sub(
        r"(?is)<style.*?>.*?</style>",
        " ",
        html,
    )

    html = re.sub(
        r"(?i)<br\s*/?>",
        ". ",
        html,
    )

    html = re.sub(
        r"(?i)</(?:p|div|tr|li|h1|h2|h3)>",
        ". ",
        html,
    )

    html = re.sub(
        r"(?is)<[^>]+>",
        " ",
        html,
    )

    text = unescape(html)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# SEC SUBMISSIONS
# ============================================================

def load_submissions(cik):
    return get_json(
        "https://data.sec.gov/submissions/"
        f"CIK{cik}.json"
    )


# ============================================================
# EARNINGS 8-Ks
# ============================================================

def latest_earnings_filings(data, limit=2):
    recent = (
        data.get("filings", {})
        .get("recent", {})
    )

    accessions = recent.get(
        "accessionNumber",
        [],
    )

    dates = recent.get(
        "filingDate",
        [],
    )

    report_dates = recent.get(
        "reportDate",
        [],
    )

    forms = recent.get(
        "form",
        [],
    )

    items = recent.get(
        "items",
        [],
    )

    documents = recent.get(
        "primaryDocument",
        [],
    )

    result = []

    for i in range(len(accessions)):
        form = (
            forms[i]
            if i < len(forms)
            else ""
        )

        filing_items = (
            items[i]
            if i < len(items)
            else ""
        )

        if (
            form in ("8-K", "8-K/A")
            and "2.02" in filing_items
        ):
            result.append({
                "accession": accessions[i],
                "filing_date": dates[i],
                "report_date": (
                    report_dates[i]
                    if i < len(report_dates)
                    else ""
                ),
                "items": filing_items,
                "primary_document": documents[i],
            })

            if len(result) >= limit:
                break

    return result


# ============================================================
# SEC ARCHIVE
# ============================================================

def archive_base(cik, accession):
    cik_number = str(int(cik))

    accession_clean = accession.replace(
        "-",
        "",
    )

    return (
        "https://www.sec.gov/"
        "Archives/edgar/data/"
        f"{cik_number}/"
        f"{accession_clean}/"
    )


def load_filing_index(cik, accession):
    base = archive_base(
        cik,
        accession,
    )

    index = get_json(
        base + "index.json"
    )

    return base, index


# ============================================================
# DOKUMENTAUSWAHL
# ============================================================

def get_html_files(index_data):
    items = (
        index_data
        .get("directory", {})
        .get("item", [])
    )

    return [
        item.get("name", "")
        for item in items
        if item.get(
            "name",
            "",
        ).lower().endswith(
            (".htm", ".html")
        )
    ]


def document_priority(name):
    lower = name.lower()
    score = 0

    if "cfocommentary" in lower:
        score += 300

    if (
        "cfo" in lower
        and "commentary" in lower
    ):
        score += 250

    if "earningscommentary" in lower:
        score += 240

    if "financialcommentary" in lower:
        score += 230

    if "outlook" in lower:
        score += 220

    if "ex99" in lower:
        score += 195

    if "exhibit99" in lower:
        score += 195

    if (
        "99-1" in lower
        or "99_1" in lower
        or "99.1" in lower
    ):
        score += 190

    if "earn" in lower:
        score += 60

    if "release" in lower:
        score += 50

    if "results" in lower:
        score += 40

    if "index" in lower:
        score -= 200

    if "header" in lower:
        score -= 200

    return score


def should_scan(name, primary_document):
    lower = name.lower()

    if (
        "index" in lower
        or "header" in lower
    ):
        return False

    if name.lower() == (
        primary_document or ""
    ).lower():
        return False

    return document_priority(name) >= 40


# ============================================================
# GUIDANCE REGION
# ============================================================

GUIDANCE_ANCHORS = [
    r"\boutlook for the first quarter\b",
    r"\boutlook for the second quarter\b",
    r"\boutlook for the third quarter\b",
    r"\boutlook for the fourth quarter\b",

    r"\boutlook for q1\b",
    r"\boutlook for q2\b",
    r"\boutlook for q3\b",
    r"\boutlook for q4\b",

    r"\bquarterly outlook\b",

    r"\bguidance for the first quarter\b",
    r"\bguidance for the second quarter\b",
    r"\bguidance for the third quarter\b",
    r"\bguidance for the fourth quarter\b",

    r"\bfull[- ]year outlook\b",
    r"\bfull[- ]year guidance\b",

    r"\bfinancial outlook\b",
    r"\bbusiness outlook\b",
]


def find_guidance_region(text):
    positions = []

    for pattern in GUIDANCE_ANCHORS:
        match = re.search(
            pattern,
            text,
            flags=re.I,
        )

        if match:
            positions.append(
                match.start()
            )

    if not positions:
        return None

    start = min(positions)

    return text[
        start:
        min(
            len(text),
            start + 6000,
        )
    ]


# ============================================================
# GUIDANCE EXTRAKTION
# ============================================================

def number(value):
    return float(
        value.replace(",", "")
    )


def extract_guidance(text):
    if not text:
        return {}

    result = {}

    revenue = re.search(
        r"revenue.{0,120}?"
        r"(?:expected|expect|approximately|about)"
        r".{0,100}?"
        r"\$\s*([\d,.]+)"
        r"\s*(billion|million)",
        text,
        flags=re.I,
    )

    if revenue:
        value = number(
            revenue.group(1)
        )

        unit = (
            revenue.group(2)
            .lower()
        )

        if unit == "million":
            value /= 1000

        result[
            "revenue_billions"
        ] = value

    revenue_range = re.search(
        r"revenue.{0,150}?"
        r"\$\s*([\d,.]+)"
        r"\s*(?:billion|million)?"
        r".{0,40}?"
        r"(?:to|-|and)"
        r".{0,40}?"
        r"\$?\s*([\d,.]+)"
        r"\s*(billion|million)",
        text,
        flags=re.I,
    )

    if revenue_range:
        low = number(
            revenue_range.group(1)
        )

        high = number(
            revenue_range.group(2)
        )

        unit = (
            revenue_range.group(3)
            .lower()
        )

        if unit == "million":
            low /= 1000
            high /= 1000

        result[
            "revenue_low_billions"
        ] = low

        result[
            "revenue_high_billions"
        ] = high

        result[
            "revenue_mid_billions"
        ] = (
            low + high
        ) / 2

    margin = re.search(
        r"gross margins?"
        r".{0,120}?"
        r"(?:expected|expect|approximately|about)"
        r".{0,100}?"
        r"([\d.]+)\s*%",
        text,
        flags=re.I,
    )

    if margin:
        result[
            "gross_margin_pct"
        ] = float(
            margin.group(1)
        )

    opex = re.search(
        r"operating expenses?"
        r".{0,120}?"
        r"(?:expected|expect|approximately|about)"
        r".{0,120}?"
        r"\$\s*([\d,.]+)"
        r"\s*(billion|million)",
        text,
        flags=re.I,
    )

    if opex:
        value = number(
            opex.group(1)
        )

        unit = (
            opex.group(2)
            .lower()
        )

        if unit == "million":
            value /= 1000

        result[
            "operating_expenses_billions"
        ] = value

    return result


# ============================================================
# GUIDANCE AUS FILING
# ============================================================

def extract_from_filing(cik, filing):
    base, index_data = load_filing_index(
        cik,
        filing["accession"],
    )

    files = get_html_files(
        index_data
    )

    files.sort(
        key=document_priority,
        reverse=True,
    )

    for name in files[:15]:
        if not should_scan(
            name,
            filing["primary_document"],
        ):
            continue

        try:
            html = get_text(
                base + name
            )
        except Exception:
            continue

        text = html_to_text(html)

        region = find_guidance_region(
            text
        )

        if not region:
            continue

        guidance = extract_guidance(
            region
        )

        if guidance:
            return {
                "filing_date":
                    filing["filing_date"],
                "document":
                    name,
                "guidance":
                    guidance,
            }

    return None


# ============================================================
# V7 BEWERTUNG
# ============================================================

def percent_change(current, previous):
    if previous == 0:
        return None

    return (
        (current - previous)
        / abs(previous)
        * 100
    )


def compare_v7(current, previous):
    if not current or not previous:
        return {
            "score": None,
            "status": "N/A",
            "reason":
                "Aktuelle oder vorherige Guidance fehlt.",
            "details": [],
        }

    cg = current["guidance"]
    pg = previous["guidance"]

    details = []

    current_revenue = (
        cg.get("revenue_mid_billions")
        or cg.get("revenue_billions")
    )

    previous_revenue = (
        pg.get("revenue_mid_billions")
        or pg.get("revenue_billions")
    )

    if (
        current_revenue is None
        or previous_revenue is None
    ):
        return {
            "score": None,
            "status": "N/A",
            "reason":
                "Keine direkt vergleichbare Umsatz-Guidance gefunden.",
            "details": details,
        }

    revenue_change = percent_change(
        current_revenue,
        previous_revenue,
    )

    if revenue_change >= 10:
        revenue_points = 3
    elif revenue_change >= 5:
        revenue_points = 2
    elif revenue_change >= 1:
        revenue_points = 1
    elif revenue_change > -1:
        revenue_points = 0
    elif revenue_change > -5:
        revenue_points = -1
    elif revenue_change > -10:
        revenue_points = -2
    else:
        revenue_points = -3

    details.append({
        "metric": "Revenue",
        "previous": previous_revenue,
        "current": current_revenue,
        "change": revenue_change,
        "raw_points": revenue_points,
    })

    margin_change = None
    margin_points = 0

    if (
        "gross_margin_pct" in cg
        and "gross_margin_pct" in pg
    ):
        current_margin = cg[
            "gross_margin_pct"
        ]

        previous_margin = pg[
            "gross_margin_pct"
        ]

        margin_change = (
            current_margin
            - previous_margin
        )

        if margin_change >= 1.0:
            margin_points = 2
        elif margin_change >= 0.25:
            margin_points = 1
        elif margin_change > -0.25:
            margin_points = 0
        elif margin_change > -1.0:
            margin_points = -1
        else:
            margin_points = -2

        details.append({
            "metric": "Gross Margin",
            "previous": previous_margin,
            "current": current_margin,
            "change": margin_change,
            "raw_points": margin_points,
        })

    if (
        "operating_expenses_billions" in cg
        and "operating_expenses_billions" in pg
    ):
        current_opex = cg[
            "operating_expenses_billions"
        ]

        previous_opex = pg[
            "operating_expenses_billions"
        ]

        details.append({
            "metric": "Operating Expenses",
            "previous": previous_opex,
            "current": current_opex,
            "change": percent_change(
                current_opex,
                previous_opex,
            ),
            "raw_points": None,
        })

    raw_score = (
        revenue_points
        + margin_points
    )

    if (
        revenue_change >= 10
        and (
            margin_change is None
            or margin_change > -1.0
        )
    ):
        score = 3
        status = "STRONG_IMPROVEMENT"
        reason = (
            "Umsatz-Guidance steigt stark; "
            "Margen-Gegenwind ist nicht dominant."
        )

    elif (
        revenue_change >= 10
        and margin_change is not None
        and margin_change <= -1.0
    ):
        score = 2
        status = (
            "POSITIVE_WITH_MARGIN_PRESSURE"
        )
        reason = (
            "Umsatz-Guidance steigt stark, "
            "aber der Margendruck ist deutlich."
        )

    elif raw_score >= 2:
        score = 3
        status = "IMPROVED"
        reason = (
            "Guidance verbessert sich."
        )

    elif raw_score >= 0:
        score = 2
        status = "STABLE_TO_POSITIVE"
        reason = (
            "Guidance ist insgesamt stabil bis positiv."
        )

    elif raw_score >= -2:
        score = 1
        status = "CAUTIOUS"
        reason = (
            "Guidance zeigt leichten bis moderaten Gegenwind."
        )

    else:
        score = 0
        status = "WEAKER"
        reason = (
            "Guidance hat sich deutlich verschlechtert."
        )

    return {
        "score": score,
        "status": status,
        "reason": reason,
        "raw_score": raw_score,
        "details": details,
    }


# ============================================================
# ÖFFENTLICHE MODULFUNKTION
# ============================================================

def get_guidance_data(cik):
    """
    Hauptfunktion für den Bullwerk-Scanner.

    Lädt die beiden jüngsten Earnings-8-Ks,
    extrahiert die Guidance und wendet die
    getestete V7-Bewertung an.
    """

    submissions = load_submissions(
        cik
    )

    filings = latest_earnings_filings(
        submissions,
        2,
    )

    if len(filings) < 2:
        return {
            "score": None,
            "status": "N/A",
            "reason":
                "Weniger als zwei vergleichbare Earnings-Filings.",
            "details": [],
        }

    current = extract_from_filing(
        cik,
        filings[0],
    )

    previous = extract_from_filing(
        cik,
        filings[1],
    )

    result = compare_v7(
        current,
        previous,
    )

    result["current_guidance"] = current
    result["previous_guidance"] = previous

    return result
