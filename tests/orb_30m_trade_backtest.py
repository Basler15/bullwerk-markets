"""Isolated exploratory ORB backtest. Not investment signals; no changes to public scanner."""
import sys
from datetime import time
import pandas as pd
import yfinance as yf

NY="America/New_York"
TIMES=[time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55)]
SYMBOLS=("PLTR","NVDA")
R_MULTIPLE=1.5

def test_symbol(symbol):
    data=yf.download(symbol,period="1mo",interval="5m",auto_adjust=True,prepost=False,progress=False,threads=False)
    if data.empty or data.index.tz is None: raise ValueError(f"{symbol}: missing data/timezone")
    if isinstance(data.columns,pd.MultiIndex): data.columns=data.columns.get_level_values(0)
    data=data.tz_convert(NY).sort_index()
    outcomes=[]
    for date,raw in data.groupby(data.index.date):
        day=raw.between_time("09:30","15:55")
        opening=day.between_time("09:30","09:55")
        if list(opening.index.time)!=TIMES: continue
        high=float(opening.High.max());low=float(opening.Low.min())
        if high<=low: continue
        after=day.between_time("10:00","15:55")
        if len(after)<60: continue # completed regular trading day only
        # First close outside range determines direction. Entry only at NEXT bar's open,
        # never on the signal candle itself (avoid lookahead).
        signal=None
        for i in range(len(after)-1):
            candle=after.iloc[i]
            if candle.Close>high: signal=(i,"LONG");break
            if candle.Close<low: signal=(i,"SHORT");break
        if signal is None:
            outcomes.append((date,"NONE","-","-","-","NO BREAK"));continue
        i,direction=signal
        entry=float(after.iloc[i+1].Open)
        # Range-opposite stop is fixed before entry; reject invalid gap-through entries.
        stop=low if direction=="LONG" else high
        risk=(entry-stop) if direction=="LONG" else (stop-entry)
        if risk<=0:
            outcomes.append((date,direction,f"{entry:.2f}","-","-","INVALID"));continue
        target=entry+R_MULTIPLE*risk if direction=="LONG" else entry-R_MULTIPLE*risk
        outcome="EOD"
        exit_price=float(after.iloc[-1].Close)
        # Include the entry candle, with conservative stop-first on ambiguous bars.
        for _,bar in after.iloc[i+1:].iterrows():
            if direction=="LONG":
                if bar.Low<=stop: outcome="STOP";exit_price=stop;break
                if bar.High>=target: outcome="TARGET";exit_price=target;break
            else:
                if bar.High>=stop: outcome="STOP";exit_price=stop;break
                if bar.Low<=target: outcome="TARGET";exit_price=target;break
        r=((exit_price-entry)/risk) * (1 if direction=="LONG" else -1)
        outcomes.append((date,direction,f"{entry:.2f}",f"{stop:.2f}",f"{target:.2f}",outcome,round(r,2)))
    if len(outcomes)<10:raise ValueError(f"{symbol}: only {len(outcomes)} complete sessions")
    print(f"\n=== {symbol}: historical ORB prototype; latest 10 complete sessions ===")
    sample=outcomes[-10:]
    for x in sample:print(*x,sep=" | ")
    traded=[x for x in sample if len(x)==7]
    print(f"Trades={len(traded)}; targets={sum(x[5]=='TARGET' for x in traded)}; stops={sum(x[5]=='STOP' for x in traded)}; EOD={sum(x[5]=='EOD' for x in traded)}; sum_R={sum(x[6] for x in traded):+.2f}")
    print("LIMITS: No spread, slippage, fees, 1D/1H filter, volume/ATR filter or live execution. Range-opposite stop may be wide. Research only.")

if __name__=="__main__":
    try:
        for s in SYMBOLS:test_symbol(s)
    except Exception as e:
        print("FAIL:",e,file=sys.stderr);sys.exit(1)
