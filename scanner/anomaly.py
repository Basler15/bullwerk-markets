# Bullwerk Markets - Fundamental Anomaly Modul
#
# Ziel:
# Ungewöhnliche fundamentale Beschleunigung früh erkennen.
#
# ANOMALY ist KEIN Bestandteil des normalen 0-20
# Fundamental-Scores.
#
# Kernregel für ANOMALY HIGH:
#
# - mindestens 3 starke Signale
# - mindestens 1 Signal aus:
#       Revenue / Demand / Orders
# - mindestens 1 Signal aus:
#       Profit / EPS / Margin / FCF
# - Beschleunigung wird zusätzlich berücksichtigt
#
# Ein einzelner extremer Wert reicht niemals aus.


def is_at_least(value, threshold):
    if value is None:
        return False

    return value >= threshold


def get_anomaly_data(
    revenue_growth=None,
    revenue_acceleration=None,
    profit_growth=None,
    profit_acceleration=None,
    eps_growth=None,
    eps_acceleration=None,
    margin_change=None,
    margin_acceleration=None,
    fcf_growth=None,
    fcf_acceleration=None,
    orders_change=None,
    orders_acceleration=None,
    guidance_score=None,
):
    """
    Erkennt ungewöhnliche fundamentale Beschleunigung.

    Rückgabe:
        level:
            NONE
            WATCH
            MEDIUM
            HIGH

        strong_signal_count
        demand_signal_count
        profit_signal_count
        acceleration_count
        signals
    """

    signals = {}


    # ========================================================
    # 1. DEMAND / REVENUE / ORDERS
    # ========================================================

    signals["revenue_growth"] = is_at_least(
        revenue_growth,
        20.0,
    )

    signals["revenue_acceleration"] = is_at_least(
        revenue_acceleration,
        5.0,
    )

    signals["orders_growth"] = is_at_least(
        orders_change,
        15.0,
    )

    signals["orders_acceleration"] = is_at_least(
        orders_acceleration,
        5.0,
    )


    # ========================================================
    # 2. PROFIT / EPS
    # ========================================================

    signals["profit_growth"] = is_at_least(
        profit_growth,
        25.0,
    )

    signals["profit_acceleration"] = is_at_least(
        profit_acceleration,
        10.0,
    )

    signals["eps_growth"] = is_at_least(
        eps_growth,
        25.0,
    )

    signals["eps_acceleration"] = is_at_least(
        eps_acceleration,
        10.0,
    )


    # ========================================================
    # 3. MARGINS
    # ========================================================

    signals["margin_expansion"] = is_at_least(
        margin_change,
        1.5,
    )

    signals["margin_acceleration"] = is_at_least(
        margin_acceleration,
        0.5,
    )


    # ========================================================
    # 4. FREE CASHFLOW
    # ========================================================

    signals["fcf_growth"] = is_at_least(
        fcf_growth,
        25.0,
    )

    signals["fcf_acceleration"] = is_at_least(
        fcf_acceleration,
        10.0,
    )


    # ========================================================
    # 5. GUIDANCE
    # ========================================================

    signals["guidance_strong"] = (
        guidance_score is not None
        and guidance_score >= 3
    )


    # ========================================================
    # SIGNALGRUPPEN
    # ========================================================

    demand_keys = [
        "revenue_growth",
        "revenue_acceleration",
        "orders_growth",
        "orders_acceleration",
    ]

    profit_keys = [
        "profit_growth",
        "profit_acceleration",
        "eps_growth",
        "eps_acceleration",
        "margin_expansion",
        "margin_acceleration",
        "fcf_growth",
        "fcf_acceleration",
    ]

    acceleration_keys = [
        "revenue_acceleration",
        "orders_acceleration",
        "profit_acceleration",
        "eps_acceleration",
        "margin_acceleration",
        "fcf_acceleration",
    ]


    demand_signal_count = sum(
        bool(signals[key])
        for key in demand_keys
    )

    profit_signal_count = sum(
        bool(signals[key])
        for key in profit_keys
    )

    acceleration_count = sum(
        bool(signals[key])
        for key in acceleration_keys
    )

    strong_signal_count = sum(
        bool(value)
        for value in signals.values()
    )


    # ========================================================
    # CROSS-GROUP CONFIRMATION
    # ========================================================

    has_demand_confirmation = (
        demand_signal_count >= 1
    )

    has_profit_confirmation = (
        profit_signal_count >= 1
    )

    has_cross_group_confirmation = (
        has_demand_confirmation
        and has_profit_confirmation
    )


    # ========================================================
    # ANOMALY HIGH
    # ========================================================
    #
    # Mindestens:
    #
    # 3 starke Signale
    # + Demand/Orders
    # + Profit/Margin/FCF
    #
    # Damit kann ein einzelner Ausreißer
    # niemals HIGH erzeugen.
    # ========================================================

    if (
        strong_signal_count >= 3
        and has_cross_group_confirmation
    ):
        level = "HIGH"

        reason = (
            "Mehrere starke fundamentale Veränderungen "
            "aus Nachfrage und Profitabilität bestätigen "
            "eine ungewöhnliche Entwicklung."
        )


    # ========================================================
    # ANOMALY MEDIUM
    # ========================================================

    elif (
        strong_signal_count >= 2
        and has_cross_group_confirmation
    ):
        level = "MEDIUM"

        reason = (
            "Mehrere Fundamentalbereiche verbessern sich, "
            "aber die Bestätigung für ANOMALY HIGH "
            "reicht noch nicht aus."
        )


    # ========================================================
    # ANOMALY WATCH
    # ========================================================

    elif strong_signal_count >= 1:
        level = "WATCH"

        reason = (
            "Ein auffälliges Fundamentalsignal wurde erkannt, "
            "aber es fehlt noch die Bestätigung durch "
            "weitere Bereiche."
        )


    # ========================================================
    # KEINE ANOMALIE
    # ========================================================

    else:
        level = "NONE"

        reason = (
            "Keine außergewöhnliche fundamentale "
            "Beschleunigung erkannt."
        )


    # ========================================================
    # BESCHLEUNIGUNGS-HINWEIS
    # ========================================================

    if (
        level == "HIGH"
        and acceleration_count >= 2
    ):
        reason += (
            " Zusätzlich beschleunigen mehrere "
            "Kennzahlen gegenüber den Vorperioden."
        )


    # ========================================================
    # AUSGABE
    # ========================================================

    active_signals = [
        key
        for key, value in signals.items()
        if value
    ]

    return {
        "level": level,
        "reason": reason,

        "strong_signal_count":
            strong_signal_count,

        "demand_signal_count":
            demand_signal_count,

        "profit_signal_count":
            profit_signal_count,

        "acceleration_count":
            acceleration_count,

        "has_cross_group_confirmation":
            has_cross_group_confirmation,

        "active_signals":
            active_signals,

        "signals":
            signals,
    }
