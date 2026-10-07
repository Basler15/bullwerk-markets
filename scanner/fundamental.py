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
#
# V2:
# - Profit/EPS-Konsistenz verbessert
# - extreme Basiseffekte werden erkannt
# - extreme Prozentwerte führen nicht
#   automatisch zu Maximalpunkten

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
# GRENZWERTE
# ============================================================

EXTREME_GROWTH = 200.0
EXTREME_ACCELERATION = 150.0

PROFIT_EPS_DIVERGENCE = 75.0


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
    der zuletzt eingereichte Wert verwendet.
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
    Liefert aktuelles YoY-Wachstum,
    vorheriges YoY-Wachstum und
    Beschleunigung.
    """

    quarters = dedupe_quarters(
        rows
    )

    if not quarters:
        return {
            "current_growth": None,
            "previous_growth": None,
            "acceleration": None,
            "current_value": None,
            "previous_value": None,
            "base_effect": False,
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

            "current_value":
                current_value,

            "previous_value":
                previous_value,
        })

    if not growth_rates:
        return {
            "current_growth": None,
            "previous_growth": None,
            "acceleration": None,
            "current_value": None,
            "previous_value": None,
            "base_effect": False,
        }

    current_data = growth_rates[0]

    current_growth = (
        current_data["growth"]
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

    base_effect = (
        abs(current_growth)
        >= EXTREME_GROWTH
    )

    return {
        "current_growth":
            current_growth,

        "previous_growth":
            previous_growth,

        "acceleration":
            acceleration,

        "current_value":
            current_data[
                "current_value"
            ],

        "previous_value":
            current_data[
                "previous_value"
            ],

        "base_effect":
            base_effect,
    }


# ============================================================
# MARGE
# ============================================================

def align_quarters(
    first_rows,
    second_rows,
):
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
# REVENUE SCORE
# ============================================================

def revenue_score(
    growth,
    acceleration,
    base_effect=False,
):
    if growth is None:
        return None

    # Extreme Wachstumsraten bleiben positiv,
    # werden aber nicht allein wegen ihrer
    # Größenordnung stärker als 4/4 gewertet.

    if growth >= 20:
        return 4

    if growth >= 10:
        return 3

    if growth >= 5:
        return 2

    if growth >= 0:
        return 1

    return 0


# ============================================================
# PROFIT / EPS SCORE
# ============================================================

def profit_eps_score(
    profit_growth,
    eps_growth,
    profit_base_effect=False,
    eps_base_effect=False,
):
    """
    Profit und EPS werden gemeinsam bewertet.

    Wichtig:
    Ein sehr starkes EPS darf einen stark
    fallenden Gewinn nicht vollständig
    überstimmen.
    """

    if (
        profit_growth is None
        and eps_growth is None
    ):
        return None

    # Nur Profit vorhanden
    if eps_growth is None:
        if profit_growth >= 25:
            return 4
        if profit_growth >= 10:
            return 3
        if profit_growth >= 0:
            return 2
        if profit_growth >= -10:
            return 1
        return 0

    # Nur EPS vorhanden
    if profit_growth is None:
        if eps_growth >= 25:
            return 4
        if eps_growth >= 10:
            return 3
        if eps_growth >= 0:
            return 2
        if eps_growth >= -10:
            return 1
        return 0

    # --------------------------------------------------------
    # Widerspruch zwischen Profit und EPS
    # --------------------------------------------------------

    divergence = abs(
        profit_growth
        - eps_growth
    )

    opposite_direction = (
        (
            profit_growth < 0
            and eps_growth > 0
        )
        or
        (
            eps_growth < 0
            and profit_growth > 0
        )
    )

    if (
        opposite_direction
        and divergence
        >= PROFIT_EPS_DIVERGENCE
    ):
        # AVGO-artiger Fall:
        # ein Wert extrem positiv,
        # der andere klar negativ.
        return 2

    if opposite_direction:
        return 2

    # --------------------------------------------------------
    # Beide positiv
    # --------------------------------------------------------

    if (
        profit_growth >= 25
        and eps_growth >= 25
    ):
        return 4

    if (
        profit_growth >= 10
        and eps_growth >= 10
    ):
        return 3

    if (
        profit_growth >= 0
        and eps_growth >= 0
    ):
        return 2

    # --------------------------------------------------------
    # Beide negativ
    # --------------------------------------------------------

    if (
        profit_growth >= -10
        and eps_growth >= -10
    ):
        return 1

    return 0


# ============================================================
# MARGIN / FCF SCORE
# ============================================================

def margin_fcf_score(
    margin_change,
    fcf_growth,
    fcf_base_effect=False,
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


# ============================================================
# GUIDANCE / ORDERS
# ============================================================

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
    N/A wird nicht automatisch als
    Null gewertet.
    """

    earned = 0.0
    available = 0.0

    for component in components:
        score = component.get(
            "score"
        )

        maximum = component.get(
            "max"
        )

        if score is None:
            continue

        earned += score
        available += maximum

    if available == 0:
        return None

    return round(
        earned
        / available
        * 20,
        1,
    )


# ============================================================
# QUALITY FLAGS
# ============================================================

def build_quality_flags(
    revenue_metrics,
    profit_metrics,
    eps_metrics,
    fcf_metrics,
):
    flags = []

    if revenue_metrics.get(
        "base_effect"
    ):
        flags.append(
            "REVENUE_EXTREME_BASE_EFFECT"
        )

    if profit_metrics.get(
        "base_effect"
    ):
        flags.append(
            "PROFIT_EXTREME_BASE_EFFECT"
        )

    if eps_metrics.get(
        "base_effect"
    ):
        flags.append(
            "EPS_EXTREME_BASE_EFFECT"
        )

    if fcf_metrics.get(
        "base_effect"
    ):
        flags.append(
            "FCF_EXTREME_BASE_EFFECT"
        )

    profit_growth = profit_metrics.get(
        "current_growth"
    )

    eps_growth = eps_metrics.get(
        "current_growth"
    )

    if (
        profit_growth is not None
        and eps_growth is not None
    ):
        opposite = (
            (
                profit_growth < 0
                and eps_growth > 0
            )
            or
            (
                profit_growth > 0
                and eps_growth < 0
            )
        )

        if opposite:
            flags.append(
                "PROFIT_EPS_DIVERGENCE"
            )

    return flags


# ============================================================
# HAUPTFUNKTION
# ============================================================

def get_fundamental_data(
    cik,
    symbol=None,
):
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

    normalized_cik = str(
        cik
    ).zfill(10)

    guidance = get_guidance_data(
        normalized_cik
    )

    orders = get_orders_backlog_data(
        normalized_cik
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
    # ORDERS / GUIDANCE
    # --------------------------------------------------------

    orders_change = orders.get(
        "change"
    )

    orders_score = orders.get(
        "score"
    )

    guidance_score = guidance.get(
        "score"
    )


    # --------------------------------------------------------
    # SUPPLY / DEMAND
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
    # SCORES
    # --------------------------------------------------------

    revenue_component = revenue_score(
        revenue_metrics[
            "current_growth"
        ],

        revenue_metrics[
            "acceleration"
        ],

        revenue_metrics[
            "base_effect"
        ],
    )

    profit_component = profit_eps_score(
        profit_metrics[
            "current_growth"
        ],

        eps_metrics[
            "current_growth"
        ],

        profit_metrics[
            "base_effect"
        ],

        eps_metrics[
            "base_effect"
        ],
    )

    margin_component = margin_fcf_score(
        margin_metrics_data[
            "margin_change"
        ],

        fcf_metrics_data[
            "current_growth"
        ],

        fcf_metrics_data[
            "base_effect"
        ],
    )

    operational_component = operational_score(
        guidance_score,
        orders_score,
    )

    supply_component = supply_demand.get(
        "score"
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
    # QUALITY FLAGS
    # --------------------------------------------------------

    quality_flags = build_quality_flags(
        revenue_metrics,
        profit_metrics,
        eps_metrics,
        fcf_metrics_data,
    )


    # --------------------------------------------------------
    # AUSGABE
    # --------------------------------------------------------

    return {
        "symbol":
            symbol,

        "cik":
            normalized_cik,

        "fundamental_score":
            fundamental_score,

        "max_score":
            20,

        "components":
            components,

        "quality_flags":
            quality_flags,

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
