
# Bullwerk Markets - Score-Historie V1
# Speichert echte Scanner-Bewertungen nach Datum.
# Keine rückwirkend erfundenen Fundamentaldaten.

import json
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_PATH = Path("data/score_history.json")


def load_history(path=DEFAULT_PATH):
    """Gespeicherte Bewertungen laden."""
    path = Path(path)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        history = json.load(file)

    if not isinstance(history, dict):
        raise ValueError("Ungueltiges Score-Historienformat")

    return history


def save_history(history, path=DEFAULT_PATH):
    """Historie dauerhaft als JSON-Datei speichern."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

    temporary.replace(path)


def record_scores(stocks, path=DEFAULT_PATH, as_of=None):
    """
    Tagesbewertung speichern.

    Erwartet eine Liste mit:
    symbol, quality_score

    Mehrere Läufe am selben Tag ersetzen den Tageswert.
    """
    history = load_history(path)
    today = as_of or date.today().isoformat()

    date.fromisoformat(today)

    for stock in stocks:
        symbol = str(stock["symbol"]).upper().strip()
        score = stock.get("quality_score")

        if not symbol or score is None:
            continue

        score = float(score)

        if not 0 <= score <= 100:
            raise ValueError(
                f"Ungueltiger Score fuer {symbol}: {score}"
            )

        entries = history.setdefault(symbol, {})
        entries[today] = round(score, 2)

    save_history(history, path)
    return history


def get_score_change(history, symbol, days=28, as_of=None):
    """
    Score-Veränderung gegenüber etwa vier Wochen.

    Verwendet nur tatsächlich gespeicherte Daten.
    Fehlt ein ausreichend alter Vergleichswert,
    wird None zurückgegeben.
    """
    today = date.fromisoformat(
        as_of or date.today().isoformat()
    )
    target = today - timedelta(days=days)

    entries = history.get(symbol.upper(), {})
    current = entries.get(today.isoformat())

    if current is None:
        return None

    candidates = []

    for day_string, score in entries.items():
        day = date.fromisoformat(day_string)

        if day <= target:
            candidates.append((day, score))

    if not candidates:
        return None

    previous_day, previous_score = max(candidates)

    return {
        "current_score": current,
        "previous_score": previous_score,
        "previous_date": previous_day.isoformat(),
        "change": round(current - previous_score, 2),
        "period_days": (today - previous_day).days,
    }


def classify_early_bull(change_data):
    """
    Vorläufige Früherkennung.
    Schwellenwerte werden später mit echten
    historischen Beobachtungen überprüft.
    """
    if change_data is None:
        return "HISTORIE FEHLT"

    change = change_data["change"]
    current = change_data["current_score"]

    if change >= 8 and current >= 75:
        return "FRUEHBULLE"

    if change >= 4 and current >= 70:
        return "VERBESSERT SICH"

    if change <= -8:
        return "VERSCHLECHTERUNG"

    return "STABIL"


if __name__ == "__main__":
    print("Bullwerk Score-Historie V1 bereit")
