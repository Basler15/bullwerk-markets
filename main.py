
"""
Bullwerk Markets - Gesamtscanner V1.1

Drei Qualitaetssaeulen:
- Fundamental: 0-20
- Kursmomentum: 0-20
- Trendqualitaet: 0-20

Qualitaetsscore = Summe / 60 * 100

Darvas und Breakout sind separate Signale.
Fehlende Daten werden nicht als Nullpunkte bewertet.

Neu:
- Score-Historie speichern
- 28-Tage-Scoreveraenderung berechnen
- Fruehbullen als zusaetzliches Signal erkennen
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from scanner.fundamental import get_fundamental_data
from scanner.price_momentum import calculate_price_momentum
from scanner.trend import calculate_trend_quality
from scanner.darvas import detect_darvas_box
from scanner.breakout import detect_breakout

from scanner.score_history import (
    load_history,
    record_scores,
    get_score_change,
    classify_early_bull,
)


WATCHLIST = [
    "AMD", "NVDA", "MSFT", "PLTR", "DELL",
    "INTC", "SNOW", "COHR", "KEYS", "APH",
]

BENCHMARK = "QQQ"
HISTORY_PERIOD = "2y"

OUTPUT_PATH = Path("data/scanner_results.json")
SCORE_HISTORY_PATH = Path("data/score_history.json")

SEC_URL = (
    "https://www.sec.gov/files/company_tickers.json"
)


def get_sec_headers():
    identity = os.environ.get(
        "SEC_USER_AGENT", ""
    ).strip()

    if not identity:
        raise ValueError(
            "SEC_USER_AGENT fehlt. "
            "Bitte in GitHub Actions setzen."
        )

    return {
        "User-Agent": identity,
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }


def load_cik_mapping():
    response = requests.get(
        SEC_URL,
        headers=get_sec_headers(),
        timeout=30,
    )
    response.raise_for_status()

    records = response.json()

    return {
        item["ticker"].upper(): str(
            item["cik_str"]
        ).zfill(10)
        for item in records.values()
    }


def download_prices(symbol):
    data = yf.download(
        symbol,
        period=HISTORY_PERIOD,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise ValueError(
            f"Keine Kursdaten fuer {symbol}"
        )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [
        str(column).lower()
        for column in data.columns
    ]

    required = [
        "open", "high", "low", "close", "volume"
    ]

    if not set(required).issubset(data.columns):
        raise ValueError(
            f"OHLCV-Daten unvollstaendig: {symbol}"
        )

    data = data[required].copy()
    data = data.dropna()
    data = data.sort_index()

    if len(data) < 252:
        raise ValueError(
            f"Zu wenig Handelstage fuer {symbol}: "
            f"{len(data)}"
        )

    return data


def align_prices(stock, benchmark):
    shared = stock.index.intersection(
        benchmark.index
    )

    stock_aligned = stock.loc[shared].copy()
    benchmark_aligned = benchmark.loc[shared].copy()

    if len(shared) < 252:
        raise ValueError(
            "Weniger als 252 gemeinsame Handelstage"
        )

    return stock_aligned, benchmark_aligned


def valid_score(value):
    if isinstance(value, bool):
        return None

    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    if not pd.notna(score):
        return None

    if not 0 <= score <= 20:
        return None

    return round(score, 2)


def evaluate_stock(symbol, cik, benchmark):
    print(f"\nPruefe {symbol} ...")

    stock = download_prices(symbol)

    stock, aligned_benchmark = align_prices(
        stock, benchmark
    )

    fundamental = get_fundamental_data(
        cik=cik,
        symbol=symbol,
    )

    momentum = calculate_price_momentum(
        stock_prices=stock["close"].tolist(),
        benchmark_prices=aligned_benchmark[
            "close"
        ].tolist(),
    )

    trend = calculate_trend_quality(stock)

    f_score = valid_score(
        fundamental.get("fundamental_score")
    )
    m_score = valid_score(
        momentum.get("score")
    )
    t_score = valid_score(
        trend.get("score")
    )

    scores = [f_score, m_score, t_score]

    if any(score is None for score in scores):
        quality_score = None
        classification = "UNVOLLSTAENDIG"
    else:
        quality_score = round(
            sum(scores) / 60 * 100, 1
        )

        if quality_score > 90:
            classification = "BULLENLEADER"
        elif quality_score > 80:
            classification = "WATCH"
        else:
            classification = "BEOBACHTUNG"

    darvas = detect_darvas_box(stock)

    breakout = detect_breakout(
        stock,
        darvas=darvas,
    )

    result = {
        "symbol": symbol,
        "as_of": str(stock.index[-1].date()),
        "close": round(
            float(stock["close"].iloc[-1]), 2
        ),
        "fundamental_score": f_score,
        "momentum_score": m_score,
        "trend_score": t_score,
        "quality_score": quality_score,
        "classification": classification,
        "darvas": darvas,
        "breakout": breakout,
        "relative_strength_gate": momentum.get(
            "rs_gate"
        ),
        "score_change_28d": None,
        "early_bull_status": "HISTORIE FEHLT",
        "score_history_details": None,
    }

    print(
        f"{symbol}: "
        f"Qualitaet={quality_score} "
        f"Status={classification} "
        f"Breakout={breakout.get('signal')}"
    )

    return result


def make_json_safe(value):
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        return make_json_safe(value.item())

    if isinstance(value, float):
        if not pd.notna(value):
            return None

    return value


def update_score_history(results):
    """
    Echte Tagesbewertungen speichern.

    Kein Score wird fuer vergangene Tage erfunden.
    Unvollstaendige Bewertungen werden ignoriert.
    """
    valid_results = [
        item for item in results
        if item["quality_score"] is not None
    ]

    if not valid_results:
        print(
            "Score-Historie: "
            "Keine vollstaendigen Bewertungen."
        )
        return

    # Alle Aktien werden fuer denselben
    # abgeschlossenen Boersentag erwartet.
    dates = {
        item["as_of"]
        for item in valid_results
    }

    if len(dates) != 1:
        raise ValueError(
            "Uneinheitliche Kursdaten-Daten: "
            f"{sorted(dates)}"
        )

    as_of = dates.pop()

    record_scores(
        valid_results,
        path=SCORE_HISTORY_PATH,
        as_of=as_of,
    )

    history = load_history(
        SCORE_HISTORY_PATH
    )

    for item in results:
        if item["quality_score"] is None:
            continue

        change_data = get_score_change(
            history,
            item["symbol"],
            days=28,
            as_of=item["as_of"],
        )

        item["score_history_details"] = change_data

        if change_data is not None:
            item["score_change_28d"] = (
                change_data["change"]
            )

        item["early_bull_status"] = (
            classify_early_bull(change_data)
        )

    print(
        f"\nScore-Historie aktualisiert: {as_of}"
    )
    print(
        f"Historien-Datei: {SCORE_HISTORY_PATH}"
    )


def main():
    print("=" * 65)
    print("BULLWERK MARKETS - GESAMTSCANNER V1.1")
    print("=" * 65)

    cik_mapping = load_cik_mapping()
    benchmark = download_prices(BENCHMARK)

    results = []
    errors = []

    for symbol in WATCHLIST:
        try:
            cik = cik_mapping.get(symbol)

            if cik is None:
                raise ValueError(
                    "SEC-CIK nicht gefunden"
                )

            result = evaluate_stock(
                symbol,
                cik,
                benchmark,
            )

            results.append(result)

        except Exception as exc:
            message = f"{symbol}: {exc}"
            print(f"FEHLER: {message}")
            errors.append(message)

        time.sleep(0.2)

    if not results:
        raise RuntimeError(
            "Keine Aktie erfolgreich ausgewertet."
        )

    update_score_history(results)

    results.sort(
        key=lambda item: (
            item["quality_score"] is not None,
            item["quality_score"]
            if item["quality_score"] is not None
            else -1,
        ),
        reverse=True,
    )

    output = {
        "scanner": "Bullwerk Markets V1.1",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "benchmark": BENCHMARK,
        "stocks": results,
        "errors": errors,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            make_json_safe(output),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("ERGEBNISLISTE")
    print("=" * 65)

    for item in results:
        change = item["score_change_28d"]
        change_text = (
            f"{change:+.1f}"
            if change is not None
            else "noch keine"
        )

        print(
            f"{item['symbol']:6} "
            f"Score: {str(item['quality_score']):6} "
            f"Status: {item['classification']:15} "
            f"28T: {change_text:12} "
            f"Fruehbulle: {item['early_bull_status']}"
        )

    print(
        f"\nErfolgreich: {len(results)}"
        f" | Fehler: {len(errors)}"
    )

    print(f"Ergebnisdatei: {OUTPUT_PATH}")
    print(f"Historie: {SCORE_HISTORY_PATH}")


if __name__ == "__main__":
    main()
