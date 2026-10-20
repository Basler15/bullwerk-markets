"""Isolated 5-minute data availability test. Does not touch Bullwerk scanner files."""
from datetime import datetime, timezone
import sys
import pandas as pd
import yfinance as yf

SYMBOLS = ("PLTR", "NVDA")
REQUIRED = {"Open", "High", "Low", "Close", "Volume"}

def main():
    failed = False
    for symbol in SYMBOLS:
        print(f"\n=== {symbol}: 5m availability ===", flush=True)
        try:
            frame = yf.download(
                symbol, period="5d", interval="5m",
                auto_adjust=True, progress=False, threads=False,
                prepost=False, timeout=25,
            )
            if frame is None or frame.empty:
                raise ValueError("No 5-minute bars returned")
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = frame.columns.get_level_values(0)
            missing = REQUIRED - set(frame.columns)
            if missing:
                raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
            frame = frame.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).sort_index()
            if frame.empty:
                raise ValueError("No complete OHLCV bars")
            last = frame.index[-1]
            print(f"Bars: {len(frame)}")
            print(f"First bar: {frame.index[0]}")
            print(f"Last bar: {last}")
            print(f"Last bar UTC: {last.tz_convert('UTC') if last.tzinfo else 'timezone missing'}")
            print(f"Last volume: {int(frame['Volume'].iloc[-1])}")
            if not last.tzinfo:
                raise ValueError("No timezone on last bar; cannot assess freshness")
            age_minutes = (datetime.now(timezone.utc) - last.to_pydatetime().astimezone(timezone.utc)).total_seconds() / 60
            print(f"Last bar age (minutes): {age_minutes:.1f}")
            print("NOTE: Availability does not prove real-time accuracy or commercial usage rights.")
        except Exception as exc:
            failed = True
            print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
