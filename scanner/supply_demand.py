# Bullwerk Markets - Supply / Demand Dynamics & Pricing Power
#
# Ziel:
# Nicht "Knappheit" allein bewerten.
#
# Bullwerk sucht eine wirtschaftliche Wirkungskette:
#
# Nachfrage / Orders steigen
#        ↓
# Angebot / Kapazität bleibt begrenzt
#        ↓
# Pricing Power
#        ↓
# Margen / FCF verbessern sich
#        ↓
# Guidance bestätigt die Entwicklung
#
# Das Modul arbeitet zunächst mit Signalen aus den
# bereits vorhandenen Bullwerk-Fundamentalmodulen.


def signal_positive(value, threshold):
    """
    Prüft, ob eine Veränderungsrate ausreichend positiv ist.
    """

    if value is None:
        return False

    return value >= threshold


def signal_strong(value, threshold):
    """
    Prüft auf besonders starke Veränderung.
    """

    if value is None:
        return False

    return value >= threshold


def get_supply_demand_score(
    revenue_growth=None,
    revenue_acceleration=None,
    margin_change=None,
    fcf_growth=None,
    orders_change=None,
    guidance_score=None,
    supply_constraint=False,
    pricing_power=False,
):
    """
    Bewertet Supply/Demand Dynamics.

    Maximal 4 Punkte.

    WICHTIG:
    Ein einzelnes starkes Signal reicht NICHT
    für einen hohen Bullwerk-Score.
    """

    signals = {
        "demand_growth": False,
        "demand_acceleration": False,
        "orders_strength": False,
        "supply_constraint": bool(
            supply_constraint
        ),
        "pricing_power": bool(
            pricing_power
        ),
        "margin_confirmation": False,
        "fcf_confirmation": False,
        "guidance_confirmation": False,
    }

    # --------------------------------------------------------
    # Nachfrage
    # --------------------------------------------------------

    if signal_positive(
        revenue_growth,
        10.0,
    ):
        signals[
            "demand_growth"
        ] = True

    if signal_positive(
        revenue_acceleration,
        3.0,
    ):
        signals[
            "demand_acceleration"
        ] = True

    # --------------------------------------------------------
    # Orders / Backlog
    # --------------------------------------------------------

    if signal_positive(
        orders_change,
        5.0,
    ):
        signals[
            "orders_strength"
        ] = True

    # --------------------------------------------------------
    # Wirtschaftliche Bestätigung
    # --------------------------------------------------------

    if signal_positive(
        margin_change,
        0.5,
    ):
        signals[
            "margin_confirmation"
        ] = True

    if signal_positive(
        fcf_growth,
        10.0,
    ):
        signals[
            "fcf_confirmation"
        ] = True

    if (
        guidance_score is not None
        and guidance_score >= 2
    ):
        signals[
            "guidance_confirmation"
        ] = True

    # --------------------------------------------------------
    # Gruppen
    # --------------------------------------------------------

    demand_signals = sum([
        signals["demand_growth"],
        signals["demand_acceleration"],
        signals["orders_strength"],
    ])

    market_power_signals = sum([
        signals["supply_constraint"],
        signals["pricing_power"],
    ])

    financial_confirmation = sum([
        signals["margin_confirmation"],
        signals["fcf_confirmation"],
        signals["guidance_confirmation"],
    ])

    total_signals = (
        demand_signals
        + market_power_signals
        + financial_confirmation
    )

    # --------------------------------------------------------
    # BULLWERK SCORE
    # --------------------------------------------------------
    #
    # 4/4:
    # Nachfrage + Angebots-/Pricing-Signal +
    # finanzielle Bestätigung
    #
    # 3/4:
    # klare Nachfrage + mehrere Bestätigungen
    #
    # 2/4:
    # positive Entwicklung, aber Kette noch
    # nicht vollständig
    #
    # 1/4:
    # erstes interessantes Signal
    #
    # 0/4:
    # keine belastbare Supply/Demand-Dynamik
    # --------------------------------------------------------

    if (
        demand_signals >= 1
        and market_power_signals >= 1
        and financial_confirmation >= 2
        and total_signals >= 5
    ):
        score = 4
        status = "STRONG"
        reason = (
            "Nachfrage, Angebots-/Pricing-Dynamik "
            "und finanzielle Entwicklung bestätigen "
            "sich gegenseitig."
        )

    elif (
        demand_signals >= 2
        and financial_confirmation >= 2
    ):
        score = 3
        status = "POSITIVE"
        reason = (
            "Starke Nachfrage mit mehreren "
            "fundamentalen Bestätigungen."
        )

    elif (
        demand_signals >= 1
        and financial_confirmation >= 1
    ):
        score = 2
        status = "DEVELOPING"
        reason = (
            "Positive Supply/Demand-Entwicklung, "
            "aber die Wirkungskette ist noch "
            "nicht vollständig bestätigt."
        )

    elif total_signals >= 1:
        score = 1
        status = "EARLY"
        reason = (
            "Erstes positives Signal vorhanden, "
            "aber noch keine ausreichende Bestätigung."
        )

    else:
        score = 0
        status = "NONE"
        reason = (
            "Keine belastbare positive "
            "Supply/Demand-Dynamik erkannt."
        )

    return {
        "score": score,
        "status": status,
        "reason": reason,

        "signals": signals,

        "demand_signals":
            demand_signals,

        "market_power_signals":
            market_power_signals,

        "financial_confirmation":
            financial_confirmation,

        "total_signals":
            total_signals,
    }


def get_supply_demand_data(
    revenue_growth=None,
    revenue_acceleration=None,
    margin_change=None,
    fcf_growth=None,
    orders_change=None,
    guidance_score=None,
    supply_constraint=False,
    pricing_power=False,
):
    """
    Öffentliche Funktion für den Bullwerk Scanner.

    Die Funktion bekommt später automatisch die
    Ergebnisse der anderen Fundamentalmodule.
    """

    return get_supply_demand_score(
        revenue_growth=
            revenue_growth,

        revenue_acceleration=
            revenue_acceleration,

        margin_change=
            margin_change,

        fcf_growth=
            fcf_growth,

        orders_change=
            orders_change,

        guidance_score=
            guidance_score,

        supply_constraint=
            supply_constraint,

        pricing_power=
            pricing_power,
    )
