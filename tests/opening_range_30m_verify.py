"""Isolated historical 30-minute opening-range verification; does not alter Bullwerk scanner."""
from datetime import time
import sys
import pandas as pd
import yfinance as yf

SYMBOLS = ("PLTR", "NVDA")
NY = "America/New_York"
EXPECTED = [time(9, 30), time(9, 35), time(9, 40), time(9, 45), time(9, 50), time(9, 55)]

def verify(symbol):
    raw = yf.download(symbol, period="1mo", interval="5m", auto_adjust=True,
                      prepost=False, progress=False, threads=False)
    if raw.empty:
        raise RuntimeError(f"{symbol}: no 5m data")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    if raw.index.tz is None:
        raise RuntimeError(f"{symbol}: missing timezone")
    raw = raw.tz_convert(NY).sort_index()
    results = []
    for date, day in raw.groupby(raw.index.date):
        day = day.between_time("09:30", "15:55")
        opening = day.between_time("09:30", "09:55")
        times = list(opening.index.time)
        if times != EXPECTED or opening[["Open", "High", "Low", "Close", "Volume"]].isna().any().any():
            continue
        high = float(opening["High"].max())
        low = float(opening["Low"].min())
        if high <= low:
            raise RuntimeError(f"{symbol} {date}: invalid opening range")
        after = day.between_time("10:00", "15:55")
        # Strict: only completed historical 5-minute candles, after the opening window.
        # This is a structural test, NOT an executable trading signal.
        long_breaks = after[after["Close"] > high]
        short_breaks = after[after["Close"] < low]
        first_long = str(long_breaks.index[0].time()) if not long_breaks.empty else "-"
        first_short = str(short_breaks.index[0].time()) if not short_breaks.empty else "-"
        results.append((str(date), high, low, first_long, first_short))
    if len(results) < 10:
        raise RuntimeError(f"{symbol}: only {len(results)} complete opening ranges, need 10")
    print(f"\n=== {symbol}: last 10 valid US sessions (New York time) ===")
    print("Date         OR High     OR Low      First 5m close > high   First 5m close < low")
    for date, high, low, lng, sht in results[-10:]:
        print(f"{date}   {high:9.2f}   {low:9.2f}   {lng:>21}   {sht:>20}")
    print(f"PASS: 6 exact opening candles on each of {len(results[-10:])} sessions")

if __name__ == "__main__":
    try:
        for symbol in SYMBOLS:
            verify(symbol)
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
