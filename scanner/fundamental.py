# Bullwerk Markets - Fundamental Scanner
#
# Zentrale Schaltstelle für die getesteten
# Fundamental-Module.
#
# Verbindet:
# - SEC Company Facts
# - Revenue
# - Profit / EPS
# - Margin / FCF
# - Guidance
# - Orders / Backlog
# - Supply / Demand
# - Fundamental Anomaly
#
# ANOMALY bleibt separat und verändert
# den normalen Fundamental-Score nicht.

from datetime import datetime

from scanner.sec_data import get_company_facts
from scanner.revenue import get_revenue_data
from scanner.profit_eps import get_profit_eps_data
from scanner.margin_fcf import get_margin_fcf_data
from scanner.guidance import get_guidance_data
from scanner.orders_backlog import get_orders_backlog_data
from scanner.supply_demand import get_supply_demand_data
from scanner.anomaly import get_anomaly_data


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def parse_date(value):
    if not value:
        return None

    if hasattr(value, "year"):
        return value

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (ValueError, TypeError):
        return None


def row_duration(row):
    start = parse_date(
        row.get("start")
    )

    end = parse_date(
        row.get("end")
    )

    if not start or not end:
        return None

    return (end - start).days


def is_quarter(row):
    duration = row_duration(row)

    if duration is None:
        return False

    return 70 <= duration <= 110


def dedupe_quarters(rows):
    """
    Bereinigt doppelte SEC-Einträge.

    Pro wirtschaftlichem Quartalsende wird
    möglichst der zuletzt eingereichte Wert
    verwendet.
    """

    by_end = {}

    for row in rows:
        if not is_quarter(row):
            continue

        end = parse_date(
            row.get("end")
        )

        if not end:
            continue

        filed = parse_date(
            row.get("filed")
        )

        existing = by_end.get(end)

        if existing is None:
            by_end[end] = row
            continue

        existing_filed = parse_date(
            existing.get("filed")
        )

        if (
            filed
            and (
                existing_filed is None
                or filed > existing_filed
            )
        ):
            by_end[end] = row

    return sorted(
        by_end.values(),
        key=lambda row:
            parse_date(row.get("end")),
        reverse=True,
    )


def numeric_value(row):
    if not row:
        return None

    value = row.get("val")

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def find_yoy_previous(
    rows,
    current_row,
):
    """
    Sucht das Quartal ungefähr ein Jahr
    vor dem aktuellen Quartal.
    """

    current_end = parse_date(
        current_row.get("end")
    )

    if not current_end:
        return None

    candidates = []

    for row in rows:
        end = parse_date(
            row.get("end")
        )

        if not end:
            continue

        gap = (
            current_end - end
        ).days

        if 330 <= gap <= 400:
            candidates.append(
                (
                    abs(gap - 365),
                    row,
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item:
            item[0]
    )

    return candidates[0][1]


def percent_change(
    current,
    previous,
):
    if (
        current is None
        or previous is None
        or previous == 0
    ):
        return None

    return (
        (current - previous)
        / abs(previous)
    ) * 100.0


def quarter_yoy_growth(rows):
    """
    Liefert aktuelles YoY-Wachstum und
    vorheriges YoY-Wachstum.

    Daraus kann die Beschleunigung
    berechnet werden.
    """

    quarters = dedupe_quarters(
        rows
    )

    if not quarters:
        return {
            "current_growth": None,
            "previous_growth": None,
            "acceleration": None,
        }

    growth_rates = []

    for current in quarters:
        previous = find_yoy_previous(
            quarters,
            current,
        )

        if not previous:
            continue

        current_value = numeric_value(
            current
        )

        previous_value = numeric_value(
            previous
        )

        growth = percent_change(
            current_value,
            previous_value,
        )

        if growth is None:
            continue

        growth_rates.append({
            "end":
                current.get("end"),
            "growth":
                growth,
        })

    if not growth_rates:
        return {
            "current_growth": None,
            "previous_growth": None,
            "acceleration": None,
        }

    current_growth = (
        growth_rates[0]["growth"]
    )

    previous_growth = None

    if len(growth_rates) >= 2:
        previous_growth = (
            growth_rates[1]["growth"]
        )

    acceleration = None

    if previous_growth is not None:
        acceleration = (
            current_growth
            - previous_growth
        )

    return {
        "current_growth":
            current_growth,

        "previous_growth":
            previous_growth,

        "acceleration":
            acceleration,
    }


# ============================================================
# MARGE
# ============================================================

def align_quarters(
    first_rows,
    second_rows,
):
    """
    Verbindet zwei Quartalsserien über
    das wirtschaftliche Quartalsende.
    """

    first = {
        row.get("end"): row
        for row in dedupe_quarters(
            first_rows
        )
    }

    second = {
        row.get("end"): row
        for row in dedupe_quarters(
            second_rows
        )
    }

    common_dates = sorted(
        set(first.keys())
        & set(second.keys()),
        reverse=True,
    )

    return [
        (
            date,
            first[date],
            second[date],
        )
        for date in common_dates
    ]


def margin_metrics(
    revenue_rows,
    operating_income_rows,
):
    aligned = align_quarters(
        revenue_rows,
        operating_income_rows,
    )

    margins = []

    for end, revenue_row, income_row in aligned:
        revenue = numeric_value(
            revenue_row
        )

        operating_income = numeric_value(
            income_row
        )

        if (
            revenue is None
            or operating_income is None
            or revenue == 0
        ):
            continue

        margin = (
            operating_income
            / revenue
        ) * 100.0

        margins.append({
            "end": end,
            "margin": margin,
        })

    if not margins:
        return {
            "current_margin": None,
            "margin_change": None,
            "margin_acceleration": None,
        }

    current_margin = (
        margins[0]["margin"]
    )

    margin_change = None

    if len(margins) >= 2:
        margin_change = (
            margins[0]["margin"]
            - margins[1]["margin"]
        )

    margin_acceleration = None

    if len(margins) >= 3:
        previous_change = (
            margins[1]["margin"]
            - margins[2]["margin"]
        )

        margin_acceleration = (
            margin_change
            - previous_change
        )

    return {
        "current_margin":
            current_margin,

        "margin_change":
            margin_change,

        "margin_acceleration":
            margin_acceleration,
    }


# ============================================================
# FREE CASHFLOW
# ============================================================

def fcf_rows(
    operating_cashflow_rows,
    capex_rows,
):
    aligned = align_quarters(
        operating_cashflow_rows,
        capex_rows,
    )

    results = []

    for end, ocf_row, capex_row in aligned:
        ocf = numeric_value(
            ocf_row
        )

        capex = numeric_value(
            capex_row
        )

        if (
            ocf is None
            or capex is None
        ):
            continue

        results.append({
            "start":
                ocf_row.get("start"),

            "end":
                end,

            "filed":
                ocf_row.get("filed"),

            "form":
                ocf_row.get("form"),

            "val":
                ocf - abs(capex),
        })

    return results


# ============================================================
# EINZEL-SCORES
# ============================================================

def revenue_score(
    growth,
    acceleration,
):
    if growth is None:
        return None

    if (
        growth >= 20
        and (
            acceleration is None
            or acceleration >= 0
        )
    ):
        return 4

    if growth >= 10:
        return 3

    if growth >= 5:
        return 2

    if growth >= 0:
        return 1

    return 0


def profit_eps_score(
    profit_growth,
    eps_growth,
):
    values = [
        value
        for value in (
            profit_growth,
            eps_growth,
        )
        if value is not None
    ]

    if not values:
        return None

    best = max(values)

    if best >= 25:
        return 4

    if best >= 10:
        return 3

    if best >= 0:
        return 2

    if best >= -10:
        return 1

    return 0


def margin_fcf_score(
    margin_change,
    fcf_growth,
):
    points = 0
    available = 0

    if margin_change is not None:
        available += 2

        if margin_change >= 1.5:
            points += 2
        elif margin_change >= 0:
            points += 1

    if fcf_growth is not None:
        available += 2

        if fcf_growth >= 20:
            points += 2
        elif fcf_growth >= 0:
            points += 1

    if available == 0:
        return None

    return round(
        points / available * 4,
        2,
    )


def operational_score(
    guidance_score,
    orders_score,
):
    values = [
        value
        for value in (
            guidance_score,
            orders_score,
        )
        if value is not None
    ]

    if not values:
        return None

    normalized = [
        value / 3 * 4
        for value in values
    ]

    return round(
        sum(normalized)
        / len(normalized),
        2,
    )


# ============================================================
# NORMALISIERTER FUNDAMENTAL SCORE
# ============================================================

def normalized_score(
    components,
):
    """
    Fehlende N/A-Komponenten werden nicht
    automatisch als Null gewertet.
    """

    earned = 0.0
    available = 0.0

    for component in components:
        score = component.get("score")
        maximum = component.get("max")

        if score is None:
            continue

        earned += score
        available += maximum

    if available == 0:
        return None

    return round(
        earned / available * 20,
        1,
    )


# ============================================================
# HAUPTFUNKTION
# ============================================================

def get_fundamental_data(
    cik,
    symbol=None,
):
    """
    Führt die getesteten Bullwerk-
    Fundamentalmodule zusammen.
    """

    facts = get_company_facts(
        cik
    )

    revenue = get_revenue_data(
        facts
    )

    profit_eps = get_profit_eps_data(
        facts
    )

    margin_fcf = get_margin_fcf_data(
        facts
    )

    guidance = get_guidance_data(
        str(cik).zfill(10)
    )

    orders = get_orders_backlog_data(
        str(cik).zfill(10)
    )


    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue_metrics = quarter_yoy_growth(
        revenue.get(
            "rows",
            [],
        )
    )


    # --------------------------------------------------------
    # PROFIT
    # --------------------------------------------------------

    profit_metrics = quarter_yoy_growth(
        profit_eps.get(
            "profit_rows",
            [],
        )
    )


    # --------------------------------------------------------
    # EPS
    # --------------------------------------------------------

    eps_metrics = quarter_yoy_growth(
        profit_eps.get(
            "eps_rows",
            [],
        )
    )


    # --------------------------------------------------------
    # MARGIN
    # --------------------------------------------------------

    margin_metrics_data = margin_metrics(
        revenue.get(
            "rows",
            [],
        ),
        margin_fcf.get(
            "operating_income_rows",
            [],
        ),
    )


    # --------------------------------------------------------
    # FREE CASHFLOW
    # --------------------------------------------------------

    calculated_fcf_rows = fcf_rows(
        margin_fcf.get(
            "operating_cashflow_rows",
            [],
        ),
        margin_fcf.get(
            "capex_rows",
            [],
        ),
    )

    fcf_metrics_data = quarter_yoy_growth(
        calculated_fcf_rows
    )


    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    orders_change = orders.get(
        "change"
    )

    orders_score = orders.get(
        "score"
    )


    # --------------------------------------------------------
    # GUIDANCE
    # --------------------------------------------------------

    guidance_score = guidance.get(
        "score"
    )


    # --------------------------------------------------------
    # SUPPLY / DEMAND
    #
    # supply_constraint und pricing_power
    # bleiben False, bis wir dafür eine
    # belastbare Datenquelle angeschlossen haben.
    # --------------------------------------------------------

    supply_demand = get_supply_demand_data(
        revenue_growth=
            revenue_metrics[
                "current_growth"
            ],

        revenue_acceleration=
            revenue_metrics[
                "acceleration"
            ],

        margin_change=
            margin_metrics_data[
                "margin_change"
            ],

        fcf_growth=
            fcf_metrics_data[
                "current_growth"
            ],

        orders_change=
            orders_change,

        guidance_score=
            guidance_score,

        supply_constraint=False,
        pricing_power=False,
    )


    # --------------------------------------------------------
    # ANOMALY
    # --------------------------------------------------------

    anomaly = get_anomaly_data(
        revenue_growth=
            revenue_metrics[
                "current_growth"
            ],

        revenue_acceleration=
            revenue_metrics[
                "acceleration"
            ],

        profit_growth=
            profit_metrics[
                "current_growth"
            ],

        profit_acceleration=
            profit_metrics[
                "acceleration"
            ],

        eps_growth=
            eps_metrics[
                "current_growth"
            ],

        eps_acceleration=
            eps_metrics[
                "acceleration"
            ],

        margin_change=
            margin_metrics_data[
                "margin_change"
            ],

        margin_acceleration=
            margin_metrics_data[
                "margin_acceleration"
            ],

        fcf_growth=
            fcf_metrics_data[
                "current_growth"
            ],

        fcf_acceleration=
            fcf_metrics_data[
                "acceleration"
            ],

        orders_change=
            orders_change,

        orders_acceleration=None,

        guidance_score=
            guidance_score,
    )


    # --------------------------------------------------------
    # 5 FUNDAMENTAL-KOMPONENTEN
    # --------------------------------------------------------

    revenue_component = revenue_score(
        revenue_metrics[
            "current_growth"
        ],
        revenue_metrics[
            "acceleration"
        ],
    )

    profit_component = profit_eps_score(
        profit_metrics[
            "current_growth"
        ],
        eps_metrics[
            "current_growth"
        ],
    )

    margin_component = margin_fcf_score(
        margin_metrics_data[
            "margin_change"
        ],
        fcf_metrics_data[
            "current_growth"
        ],
    )

    operational_component = operational_score(
        guidance_score,
        orders_score,
    )

    supply_component = (
        supply_demand.get(
            "score"
        )
    )

    components = [
        {
            "name": "Revenue",
            "score": revenue_component,
            "max": 4,
        },
        {
            "name": "Profit_EPS",
            "score": profit_component,
            "max": 4,
        },
        {
            "name": "Margin_FCF",
            "score": margin_component,
            "max": 4,
        },
        {
            "name": "Guidance_Orders",
            "score": operational_component,
            "max": 4,
        },
        {
            "name": "Supply_Demand",
            "score": supply_component,
            "max": 4,
        },
    ]


    fundamental_score = normalized_score(
        components
    )


    # --------------------------------------------------------
    # AUSGABE
    # --------------------------------------------------------

    return {
        "symbol":
            symbol,

        "cik":
            str(cik).zfill(10),

        "fundamental_score":
            fundamental_score,

        "max_score":
            20,

        "components":
            components,

        "revenue":
            revenue_metrics,

        "profit":
            profit_metrics,

        "eps":
            eps_metrics,

        "margin":
            margin_metrics_data,

        "fcf":
            fcf_metrics_data,

        "guidance":
            guidance,

        "orders_backlog":
            orders,

        "supply_demand":
            supply_demand,

        "anomaly":
            anomaly,
    }
