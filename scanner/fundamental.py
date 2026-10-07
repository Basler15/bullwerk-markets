# Bullwerk Markets - Fundamental Scanner
#
# Zentrale Fundamental-Schaltstelle
#
# V3:
# - direkte SEC-Quartale bevorzugen
# - fehlende Quartale aus kumulierten Perioden ableiten
# - SEC-Duplikate bereinigen
# - Profit/EPS-Konsistenz
# - Basiseffekt-/Qualitätsflags
# - Anomaly bleibt separat vom 0-20 Score

from datetime import datetime

from scanner.sec_data import get_company_facts
from scanner.revenue import get_revenue_data
from scanner.profit_eps import get_profit_eps_data
from scanner.margin_fcf import get_margin_fcf_data
from scanner.guidance import get_guidance_data
from scanner.orders_backlog import get_orders_backlog_data
from scanner.supply_demand import get_supply_demand_data
from scanner.anomaly import get_anomaly_data


EXTREME_GROWTH = 200.0
PROFIT_EPS_DIVERGENCE = 75.0


# ============================================================
# DATUM / BASIS
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


def row_duration(row):
    start = parse_date(row.get("start"))
    end = parse_date(row.get("end"))

    if not start or not end:
        return None

    return (end - start).days


def is_valid_form(row):
    return row.get("form") in (
        "10-Q",
        "10-K",
    )


# ============================================================
# SEC-DUPLIKATE
# ============================================================

def dedupe_period_rows(rows):
    """
    Gleiche wirtschaftliche Periode kann durch spätere
    SEC-Filings mehrfach vorkommen.

    Pro Start-/Enddatum wird der zuletzt eingereichte
    Datensatz verwendet.
    """

    periods = {}

    for row in rows:
        if not is_valid_form(row):
            continue

        start = parse_date(
            row.get("start")
        )

        end = parse_date(
            row.get("end")
        )

        if not start or not end:
            continue

        key = (
            start,
            end,
        )

        filed = parse_date(
            row.get("filed")
        )

        existing = periods.get(key)

        if existing is None:
            periods[key] = row
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
            periods[key] = row

    return list(
        periods.values()
    )


# ============================================================
# PERIODENTYP
# ============================================================

def period_type(row):
    """
    SEC-Zeiträume werden anhand ihrer Länge eingeordnet.

    Q  = Einzelquartal
    H  = ca. 6 Monate
    9M = ca. 9 Monate
    FY = ca. 12 Monate
    """

    days = row_duration(row)

    if days is None:
        return None

    if 70 <= days <= 110:
        return "Q"

    if 150 <= days <= 210:
        return "H"

    if 240 <= days <= 300:
        return "9M"

    if 330 <= days <= 390:
        return "FY"

    return None


# ============================================================
# DIREKTE QUARTALE
# ============================================================

def direct_quarters(rows):
    """
    Holt echte, direkt gemeldete Einzelquartale.
    """

    cleaned = dedupe_period_rows(
        rows
    )

    by_end = {}

    for row in cleaned:
        if period_type(row) != "Q":
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

    return by_end


# ============================================================
# KUMULIERTE PERIODEN
# ============================================================

def cumulative_periods(rows):
    cleaned = dedupe_period_rows(
        rows
    )

    result = []

    for row in cleaned:
        kind = period_type(row)

        if kind in (
            "H",
            "9M",
            "FY",
        ):
            result.append(row)

    return result


def make_derived_row(
    cumulative_row,
    previous_row,
):
    """
    Einzelquartal =
    längere kumulierte Periode
    minus kürzere kumulierte Periode
    desselben Geschäftsjahresbeginns.
    """

    cumulative_value = numeric_value(
        cumulative_row
    )

    previous_value = numeric_value(
        previous_row
    )

    if (
        cumulative_value is None
        or previous_value is None
    ):
        return None

    previous_end = parse_date(
        previous_row.get("end")
    )

    cumulative_end = parse_date(
        cumulative_row.get("end")
    )

    if (
        previous_end is None
        or cumulative_end is None
    ):
        return None

    start = previous_end

    # Der abgeleitete Zeitraum beginnt am Tag
    # nach dem Ende der vorherigen Periode.
    from datetime import timedelta

    derived_start = (
        previous_end
        + timedelta(days=1)
    )

    return {
        "start":
            derived_start.isoformat(),

        "end":
            cumulative_end.isoformat(),

        "filed":
            cumulative_row.get("filed"),

        "form":
            cumulative_row.get("form"),

        "val":
            cumulative_value
            - previous_value,

        "derived":
            True,
    }


def derive_from_cumulative(rows):
    """
    Leitet fehlende Einzelquartale aus kumulierten
    SEC-Perioden ab.

    Beispiele:

    9M - 6M = Q3
    6M - Q1 = Q2
    FY - 9M = Q4
    """

    cleaned = dedupe_period_rows(
        rows
    )

    direct = direct_quarters(
        rows
    )

    cumulative = cumulative_periods(
        rows
    )

    derived = {}

    # --------------------------------------------------------
    # 6M - Q1 = Q2
    # --------------------------------------------------------

    half_years = [
        row
        for row in cumulative
        if period_type(row) == "H"
    ]

    direct_rows = list(
        direct.values()
    )

    for half in half_years:
        half_start = parse_date(
            half.get("start")
        )

        half_end = parse_date(
            half.get("end")
        )

        if not half_start or not half_end:
            continue

        candidates = []

        for quarter in direct_rows:
            q_start = parse_date(
                quarter.get("start")
            )

            q_end = parse_date(
                quarter.get("end")
            )

            if not q_start or not q_end:
                continue

            if (
                abs(
                    (
                        q_start
                        - half_start
                    ).days
                )
                <= 3
                and q_end < half_end
            ):
                candidates.append(
                    quarter
                )

        if candidates:
            q1 = sorted(
                candidates,
                key=lambda row:
                    parse_date(
                        row.get("end")
                    ),
            )[0]

            new_row = make_derived_row(
                half,
                q1,
            )

            if new_row:
                end = parse_date(
                    new_row.get("end")
                )

                if end not in direct:
                    derived[end] = new_row

    # --------------------------------------------------------
    # 9M - 6M = Q3
    # --------------------------------------------------------

    nine_months = [
        row
        for row in cumulative
        if period_type(row) == "9M"
    ]

    for nine in nine_months:
        nine_start = parse_date(
            nine.get("start")
        )

        nine_end = parse_date(
            nine.get("end")
        )

        if not nine_start or not nine_end:
            continue

        candidates = []

        for half in half_years:
            half_start = parse_date(
                half.get("start")
            )

            half_end = parse_date(
                half.get("end")
            )

            if not half_start or not half_end:
                continue

            if (
                abs(
                    (
                        half_start
                        - nine_start
                    ).days
                )
                <= 3
                and half_end < nine_end
            ):
                candidates.append(
                    half
                )

        if candidates:
            half = sorted(
                candidates,
                key=lambda row:
                    parse_date(
                        row.get("end")
                    ),
                reverse=True,
            )[0]

            new_row = make_derived_row(
                nine,
                half,
            )

            if new_row:
                end = parse_date(
                    new_row.get("end")
                )

                if end not in direct:
                    derived[end] = new_row

    # --------------------------------------------------------
    # FY - 9M = Q4
    # --------------------------------------------------------

    full_years = [
        row
        for row in cumulative
        if period_type(row) == "FY"
    ]

    for full in full_years:
        full_start = parse_date(
            full.get("start")
        )

        full_end = parse_date(
            full.get("end")
        )

        if not full_start or not full_end:
            continue

        candidates = []

        for nine in nine_months:
            nine_start = parse_date(
                nine.get("start")
            )

            nine_end = parse_date(
                nine.get("end")
            )

            if not nine_start or not nine_end:
                continue

            if (
                abs(
                    (
                        nine_start
                        - full_start
                    ).days
                )
                <= 3
                and nine_end < full_end
            ):
                candidates.append(
                    nine
                )

        if candidates:
            nine = sorted(
                candidates,
                key=lambda row:
                    parse_date(
                        row.get("end")
                    ),
                reverse=True,
            )[0]

            new_row = make_derived_row(
                full,
                nine,
            )

            if new_row:
                end = parse_date(
                    new_row.get("end")
                )

                if end not in direct:
                    derived[end] = new_row

    return derived


# ============================================================
# EINHEITLICHE QUARTALSREIHE
# ============================================================

def normalized_quarters(rows):
    """
    Direkte Quartale haben immer Vorrang.

    Nur wenn ein Quartal fehlt, darf ein aus
    kumulierten SEC-Werten abgeleitetes Quartal
    eingesetzt werden.
    """

    direct = direct_quarters(
        rows
    )

    derived = derive_from_cumulative(
        rows
    )

    combined = dict(
        derived
    )

    combined.update(
        direct
    )

    return sorted(
        combined.values(),
        key=lambda row:
            parse_date(
                row.get("end")
            ),
        reverse=True,
    )


# ============================================================
# YOY
# ============================================================

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
            current_end
            - end
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
    quarters = normalized_quarters(
        rows
    )

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
            abs(current_growth)
            >= EXTREME_GROWTH,
    }


# ============================================================
# MARGE
# ============================================================

def margin_metrics(
    revenue_rows,
    operating_income_rows,
):
    revenues = {
        row.get("end"): row
        for row in normalized_quarters(
            revenue_rows
        )
    }

    incomes = {
        row.get("end"): row
        for row in normalized_quarters(
            operating_income_rows
        )
    }

    common_dates = sorted(
        set(revenues.keys())
        & set(incomes.keys()),
        reverse=True,
    )

    margins = []

    for end in common_dates:
        revenue = numeric_value(
            revenues[end]
        )

        income = numeric_value(
            incomes[end]
        )

        if (
            revenue is None
            or income is None
            or revenue == 0
        ):
            continue

        margins.append({
            "end": end,
            "margin":
                income
                / revenue
                * 100.0,
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

def build_fcf_quarters(
    operating_cashflow_rows,
    capex_rows,
):
    ocf = {
        row.get("end"): row
        for row in normalized_quarters(
            operating_cashflow_rows
        )
    }

    capex = {
        row.get("end"): row
        for row in normalized_quarters(
            capex_rows
        )
    }

    common_dates = sorted(
        set(ocf.keys())
        & set(capex.keys()),
        reverse=True,
    )

    results = []

    for end in common_dates:
        ocf_value = numeric_value(
            ocf[end]
        )

        capex_value = numeric_value(
            capex[end]
        )

        if (
            ocf_value is None
            or capex_value is None
        ):
            continue

        results.append({
            "start":
                ocf[end].get("start"),

            "end":
                end,

            "filed":
                ocf[end].get("filed"),

            "form":
                ocf[end].get("form"),

            "val":
                ocf_value
                - abs(capex_value),
        })

    return results


# ============================================================
# SCORES
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


def single_growth_score(
    growth,
):
    if growth is None:
        return None

    if growth >= 25:
        return 4

    if growth >= 10:
        return 3

    if growth >= 0:
        return 2

    if growth >= -10:
        return 1

    return 0


def profit_eps_score(
    profit_growth,
    eps_growth,
):
    if (
        profit_growth is None
        and eps_growth is None
    ):
        return None

    if profit_growth is None:
        return single_growth_score(
            eps_growth
        )

    if eps_growth is None:
        return single_growth_score(
            profit_growth
        )

    opposite_direction = (
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

    divergence = abs(
        profit_growth
        - eps_growth
    )

    if opposite_direction:
        if (
            divergence
            >= PROFIT_EPS_DIVERGENCE
        ):
            return 2

        return 2

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

    if (
        profit_growth >= -10
        and eps_growth >= -10
    ):
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
        points
        / available
        * 4,
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


def normalized_score(
    components,
):
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

    profit_growth = (
        profit_metrics.get(
            "current_growth"
        )
    )

    eps_growth = (
        eps_metrics.get(
            "current_growth"
        )
    )

    if (
        profit_growth is not None
        and eps_growth is not None
        and (
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
    ):
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
    normalized_cik = str(
        cik
    ).zfill(10)

    facts = get_company_facts(
        normalized_cik
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
        normalized_cik
    )

    orders = get_orders_backlog_data(
        normalized_cik
    )


    revenue_metrics = quarter_yoy_growth(
        revenue.get(
            "rows",
            [],
        )
    )

    profit_metrics = quarter_yoy_growth(
        profit_eps.get(
            "profit_rows",
            [],
        )
    )

    eps_metrics = quarter_yoy_growth(
        profit_eps.get(
            "eps_rows",
            [],
        )
    )

    margin_data = margin_metrics(
        revenue.get(
            "rows",
            [],
        ),
        margin_fcf.get(
            "operating_income_rows",
            [],
        ),
    )

    fcf_quarters = build_fcf_quarters(
        margin_fcf.get(
            "operating_cashflow_rows",
            [],
        ),
        margin_fcf.get(
            "capex_rows",
            [],
        ),
    )

    fcf_metrics = quarter_yoy_growth(
        fcf_quarters
    )

    orders_change = orders.get(
        "change"
    )

    orders_score = orders.get(
        "score"
    )

    guidance_score = guidance.get(
        "score"
    )


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
            margin_data[
                "margin_change"
            ],

        fcf_growth=
            fcf_metrics[
                "current_growth"
            ],

        orders_change=
            orders_change,

        guidance_score=
            guidance_score,

        supply_constraint=False,
        pricing_power=False,
    )


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
            margin_data[
                "margin_change"
            ],

        margin_acceleration=
            margin_data[
                "margin_acceleration"
            ],

        fcf_growth=
            fcf_metrics[
                "current_growth"
            ],

        fcf_acceleration=
            fcf_metrics[
                "acceleration"
            ],

        orders_change=
            orders_change,

        orders_acceleration=None,

        guidance_score=
            guidance_score,
    )


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
        margin_data[
            "margin_change"
        ],
        fcf_metrics[
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
            "score":
                revenue_component,
            "max": 4,
        },
        {
            "name": "Profit_EPS",
            "score":
                profit_component,
            "max": 4,
        },
        {
            "name": "Margin_FCF",
            "score":
                margin_component,
            "max": 4,
        },
        {
            "name":
                "Guidance_Orders",
            "score":
                operational_component,
            "max": 4,
        },
        {
            "name":
                "Supply_Demand",
            "score":
                supply_component,
            "max": 4,
        },
    ]


    fundamental_score = normalized_score(
        components
    )

    quality_flags = build_quality_flags(
        revenue_metrics,
        profit_metrics,
        eps_metrics,
        fcf_metrics,
    )


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
            margin_data,

        "fcf":
            fcf_metrics,

        "guidance":
            guidance,

        "orders_backlog":
            orders,

        "supply_demand":
            supply_demand,

        "anomaly":
            anomaly,
    }
