
from typing import Dict, List, Optional

import pandas as pd


# ============================================================
# BULLWERK MARKETS
# TREND QUALITY V1
#
# Säule 3: maximal 20 Punkte
#
# 1. Kurs vs. EMA50                  0-4
# 2. EMA50 vs. EMA200                0-4
# 3. EMA-Steigungen                  0-4
# 4. Higher Highs / Higher Lows      0-4
# 5. 20T / 60T Trendausrichtung      0-4
#
# Die Darvas-Box wird separat in Säule 4 bewertet.
# ============================================================


def pct_change(current, previous):
    if previous is None or previous == 0:
        return 0.0
    return ((current / previous) - 1) * 100.0


# ============================================================
# 1. KURS VS EMA50
# ============================================================

def score_price_vs_ema50(close, ema50):
    distance = pct_change(close, ema50)

    if 2 <= distance <= 10:
        score = 4
    elif 0 <= distance < 2:
        score = 3
    elif 10 < distance <= 20:
        score = 3
    elif -3 <= distance < 0:
        score = 2
    elif -8 <= distance < -3:
        score = 1
    else:
        score = 0

    return score, distance


# ============================================================
# 2. EMA50 VS EMA200
# ============================================================

def score_ema50_vs_ema200(ema50, ema200):
    distance = pct_change(ema50, ema200)

    if distance >= 5:
        score = 4
    elif distance >= 2:
        score = 3
    elif distance >= 0:
        score = 2
    elif distance >= -3:
        score = 1
    else:
        score = 0

    return score, distance


# ============================================================
# 3. EMA-STEIGUNGEN
# Vergleich mit 20 Handelstagen zuvor
# ============================================================

def direction(change):
    if change > 1:
        return "RISING"
    if change < -1:
        return "FALLING"
    return "FLAT"


def score_ema_slope(
    ema50_now,
    ema50_old,
    ema200_now,
    ema200_old,
):
    change50 = pct_change(ema50_now, ema50_old)
    change200 = pct_change(ema200_now, ema200_old)

    dir50 = direction(change50)
    dir200 = direction(change200)

    if dir50 == "RISING" and dir200 == "RISING":
        score = 4
    elif dir50 == "RISING" and dir200 == "FLAT":
        score = 3
    elif dir50 == "RISING" and dir200 == "FALLING":
        score = 2
    elif dir50 in ("FLAT", "FALLING") and dir200 == "RISING":
        score = 1
    else:
        score = 0

    return score, change50, change200, dir50, dir200


# ============================================================
# 4. HIGHER HIGHS / HIGHER LOWS
#
# 63 Handelstage
# Erste 21 Tage vs. letzte 21 Tage
# Mittlere 21 Tage = Puffer
# Toleranz: +/- 2 %
# ============================================================

def structural_direction(new_value, old_value):
    change = pct_change(new_value, old_value)

    if change > 2:
        return "HIGHER"
    if change < -2:
        return "LOWER"
    return "EQUAL"


def score_market_structure(df):
    window = df.iloc[-63:]

    first = window.iloc[:21]
    last = window.iloc[-21:]

    first_high = first["high"].max()
    first_low = first["low"].min()

    last_high = last["high"].max()
    last_low = last["low"].min()

    high_direction = structural_direction(
        last_high,
        first_high,
    )
    low_direction = structural_direction(
        last_low,
        first_low,
    )

    if high_direction == "HIGHER" and low_direction == "HIGHER":
        score = 4
    elif low_direction == "HIGHER" and high_direction == "EQUAL":
        score = 3
    elif high_direction == "EQUAL" and low_direction == "EQUAL":
        score = 2
    elif high_direction == "LOWER" and low_direction in ("EQUAL", "HIGHER"):
        score = 1
    else:
        score = 0

    return (
        score,
        high_direction,
        low_direction,
        pct_change(last_high, first_high),
        pct_change(last_low, first_low),
    )


# ============================================================
# 5. 20T / 60T TRENDAUSRICHTUNG
# Toleranz: +/- 2 %
# ============================================================

def trend_direction(value):
    if value > 2:
        return "UP"
    if value < -2:
        return "DOWN"
    return "SIDEWAYS"


def score_trend_alignment(return20, return60):
    dir20 = trend_direction(return20)
    dir60 = trend_direction(return60)

    if dir20 == "UP" and dir60 == "UP":
        score = 4
    elif dir20 == "UP" and dir60 == "DOWN":
        score = 3
    elif dir20 == "SIDEWAYS" and dir60 == "UP":
        score = 2
    elif dir20 == "DOWN" and dir60 == "UP":
        score = 1
    else:
        score = 0

    return score, dir20, dir60


# ============================================================
# HAUPTBERECHNUNG
#
# Eingabe:
# DataFrame mit Spalten:
# close, high, low
#
# Mindestens 252 Handelstage
# ============================================================

def calculate_trend_quality(df: pd.DataFrame) -> Dict:
    required_columns = {"close", "high", "low"}

    if not required_columns.issubset(df.columns):
        raise ValueError(
            "DataFrame benötigt close, high und low."
        )

    if len(df) < 252:
        raise ValueError(
            "Mindestens 252 Handelstage erforderlich."
        )

    df = df.copy().dropna(subset=["close", "high", "low"])

    if len(df) < 252:
        raise ValueError(
            "Zu wenige gültige Handelstage."
        )

    close = df["close"]

    ema50 = close.ewm(
        span=50,
        adjust=False,
    ).mean()

    ema200 = close.ewm(
        span=200,
        adjust=False,
    ).mean()

    current_close = close.iloc[-1]
    current_ema50 = ema50.iloc[-1]
    current_ema200 = ema200.iloc[-1]

    old_ema50 = ema50.iloc[-21]
    old_ema200 = ema200.iloc[-21]

    score1, distance50 = score_price_vs_ema50(
        current_close,
        current_ema50,
    )

    score2, distance200 = score_ema50_vs_ema200(
        current_ema50,
        current_ema200,
    )

    (
        score3,
        ema50_change,
        ema200_change,
        ema50_direction,
        ema200_direction,
    ) = score_ema_slope(
        current_ema50,
        old_ema50,
        current_ema200,
        old_ema200,
    )

    (
        score4,
        high_direction,
        low_direction,
        high_change,
        low_change,
    ) = score_market_structure(df)

    return20 = pct_change(
        close.iloc[-1],
        close.iloc[-21],
    )

    return60 = pct_change(
        close.iloc[-1],
        close.iloc[-61],
    )

    score5, trend20, trend60 = score_trend_alignment(
        return20,
        return60,
    )

    total = score1 + score2 + score3 + score4 + score5

    return {
        "score": total,
        "max_score": 20,
        "components": {
            "price_vs_ema50": score1,
            "ema50_vs_ema200": score2,
            "ema_slopes": score3,
            "market_structure": score4,
            "trend_alignment": score5,
        },
        "metrics": {
            "close": float(current_close),
            "ema50": float(current_ema50),
            "ema200": float(current_ema200),
            "price_distance_ema50": float(distance50),
            "ema50_distance_ema200": float(distance200),
            "ema50_20t_change": float(ema50_change),
            "ema200_20t_change": float(ema200_change),
            "ema50_direction": ema50_direction,
            "ema200_direction": ema200_direction,
            "high_structure": high_direction,
            "low_structure": low_direction,
            "high_change": float(high_change),
            "low_change": float(low_change),
            "return20": float(return20),
            "return60": float(return60),
            "trend20": trend20,
            "trend60": trend60,
        },
    }
