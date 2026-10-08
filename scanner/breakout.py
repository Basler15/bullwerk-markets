
"""
Bullwerk Markets - Breakout & Volume V1

Erkennt:
1. Ausbruch aus einer Darvas-Box
2. Ausbruch ueber die letzte rote Kerze
3. Ausbruch ueber das vorherige 20-Tage-Hoch

Bewertet Signalqualitaet und Volumen (0-20).
Unabhaengig vom Aktienqualitaets-Score (0-100).

Nur abgeschlossene Tageskerzen verwenden.
"""

import math
import pandas as pd


BREAKOUT_BUFFER = 0.005
VOLUME_WINDOW = 20
HIGH_WINDOW = 20
MAX_RED_CANDLE_AGE = 10


def _empty_result():
    return {
        "signal": False,
        "signal_type": "KEIN SIGNAL",
        "trigger": None,
        "score": 0,
        "volume_ratio": None,
        "volume_confirmed": False,
        "darvas_breakout": False,
        "red_candle_breakout": False,
        "high_20_breakout": False,
    }


def detect_breakout(df, darvas=None):
    """
    df: DataFrame mit open, high, low, close, volume.
        Letzte Zeile = zuletzt abgeschlossener Handelstag.

    darvas: optionales Ergebnis von detect_darvas_box().
    """

    result = _empty_result()

    if df is None or len(df) < HIGH_WINDOW + 1:
        return result

    data = df.copy()
    data.columns = [
        str(col).lower() for col in data.columns
    ]

    required = {
        "open", "high", "low", "close", "volume"
    }

    if not required.issubset(data.columns):
        raise ValueError(
            "Benoetigte Spalten: open, high, low, close, volume"
        )

    data = data.dropna(subset=list(required)).sort_index()

    if len(data) < HIGH_WINDOW + 1:
        return result

    current = data.iloc[-1]
    previous = data.iloc[:-1]

    close = float(current["close"])
    volume = float(current["volume"])

    if not all(
        math.isfinite(v) for v in (close, volume)
    ) or close <= 0 or volume < 0:
        return result

    previous_volume = previous["volume"].tail(
        VOLUME_WINDOW
    )

    average_volume = float(previous_volume.mean())

    volume_ratio = (
        volume / average_volume
        if average_volume > 0
        else 0.0
    )

    result["volume_ratio"] = round(
        volume_ratio, 2
    )

    result["volume_confirmed"] = (
        volume_ratio >= 1.5
    )

    signals = []

    # 1. Darvas-Ausbruch
    # Die Darvas-Funktion liefert den Status
    # der zuletzt abgeschlossenen Box.
    if (
        isinstance(darvas, dict)
        and darvas.get("breakout_up") is True
        and darvas.get("upper") is not None
    ):
        upper = float(darvas["upper"])

        # Ein vergangener Ausbruch darf nicht
        # als heutiges Signal erscheinen.
        box_end = darvas.get("box_end")
        current_date = str(data.index[-1])[:10]

        if (
            box_end == current_date
            and close > upper * (1 + BREAKOUT_BUFFER)
        ):
            signals.append(
                ("DARVAS BREAKOUT", upper, 12)
            )
            result["darvas_breakout"] = True

    # 2. Ausbruch ueber letzte rote Kerze
    recent = previous.tail(MAX_RED_CANDLE_AGE)

    red = recent[
        recent["close"] < recent["open"]
    ]

    if not red.empty:
        last_red = red.iloc[-1]
        red_high = float(last_red["high"])

        if red_high > 0:
            previous_close = float(
                previous["close"].iloc[-1]
            )

            crossed = (
                previous_close <= red_high
                and close > red_high * (
                    1 + BREAKOUT_BUFFER
                )
            )

            if crossed:
                signals.append(
                    ("LETZTE ROTE KERZE", red_high, 10)
                )
                result["red_candle_breakout"] = True

    # 3. Neues 20-Tage-Hoch
    high_20 = float(
        previous["high"].tail(HIGH_WINDOW).max()
    )

    previous_close = float(
        previous["close"].iloc[-1]
    )

    if (
        high_20 > 0
        and previous_close <= high_20
        and close > high_20 * (
            1 + BREAKOUT_BUFFER
        )
    ):
        signals.append(
            ("20-TAGE-HOCH", high_20, 10)
        )
        result["high_20_breakout"] = True

    if not signals:
        return result

    # Das staerkste Setup gewinnt.
    # Mehrere Signale werden nicht addiert.
    best = max(signals, key=lambda item: item[2])

    signal_type, trigger, base_score = best

    # Volumenqualitaet: maximal 8 Punkte
    if volume_ratio >= 2.0:
        volume_points = 8
    elif volume_ratio >= 1.5:
        volume_points = 6
    elif volume_ratio >= 1.2:
        volume_points = 4
    elif volume_ratio >= 1.0:
        volume_points = 2
    else:
        volume_points = 0

    result.update({
        "signal": True,
        "signal_type": signal_type,
        "trigger": round(trigger, 4),
        "score": min(
            20, base_score + volume_points
        ),
    })

    return result
