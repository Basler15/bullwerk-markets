from typing import Dict, List, Optional


# ============================================================
# Bullwerk Markets
# Price & Relative Strength Momentum V2
#
# Säule 2 des Bullwerk Scores
#
# 1. Relative Stärke vs. QQQ        0-5
# 2. RS-Beschleunigung              0-5
# 3. Momentum 1-3 Monate            0-4
# 4. Momentum 3-6 Monate            0-3
# 5. Nähe zum 52-Wochen-Hoch        0-3
#
# Gesamt                              20
# ============================================================


def percent_change(
    current: float,
    previous: float,
) -> Optional[float]:

    if current is None or previous is None:
        return None

    if previous == 0:
        return None

    return ((current / previous) - 1) * 100.0


def price_return(
    prices: List[float],
    periods_back: int,
) -> Optional[float]:

    if not prices:
        return None

    if len(prices) <= periods_back:
        return None

    return percent_change(
        prices[-1],
        prices[-1 - periods_back],
    )


def window_return(
    prices: List[float],
    start_back: int,
    end_back: int,
) -> Optional[float]:
    """
    Rendite eines historischen Fensters.

    Beispiel:
    start_back = 63
    end_back   = 21

    misst die Rendite vom Zeitpunkt vor
    63 Handelstagen bis vor 21 Handelstagen.
    """

    if not prices:
        return None

    if start_back <= end_back:
        return None

    if len(prices) <= start_back:
        return None

    start_price = prices[-1 - start_back]
    end_price = prices[-1 - end_back]

    return percent_change(
        end_price,
        start_price,
    )


def relative_strength_return(
    stock_prices: List[float],
    benchmark_prices: List[float],
    periods_back: int,
) -> Optional[float]:

    stock_return = price_return(
        stock_prices,
        periods_back,
    )

    benchmark_return = price_return(
        benchmark_prices,
        periods_back,
    )

    if stock_return is None or benchmark_return is None:
        return None

    return stock_return - benchmark_return


def calculate_rs_metrics(
    stock_prices: List[float],
    benchmark_prices: List[float],
) -> Dict:

    rs_1m = relative_strength_return(
        stock_prices,
        benchmark_prices,
        21,
    )

    rs_3m = relative_strength_return(
        stock_prices,
        benchmark_prices,
        63,
    )

    rs_6m = relative_strength_return(
        stock_prices,
        benchmark_prices,
        126,
    )

    # --------------------------------------------------------
    # Echte RS-Beschleunigung:
    #
    # aktuelle 21 Handelstage
    # gegen
    # vorherige 42 Handelstage.
    #
    # Damit messen wir nicht nur Stärke,
    # sondern ob die Outperformance gerade zunimmt.
    # --------------------------------------------------------

    stock_previous = window_return(
        stock_prices,
        63,
        21,
    )

    benchmark_previous = window_return(
        benchmark_prices,
        63,
        21,
    )

    previous_rs = None

    if (
        stock_previous is not None
        and benchmark_previous is not None
    ):
        previous_rs = (
            stock_previous
            - benchmark_previous
        )

    rs_acceleration = None

    if (
        rs_1m is not None
        and previous_rs is not None
    ):
        rs_acceleration = (
            rs_1m
            - previous_rs
        )

    return {
        "rs_1m": rs_1m,
        "rs_3m": rs_3m,
        "rs_6m": rs_6m,
        "previous_rs": previous_rs,
        "rs_acceleration": rs_acceleration,
    }


# ============================================================
# 1. RELATIVE STÄRKE VS. QQQ
# Maximal 5 Punkte
# ============================================================

def score_relative_strength(
    rs_3m: Optional[float],
) -> int:

    if rs_3m is None:
        return 0

    if rs_3m >= 15:
        return 5

    if rs_3m >= 10:
        return 4

    if rs_3m >= 5:
        return 3

    if rs_3m >= 0:
        return 2

    if rs_3m >= -5:
        return 1

    return 0


# ============================================================
# 2. RS-BESCHLEUNIGUNG
# Maximal 5 Punkte
# ============================================================

def score_rs_acceleration(
    acceleration: Optional[float],
) -> int:

    if acceleration is None:
        return 0

    if acceleration >= 10:
        return 5

    if acceleration >= 6:
        return 4

    if acceleration >= 3:
        return 3

    if acceleration >= 0:
        return 2

    if acceleration >= -3:
        return 1

    return 0


# ============================================================
# 3. MOMENTUM 1-3 MONATE
# Maximal 4 Punkte
# ============================================================

def score_short_momentum(
    return_1m: Optional[float],
    return_3m: Optional[float],
) -> int:

    if return_1m is None or return_3m is None:
        return 0

    if (
        return_1m >= 10
        and return_3m >= 20
    ):
        return 4

    if (
        return_1m >= 5
        and return_3m >= 10
    ):
        return 3

    if (
        return_1m >= 0
        and return_3m >= 5
    ):
        return 2

    if (
        return_1m >= 0
        or return_3m >= 0
    ):
        return 1

    return 0


# ============================================================
# 4. MOMENTUM 3-6 MONATE
# Maximal 3 Punkte
# ============================================================

def score_medium_momentum(
    return_3m: Optional[float],
    return_6m: Optional[float],
) -> int:

    if return_3m is None or return_6m is None:
        return 0

    if (
        return_3m >= 15
        and return_6m >= 30
    ):
        return 3

    if (
        return_3m >= 5
        and return_6m >= 15
    ):
        return 2

    if (
        return_3m >= 0
        and return_6m >= 0
    ):
        return 1

    return 0


# ============================================================
# 5. NÄHE ZUM 52-WOCHEN-HOCH
# Maximal 3 Punkte
# ============================================================

def distance_from_52w_high(
    prices: List[float],
) -> Optional[float]:

    if not prices:
        return None

    lookback = prices[-252:]

    if not lookback:
        return None

    high_52w = max(lookback)

    if high_52w == 0:
        return None

    current = prices[-1]

    return (
        (current / high_52w) - 1
    ) * 100.0


def score_52w_high(
    distance: Optional[float],
) -> int:

    if distance is None:
        return 0

    if distance >= -2:
        return 3

    if distance >= -5:
        return 2

    if distance >= -10:
        return 1

    return 0


# ============================================================
# HAUPTBERECHNUNG
# ============================================================

def calculate_price_momentum(
    stock_prices: List[float],
    benchmark_prices: List[float],
) -> Dict:

    return_1m = price_return(
        stock_prices,
        21,
    )

    return_3m = price_return(
        stock_prices,
        63,
    )

    return_6m = price_return(
        stock_prices,
        126,
    )

    rs = calculate_rs_metrics(
        stock_prices,
        benchmark_prices,
    )

    high_distance = distance_from_52w_high(
        stock_prices
    )

    rs_score = score_relative_strength(
        rs["rs_3m"]
    )

    rs_acceleration_score = score_rs_acceleration(
        rs["rs_acceleration"]
    )

    short_score = score_short_momentum(
        return_1m,
        return_3m,
    )

    medium_score = score_medium_momentum(
        return_3m,
        return_6m,
    )

    high_score = score_52w_high(
        high_distance
    )

    raw_score = (
        rs_score
        + rs_acceleration_score
        + short_score
        + medium_score
        + high_score
    )

    # --------------------------------------------------------
    # BULLWERK RS-GATE
    #
    # Eine Aktie darf nicht nur durch absolutes Momentum
    # oder Nähe zum Hoch zum Leader werden, wenn sie den
    # Nasdaq/QQQ nicht schlägt.
    #
    # Leichte Underperformance:
    # maximal 14/20.
    #
    # Deutliche Underperformance <= -5 Prozentpunkte:
    # maximal 10/20.
    # --------------------------------------------------------

    final_score = raw_score
    rs_gate = None

    if rs["rs_3m"] is not None:

        if rs["rs_3m"] <= -5:
            final_score = min(
                final_score,
                10,
            )
            rs_gate = "STRONG_UNDERPERFORMANCE"

        elif rs["rs_3m"] < 0:
            final_score = min(
                final_score,
                14,
            )
            rs_gate = "UNDERPERFORMANCE"

    return {
        "score": final_score,
        "raw_score": raw_score,
        "max_score": 20,

        "components": {
            "relative_strength": rs_score,
            "rs_acceleration": rs_acceleration_score,
            "momentum_1_3m": short_score,
            "momentum_3_6m": medium_score,
            "high_52w": high_score,
        },

        "metrics": {
            "return_1m": return_1m,
            "return_3m": return_3m,
            "return_6m": return_6m,

            "rs_1m": rs["rs_1m"],
            "rs_3m": rs["rs_3m"],
            "rs_6m": rs["rs_6m"],

            "previous_rs": rs["previous_rs"],
            "rs_acceleration": rs["rs_acceleration"],

            "distance_52w_high": high_distance,
        },

        "rs_gate": rs_gate,
    }
