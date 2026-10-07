# Bullwerk Markets - Margin & Free Cashflow Modul

from datetime import datetime


OPERATING_INCOME_CONCEPTS = [
    "OperatingIncomeLoss",
]

OPERATING_CASHFLOW_CONCEPTS = [
    "NetCashProvidedByUsedInOperatingActivities",
]

CAPEX_CONCEPTS = [
    "PaymentsToAcquirePropertyPlantAndEquipment",
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


def get_operating_income_data(facts):
    """
    Operatives Ergebnis für die spätere
    Berechnung der operativen Marge.
    """

    return get_concept_rows(
        facts,
        OPERATING_INCOME_CONCEPTS,
        ["USD"],
    )


def get_operating_cashflow_data(facts):
    """
    Operativer Cashflow.
    """

    return get_concept_rows(
        facts,
        OPERATING_CASHFLOW_CONCEPTS,
        ["USD"],
    )


def get_capex_data(facts):
    """
    Investitionsausgaben (CapEx).
    """

    return get_concept_rows(
        facts,
        CAPEX_CONCEPTS,
        ["USD"],
    )


def get_margin_fcf_data(facts):
    """
    Gemeinsame Rohdaten-Ausgabe für
    operative Marge und Free Cashflow.

    Free Cashflow wird später aus
    Operating Cashflow minus CapEx berechnet.

    Revenue kommt aus dem separaten
    revenue.py-Modul.
    """

    operating_income = get_operating_income_data(facts)
    operating_cashflow = get_operating_cashflow_data(facts)
    capex = get_capex_data(facts)

    return {
        "operating_income_concept":
            operating_income["concept"],

        "operating_income_rows":
            operating_income["rows"],

        "operating_cashflow_concept":
            operating_cashflow["concept"],

        "operating_cashflow_rows":
            operating_cashflow["rows"],

        "capex_concept":
            capex["concept"],

        "capex_rows":
            capex["rows"],
    }
