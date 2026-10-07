# Bullwerk Markets - Gewinn & EPS Modul

from datetime import datetime


PROFIT_CONCEPTS = [
    "NetIncomeLoss",
]

EPS_CONCEPTS = [
    "EarningsPerShareDiluted",
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


def get_concept_rows(facts, concepts, units):
    """
    Holt brauchbare SEC-Datensätze für ein Concept.
    """

    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    for concept in concepts:
        concept_data = us_gaap.get(concept)

        if not concept_data:
            continue

        concept_units = concept_data.get("units", {})

        rows = []

        for unit in units:
            rows.extend(concept_units.get(unit, []))

        usable = []

        for row in rows:
            if row.get("form") not in ("10-Q", "10-K"):
                continue

            duration = duration_days(row)

            if duration is None:
                continue

            if (
                70 <= duration <= 110
                or 150 <= duration <= 220
                or 230 <= duration <= 310
                or 330 <= duration <= 380
            ):
                usable.append(row)

        if usable:
            return {
                "concept": concept,
                "rows": usable,
            }

    return {
        "concept": None,
        "rows": [],
    }


def get_profit_data(facts):
    """
    Holt Net Income aus den SEC Company Facts.
    """

    return get_concept_rows(
        facts,
        PROFIT_CONCEPTS,
        ["USD"],
    )


def get_eps_data(facts):
    """
    Holt diluted EPS aus den SEC Company Facts.
    """

    return get_concept_rows(
        facts,
        EPS_CONCEPTS,
        ["USD/shares", "USD / shares"],
    )


def get_profit_eps_data(facts):
    """
    Gemeinsame Ausgabe für spätere Bullwerk-Module.
    """

    profit = get_profit_data(facts)
    eps = get_eps_data(facts)

    return {
        "profit_concept": profit["concept"],
        "profit_rows": profit["rows"],
        "eps_concept": eps["concept"],
        "eps_rows": eps["rows"],
    }
