
"""
Bullwerk Markets – Darvas-Box-Erkennung

Ergebnisse:
- box_exists: True / False
- inside_box: True / False
- upper: obere Box-Grenze
- lower: untere Box-Grenze
- breakout_up: True / False
- breakout_down: True / False

Keine Score-Berechnung.
"""

import pandas as pd


WINDOWS = (10, 15, 20, 30, 40, 60, 90, 120)
TOUCH_TOLERANCE = 0.025
MIN_TOUCH_GAP = 3
MAX_BOX_WIDTH = 0.35
MAX_NET_CHANGE = 0.12
BREAKOUT_BUFFER = 0.005


def _touch_count(values, level, upper):
    """Zaehlt zeitlich getrennte Beruehrungen einer Grenze."""
    count = 0
    last_touch = -MIN_TOUCH_GAP

    for i, value in enumerate(values):
        if upper:
            touched = value >= level * (1 - TOUCH_TOLERANCE)
        else:
            touched = value <= level * (1 + TOUCH_TOLERANCE)

        if touched and i - last_touch >= MIN_TOUCH_GAP:
            count += 1
            last_touch = i

    return count


def _find_boxes(history):
    """Sucht bestaetigte Boxen in historischen Kursdaten."""
    candidates = []

    for window in WINDOWS:
        if len(history) < window:
            continue

        data = history.iloc[-window:]

        upper = float(data["high"].max())
        lower = float(data["low"].min())

        if lower <= 0:
            continue

        width = (upper - lower) / lower
        if width > MAX_BOX_WIDTH:
            continue

        first_close = float(data["close"].iloc[0])
        last_close = float(data["close"].iloc[-1])

        if first_close <= 0:
            continue

        net_change = abs(last_close / first_close - 1)
        if net_change > MAX_NET_CHANGE:
            continue

        highs = _touch_count(data["high"], upper, True)
        lows = _touch_count(data["low"], lower, False)

        if highs < 2 or lows < 2:
            continue

        candidates.append({
            "window": window,
            "upper": upper,
            "lower": lower,
            "high_touches": highs,
            "low_touches": lows,
        })

    return candidates


def detect_darvas_box(df):
    """
    Erkennt eine Darvas-Box anhand von OHLC-Daten.

    Erwartet ein DataFrame mit:
    high, low, close

    Die letzte Kerze wird nur zur aktuellen
    Positionspruefung verwendet.
    """

    result = {
        "box_exists": False,
        "inside_box": False,
        "upper": None,
        "lower": None,
        "breakout_up": False,
        "breakout_down": False,
        "window": None,
    }

    if df is None or len(df) < 11:
        return result

    data = df.copy()
    data.columns = [str(c).lower() for c in data.columns]

    required = {"high", "low", "close"}
    if not required.issubset(data.columns):
        raise ValueError("Benötigte Spalten: high, low, close")

    data = data.dropna(subset=["high", "low", "close"])

    if len(data) < 11:
        return result

    current_close = float(data["close"].iloc[-1])

    # Die Box wird aus abgeschlossenen Vortagen
    # gebildet, ohne die aktuelle Kerze.
    history = data.iloc[:-1]

    candidates = _find_boxes(history)

    if not candidates:
        return result

    # Bevorzugt laengere bestaetigte Boxen.
    selected = max(
        candidates,
        key=lambda box: (
            box["window"],
            box["high_touches"] + box["low_touches"],
        ),
    )

    upper = selected["upper"]
    lower = selected["lower"]

    result["box_exists"] = True
    result["upper"] = round(upper, 4)
    result["lower"] = round(lower, 4)
    result["window"] = selected["window"]

    result["inside_box"] = lower <= current_close <= upper

    result["breakout_up"] = (
        current_close > upper * (1 + BREAKOUT_BUFFER)
    )

    result["breakout_down"] = (
        current_close < lower * (1 - BREAKOUT_BUFFER)
    )

    return result
