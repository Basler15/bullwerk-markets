# Bullwerk Markets - Revenue Modul

from datetime import datetime


REVENUE_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "Revenues",
]


def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def duration_days(row):
    start = parse_date(row.get("start"))
    end = parse_date(row.get("end"))

    if not start or not end:
        return None

    return (end - start).days


def usable_revenue_rows(facts, concept):
    """
    Holt brauchbare Revenue-Datensätze eines SEC-Concepts.
    """

    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    concept_data = us_gaap.get(concept)

    if not concept_data:
        return []

    units = concept_data.get("units", {})

    rows = units.get("USD", [])

    usable = []

    for row in rows:
        if row.get("form") not in ("10-Q", "10-K"):
            continue

        start = parse_date(row.get("start"))
        end = parse_date(row.get("end"))

        if not start or not end:
            continue

        duration = duration_days(row)

        if duration is None:
            continue

        # Einzelquartal
        quarter = 70 <= duration <= 110

        # Halbjahr / kumuliertes Q2
        half_year = 150 <= duration <= 220

        # Neun Monate / kumuliertes Q3
        nine_months = 230 <= duration <= 310

        # Geschäftsjahr
        full_year = 330 <= duration <= 380

        if not (
            quarter
            or half_year
            or nine_months
            or full_year
        ):
            continue

        usable.append(row)

    return usable


def concept_quality(facts, concept):
    """
    Bewertet ein Revenue-Concept danach,
    wie aktuell und brauchbar seine SEC-Daten sind.
    """

    rows = usable_revenue_rows(
        facts,
        concept,
    )

    if not rows:
        return None

    end_dates = [
        parse_date(row.get("end"))
        for row in rows
        if parse_date(row.get("end"))
    ]

    filed_dates = [
        parse_date(row.get("filed"))
        for row in rows
        if parse_date(row.get("filed"))
    ]

    if not end_dates:
        return None

    latest_end = max(end_dates)

    latest_filed = (
        max(filed_dates)
        if filed_dates
        else None
    )

    recent_quarters = 0

    for row in rows:
        duration = duration_days(row)

        if duration is None:
            continue

        if 70 <= duration <= 110:
            recent_quarters += 1

    return {
        "concept": concept,
        "rows": rows,
        "latest_end": latest_end,
        "latest_filed": latest_filed,
        "quarter_rows": recent_quarters,
    }


def select_revenue_concept(facts):
    """
    Wählt automatisch das aktuellste brauchbare
    Revenue-Concept.

    Wichtig für Unternehmen wie NVDA:
    Ein alter SEC-Tag darf einen aktuelleren
    Revenue-Tag nicht mehr blockieren.
    """

    candidates = []

    for concept in REVENUE_CONCEPTS:
        quality = concept_quality(
            facts,
            concept,
        )

        if quality:
            candidates.append(quality)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["latest_end"],
            item["quarter_rows"],
            item["latest_filed"]
            or datetime.min.date(),
        ),
        reverse=True,
    )

    return candidates[0]


def get_revenue_data(facts):
    """
    Zentrale Revenue-Ausgabe für die späteren
    Bullwerk-Fundamentalmodule.
    """

    selected = select_revenue_concept(facts)

    if not selected:
        return {
            "concept": None,
            "rows": [],
            "latest_end": None,
        }

    return {
        "concept": selected["concept"],
        "rows": selected["rows"],
        "latest_end": selected["latest_end"],
    }
