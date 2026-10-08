
"""
Bullwerk Markets - Darvas V5

Einfache Darvas-Box-Erkennung mit stabilen Grenzen.

Ausgabe:
- box_exists
- inside_box
- upper / lower
- breakout_up / breakout_down
- status
- window

Keine Punktebewertung.
"""

import pandas as pd


WINDOWS = (10, 15, 20, 30, 40, 60, 90, 120)

TOUCH_TOLERANCE = 0.025
MIN_TOUCH_GAP = 3
MAX_BOX_WIDTH = 0.35
MAX_NET_CHANGE = 0.12
BREAKOUT_BUFFER = 0.005


def _touch_count(values, level, upper):
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


def _find_box(history):
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

        high_touches = _touch_count(
            data["high"], upper, True
        )
        low_touches = _touch_count(
            data["low"], lower, False
        )

        if high_touches < 2 or low_touches < 2:
            continue

        candidates.append({
            "window": window,
            "upper": upper,
            "lower": lower,
            "high_touches": high_touches,
            "low_touches": low_touches,
        })

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda box: (
            box["window"],
            box["high_touches"] + box["low_touches"],
        ),
    )


def _empty_result():
    return {
        "box_exists": False,
        "inside_box": False,
        "upper": None,
        "lower": None,
        "breakout_up": False,
        "breakout_down": False,
        "status": "KEINE BOX",
        "window": None,
        "box_start": None,
        "box_end": None,
    }


def detect_darvas_box(df):
    """
    Verarbeitet die Kurshistorie chronologisch.

    Erwartet DataFrame mit:
    high, low, close

    Bereits erkannte Boxen bleiben bestehen,
    bis ein Schlusskurs die Box verlaesst.
    """

    result = _empty_result()

    if df is None or len(df) < 11:
        return result

    data = df.copy()
    data.columns = [
        str(col).lower() for col in data.columns
    ]

    required = {"high", "low", "close"}

    if not required.issubset(data.columns):
        raise ValueError(
            "Benoetigte Spalten: high, low, close"
        )

    data = data.dropna(
        subset=["high", "low", "close"]
    ).sort_index()

    if len(data) < 11:
        return result

    active_box = None
    last_closed_box = None

    # Jede Kerze wird in zeitlicher Reihenfolge
    # verarbeitet. Es werden nur Vortage
    # fuer die Box-Erkennung verwendet.
    for i in range(10, len(data)):

        current_close = float(
            data["close"].iloc[i]
        )

        current_date = str(
            data.index[i].date()
        ) if hasattr(
            data.index[i], "date"
        ) else str(data.index[i])

        if active_box is not None:

            upper = active_box["upper"]
            lower = active_box["lower"]

            if current_close > upper * (
                1 + BREAKOUT_BUFFER
            ):
                last_closed_box = {
                    **active_box,
                    "box_end": current_date,
                    "status": "AUSBRUCH OBEN",
                }
                active_box = None

            elif current_close < lower * (
                1 - BREAKOUT_BUFFER
            ):
                last_closed_box = {
                    **active_box,
                    "box_end": current_date,
                    "status": "BOX GESCHEITERT",
                }
                active_box = None

            else:
                continue

        # Eine neue Box nur suchen, wenn
        # aktuell keine aktive Box besteht.
        if active_box is None:

            history = data.iloc[:i]
            candidate = _find_box(history)

            if candidate is not None:

                # Die aktuelle Kerze muss sich
                # innerhalb der neuen Box befinden.
                if (
                    candidate["lower"]
                    <= current_close
                    <= candidate["upper"]
                ):
                    active_box = {
                        **candidate,
                        "box_start": current_date,
                    }

    # Aktive Box hat Vorrang.
    if active_box is not None:

        result.update({
            "box_exists": True,
            "inside_box": True,
            "upper": round(
                active_box["upper"], 4
            ),
            "lower": round(
                active_box["lower"], 4
            ),
            "status": "BOX AKTIV",
            "window": active_box["window"],
            "box_start": active_box["box_start"],
        })

    # Wenn keine aktive Box besteht,
    # letzten abgeschlossenen Zustand melden.
    elif last_closed_box is not None:

        status = last_closed_box["status"]

        result.update({
            "box_exists": True,
            "inside_box": False,
            "upper": round(
                last_closed_box["upper"], 4
            ),
            "lower": round(
                last_closed_box["lower"], 4
            ),
            "breakout_up": (
                status == "AUSBRUCH OBEN"
            ),
            "breakout_down": (
                status == "BOX GESCHEITERT"
            ),
            "status": status,
            "window": last_closed_box["window"],
            "box_start": last_closed_box["box_start"],
            "box_end": last_closed_box["box_end"],
        })

    return result
