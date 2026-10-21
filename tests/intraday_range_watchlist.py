"""Private research-only 5m range screener; independent of Bullwerk's main scanner."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import math
import pandas as pd
import yfinance as yf

US = "AAPL MSFT NVDA AMD PLTR META AMZN GOOGL AVGO TSLA MU INTC DELL HPE ORCL SNOW COHR KEYS APH SMCI QCOM LRCX TER CRM NFLX UBER HOOD COIN MSTR SHOP PANW CRWD NET DDOG NOW ANET ARM MRVL AMAT KLAC TSM ASML JPM BAC GS MS V XOM CVX CAT GE BA F GM RIVN SOFI SQ PYPL ABNB COST WMT TGT DIS NKE RBLX ROKU DKNG SPOT IBM CSCO TXN ADI ON SMTC".split()
DE = "ENR.DE SIE.DE SAP.DE IFX.DE RHM.DE HAG.DE ALV.DE BAS.DE BMW.DE MBG.DE VOW3.DE PAH3.DE DBK.DE CBK.DE DTE.DE DHL.DE ADS.DE BEI.DE HEN3.DE HEI.DE MUV2.DE RWE.DE EON.DE MTX.DE AIR.DE ZAL.DE P911.DE CON.DE VNA.DE SHL.DE".split()
SYMBOLS = list(dict.fromkeys(US + DE))

def scan(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="5m", auto_adjust=True,
                         prepost=False, progress=False, threads=False, timeout=15)
        if df.empty or df.index.tz is None: return None, "no data/timezone"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.sort_index()
        tz = ZoneInfo("Europe/Berlin") if symbol.endswith(".DE") else ZoneInfo("America/New_York")
        df = df.tz_convert(tz)
        sessions = [(d,g) for d,g in df.groupby(df.index.date) if len(g)>=20]
        if not sessions: return None, "insufficient session"
        date, day = sessions[-1]
        # Exclude an unfinished current candle. Historical days are already complete.
        now = datetime.now(tz)
        if date == now.date():
            day = day[day.index + pd.Timedelta(minutes=5) <= pd.Timestamp(now)]
        if len(day)<20: return None, "too few completed candles"
        # 24 candles = two hours; look for horizontal consolidation BEFORE any breakout.
        window = day.tail(24)
        hi=float(window.High.max()); lo=float(window.Low.min())
        mid=(hi+lo)/2
        if not math.isfinite(mid) or mid<=0 or hi<=lo:return None,"bad price"
        width=(hi-lo)/mid*100
        if width>3.0:return None,"range too wide"
        # Independent touches near both boundaries, with at least one candle between touches.
        tolerance=max((hi-lo)*0.18,mid*0.0005)
        highs=[i for i,v in enumerate(window.High) if hi-v<=tolerance]
        lows=[i for i,v in enumerate(window.Low) if v-lo<=tolerance]
        def distinct(indices):
            count=0;last=-3
            for i in indices:
                if i-last>=3:count+=1;last=i
            return count
        ht=distinct(highs);lt=distinct(lows)
        if ht<2 or lt<2:return None,"insufficient touches"
        volume=window.Volume.astype(float)
        if volume.isna().any() or volume.sum()<=0:return None,"missing volume"
        last=float(window.Close.iloc[-1])
        if last<lo or last>hi:return None,"outside range"
        # Rank narrow and well-tested ranges; score is structural, not Bullwerk's 0-100 fundamental score.
        score=round(min(100, 55+8*min(ht,4)+8*min(lt,4)-12*width),1)
        url=f"https://www.tradingview.com/chart/?symbol={'XETR%3A'+symbol[:-3] if symbol.endswith('.DE') else 'NASDAQ%3A'+symbol}"
        return {"symbol":symbol,"date":str(date),"bar_time":str(window.index[-1]),"high":round(hi,3),
                "low":round(lo,3),"width_pct":round(width,2),"high_touches":ht,"low_touches":lt,
                "score":score,"tradingview":url},None
    except Exception as e:
        return None,str(e)[:120]

def main():
    print(f"RESEARCH ONLY | universe={len(SYMBOLS)} | no orders | no public export")
    found=[];failed=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(scan,s):s for s in SYMBOLS}
        for future in as_completed(futures):
            row,error=future.result()
            if row:found.append(row)
            elif error:failed+=1
    found.sort(key=lambda r:(-r["score"],r["width_pct"],r["symbol"]))
    print(f"Valid range candidates: {len(found)} | no-match/unavailable: {failed}")
    for row in found[:5]:
        print(f"WATCH {row['symbol']} | {row['date']} | {row['bar_time']} | "
              f"range {row['low']}-{row['high']} | width {row['width_pct']}% | "
              f"touches {row['low_touches']}/{row['high_touches']} | structural {row['score']} | {row['tradingview']}")
    if not found: print("No qualifying charts. Do not force candidates.")
if __name__=="__main__":main()
