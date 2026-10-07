# Bullwerk Markets - Orders / Backlog Modul
# Basierend auf der getesteten V6-Logik

import json
import re
import urllib.request
from html import unescape


USER_AGENT = (
    "Bullwerk Markets "
    "contact: bullwerkmarkets@gmail.com"
)

METRICS = {
    "RPO": [
        "remaining performance obligations",
        "remaining performance obligation",
    ],
    "BACKLOG": [
        "order backlog",
        "contracted backlog",
        "backlog",
    ],
    "BOOKINGS": [
        "bookings",
    ],
}

MAX_POSITIVE_JUMP = 75.0
MAX_NEGATIVE_JUMP = -50.0


# ============================================================
# HTTP
# ============================================================

def get_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return json.loads(
            response.read().decode(
                "utf-8",
                errors="replace",
            )
        )


# ============================================================
# HTML -> TEXT
# ============================================================

def clean_html(html):
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
        r"(?i)</(?:p|div|tr|li|h1|h2|h3|td)>",
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
# GELDWERTE NORMALISIEREN
# ============================================================

def money_to_billions(number, unit):
    try:
        value = float(
            number.replace(",", "")
        )
    except (ValueError, AttributeError):
        return None

    unit = unit.lower()

    if unit in (
        "billion",
        "billions",
    ):
        return value

    if unit in (
        "million",
        "millions",
    ):
        return value / 1000.0

    if unit in (
        "trillion",
        "trillions",
    ):
        return value * 1000.0

    return None


# ============================================================
# RELEVANTE PASSAGEN
# ============================================================

def find_metric_passages(text):
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    results = []

    for i, sentence in enumerate(sentences):
        lower = sentence.lower()
        found_metric = None

        for metric, terms in METRICS.items():
            if any(
                term in lower
                for term in terms
            ):
                found_metric = metric
                break

        if not found_metric:
            continue

        start = max(0, i - 1)
        end = min(
            len(sentences),
            i + 2,
        )

        passage = " ".join(
            sentences[start:end]
        ).strip()

        if 40 <= len(passage) <= 3000:
            results.append({
                "metric": found_metric,
                "text": passage,
            })

    return results


# ============================================================
# GELDWERTE EXTRAHIEREN
# ============================================================

def extract_money_values(passage):
    text = passage["text"]
    values = []

    patterns = [
        (
            r"\$\s*([0-9]+(?:\.[0-9]+)?)\s*"
            r"(billion|billions|million|millions|"
            r"trillion|trillions)"
        ),
        (
            r"([0-9]+(?:\.[0-9]+)?)\s*"
            r"(billion|billions|million|millions|"
            r"trillion|trillions)\s+"
            r"(?:U\.S\.\s*)?dollars"
        ),
    ]

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.I,
        ):
            value = money_to_billions(
                match.group(1),
                match.group(2),
            )

            if value is None:
                continue

            values.append({
                "value_bn": value,
                "raw": match.group(0),
            })

    return values


# ============================================================
# BESTEN WERT AUS PASSAGE WÄHLEN
# ============================================================

def choose_metric_value(
    metric,
    passage_text,
    values,
):
    if not values:
        return None

    lower = passage_text.lower()
    candidates = []

    for item in values:
        raw_lower = item["raw"].lower()
        pos = lower.find(raw_lower)

        if pos == -1:
            candidate = dict(item)
            candidate[
                "recognition_context"
            ] = False

            candidates.append(
                candidate
            )
            continue

        context = lower[
            max(0, pos - 180):
            min(len(lower), pos + 180)
        ]

        recognition_words = [
            "recognized",
            "recognize",
            "recognition",
            "next twelve months",
            "next 12 months",
            "over the next",
        ]

        candidate = dict(item)

        candidate[
            "recognition_context"
        ] = any(
            word in context
            for word in recognition_words
        )

        candidates.append(
            candidate
        )

    preferred = [
        item
        for item in candidates
        if not item[
            "recognition_context"
        ]
    ]

    pool = (
        preferred
        if preferred
        else candidates
    )

    if not pool:
        return None

    return max(
        pool,
        key=lambda x:
            x["value_bn"],
    )


# ============================================================
# DOKUMENT ANALYSIEREN
# ============================================================

def analyse_text(text):
    passages = find_metric_passages(
        text
    )

    candidates = []

    for passage in passages:
        values = extract_money_values(
            passage
        )

        chosen = choose_metric_value(
            passage["metric"],
            passage["text"],
            values,
        )

        if chosen:
            candidates.append({
                "metric":
                    passage["metric"],
                "value_bn":
                    chosen["value_bn"],
                "raw":
                    chosen["raw"],
                "passage":
                    passage["text"],
            })

    best_by_metric = {}

    for candidate in candidates:
        metric = candidate["metric"]

        if metric not in best_by_metric:
            best_by_metric[
                metric
            ] = candidate

        elif (
            candidate["value_bn"]
            >
            best_by_metric[
                metric
            ]["value_bn"]
        ):
            best_by_metric[
                metric
            ] = candidate

    return best_by_metric


# ============================================================
# SEC SUBMISSIONS
# ============================================================

def load_submissions(cik):
    url = (
        "https://data.sec.gov/"
        f"submissions/CIK{cik}.json"
    )

    data = get_json(url)

    recent = (
        data.get("filings", {})
        .get("recent", {})
    )

    filings = []

    for (
        form,
        accession,
        document,
        filing_date,
    ) in zip(
        recent.get("form", []),
        recent.get(
            "accessionNumber",
            [],
        ),
        recent.get(
            "primaryDocument",
            [],
        ),
        recent.get(
            "filingDate",
            [],
        ),
    ):
        if form not in (
            "10-Q",
            "10-K",
        ):
            continue

        filings.append({
            "form": form,
            "accession": accession,
            "document": document,
            "filing_date": filing_date,
        })

        if len(filings) >= 12:
            break

    return filings


# ============================================================
# SEC DOKUMENT LADEN
# ============================================================

def load_document(cik, filing):
    accession = (
        filing["accession"]
        .replace("-", "")
    )

    cik_number = str(
        int(cik)
    )

    url = (
        "https://www.sec.gov/"
        "Archives/edgar/data/"
        f"{cik_number}/"
        f"{accession}/"
        f"{filing['document']}"
    )

    try:
        html = get_text(url)
    except Exception:
        return None

    metrics = analyse_text(
        clean_html(html)
    )

    return {
        "filing_date":
            filing["filing_date"],
        "form":
            filing["form"],
        "metrics":
            metrics,
    }


# ============================================================
# VERÄNDERUNG
# ============================================================

def compare_values(
    current,
    previous,
):
    if (
        current is None
        or previous is None
        or previous <= 0
    ):
        return None

    return (
        (current / previous) - 1
    ) * 100


# ============================================================
# PLAUSIBILITÄTSPRÜFUNG
# ============================================================

def plausibility_check(change):
    if change is None:
        return {
            "valid": False,
            "reason":
                "Keine Veränderung berechenbar.",
        }

    if change > MAX_POSITIVE_JUMP:
        return {
            "valid": False,
            "reason":
                "Ungewöhnlich großer positiver "
                "Sprung. Vergleichbarkeit prüfen.",
        }

    if change < MAX_NEGATIVE_JUMP:
        return {
            "valid": False,
            "reason":
                "Ungewöhnlich großer negativer "
                "Sprung. Vergleichbarkeit prüfen.",
        }

    return {
        "valid": True,
        "reason":
            "Veränderung plausibel.",
    }


# ============================================================
# SCORE
# ============================================================

def bullwerk_score(change):
    check = plausibility_check(
        change
    )

    if not check["valid"]:
        return {
            "score": None,
            "status":
                "CHECK_REQUIRED",
            "reason":
                check["reason"],
        }

    if change >= 15:
        return {
            "score": 3,
            "status":
                "STRONG_POSITIVE",
            "reason":
                "Starkes Wachstum.",
        }

    if change >= 5:
        return {
            "score": 3,
            "status":
                "POSITIVE",
            "reason":
                "Klare positive Entwicklung.",
        }

    if change >= -5:
        return {
            "score": 2,
            "status":
                "STABLE",
            "reason":
                "Stabile bis leicht positive "
                "Entwicklung.",
        }

    if change >= -15:
        return {
            "score": 1,
            "status":
                "CAUTIOUS",
            "reason":
                "Moderate Verschlechterung.",
        }

    return {
        "score": 0,
        "status":
            "WEAKER",
        "reason":
            "Deutliche Verschlechterung.",
    }


# ============================================================
# V6 DIREKTER VERGLEICH
# ============================================================

def build_comparison(
    results,
    metric,
):
    observations = []

    for result in results:
        if metric in result["metrics"]:
            observations.append({
                "date":
                    result["filing_date"],
                "form":
                    result["form"],
                "value":
                    result[
                        "metrics"
                    ][
                        metric
                    ][
                        "value_bn"
                    ],
            })

    if len(observations) < 2:
        return None

    # SEC-Liste kommt neu -> alt.
    current = observations[0]
    previous = observations[1]

    change = compare_values(
        current["value"],
        previous["value"],
    )

    if change is None:
        return None

    score_data = bullwerk_score(
        change
    )

    return {
        "metric":
            metric,
        "current":
            current,
        "previous":
            previous,
        "change":
            change,
        "score":
            score_data["score"],
        "status":
            score_data["status"],
        "reason":
            score_data["reason"],
        "same_form": (
            current["form"]
            == previous["form"]
        ),
    }


# ============================================================
# HAUPTFUNKTION FÜR BULLWERK
# ============================================================

def get_orders_backlog_data(cik):
    """
    Hauptfunktion für den Bullwerk Scanner.

    Sucht RPO, Backlog und Bookings in den
    jüngsten 10-Q/10-K-Filings und bewertet
    die jüngste Veränderung nach V6.
    """

    filings = load_submissions(
        cik
    )

    results = []

    for filing in filings:
        result = load_document(
            cik,
            filing,
        )

        if result is not None:
            results.append(
                result
            )

    comparisons = []

    for metric in (
        "RPO",
        "BACKLOG",
        "BOOKINGS",
    ):
        comparison = build_comparison(
            results,
            metric,
        )

        if comparison:
            comparisons.append(
                comparison
            )

    if not comparisons:
        return {
            "metric": None,
            "score": None,
            "status": "N/A",
            "reason":
                "Keine zwei vergleichbaren "
                "Backlog-, RPO- oder Bookings-Werte gefunden.",
            "comparisons": [],
        }

    priority = {
        "BACKLOG": 3,
        "BOOKINGS": 2,
        "RPO": 1,
    }

    comparisons.sort(
        key=lambda x:
            priority[x["metric"]],
        reverse=True,
    )

    best = comparisons[0]

    return {
        "metric":
            best["metric"],
        "score":
            best["score"],
        "status":
            best["status"],
        "reason":
            best["reason"],
        "change":
            best["change"],
        "current":
            best["current"],
        "previous":
            best["previous"],
        "same_form":
            best["same_form"],
        "comparisons":
            comparisons,
    }
