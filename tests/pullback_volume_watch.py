"""Isolated Bullwerk pullback pattern research: green impulse, 2-4 red low-volume candles."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import pandas as pd
import yfinance as yf

US="AAPL MSFT NVDA AMD PLTR META AMZN GOOGL AVGO TSLA MU INTC DELL HPE ORCL SNOW COHR KEYS APH SMCI QCOM LRCX TER CRM NFLX UBER HOOD COIN MSTR SHOP PANW CRWD NET DDOG NOW ANET ARM MRVL AMAT KLAC TSM ASML JPM BAC GS MS V XOM CVX CAT GE BA F GM RIVN SOFI SQ PYPL ABNB COST WMT TGT DIS NKE RBLX ROKU DKNG SPOT IBM CSCO TXN ADI ON SMTC".split()
DE="ENR.DE SIE.DE SAP.DE IFX.DE RHM.DE HAG.DE ALV.DE BAS.DE BMW.DE MBG.DE VOW3.DE PAH3.DE DBK.DE CBK.DE DTE.DE DHL.DE ADS.DE BEI.DE HEN3.DE HEI.DE MUV2.DE RWE.DE EON.DE MTX.DE AIR.DE ZAL.DE P911.DE CON.DE VNA.DE SHL.DE".split()
SYMBOLS=list(dict.fromkeys(US+DE))

def fetch(symbol):
    # 60m is available historically; 4h bars are built within each exchange-local session.
    x=yf.download(symbol,period="60d",interval="60m",auto_adjust=True,prepost=False,progress=False,threads=False,timeout=20)
    d=yf.download(symbol,period="6mo",interval="1d",auto_adjust=True,prepost=False,progress=False,threads=False,timeout=20)
    def normalize(df):
        if df.empty:return df
        if isinstance(df.columns,pd.MultiIndex):df.columns=df.columns.get_level_values(0)
        return df.sort_index().dropna(subset=["Open","High","Low","Close","Volume"])
    return normalize(x),normalize(d)

def four_hour(df,symbol):
    if df.empty or df.index.tz is None:return pd.DataFrame()
    zone="Europe/Berlin" if symbol.endswith(".DE") else "America/New_York"
    x=df.tz_convert(zone)
    # Exchange-session anchored 4-hour blocks, not UTC midnight resampling.
    start="09:00" if symbol.endswith(".DE") else "09:30"
    chunks=[]
    for _,day in x.groupby(x.index.date):
        session=day.between_time("09:00","17:25") if symbol.endswith(".DE") else day.between_time("09:30","15:59")
        if len(session)<4:continue
        # Avoid incomplete 4h blocks and the short end-of-session stub.
        for offset in (0,4):
            part=session.iloc[offset:offset+4]
            if len(part)!=4:continue
            chunks.append((part.index[0],float(part.Open.iloc[0]),float(part.High.max()),
                           float(part.Low.min()),float(part.Close.iloc[-1]),float(part.Volume.sum())))
    if not chunks:return pd.DataFrame()
    return pd.DataFrame(chunks,columns=["time","Open","High","Low","Close","Volume"]).set_index("time")

def detect(df,tf):
    if len(df)<55:return []
    # Exclude last potentially incomplete bar for intraday series; conservative.
    if tf!="1D":df=df.iloc[:-1]
    close=df.Close.astype(float)
    ema20=close.ewm(span=20,adjust=False).mean()
    ema50=close.ewm(span=50,adjust=False).mean()
    candidates=[]
    # Evaluate last three completed bars as possible formation endpoints.
    for end in range(len(df)-3,len(df)):
        for reds in (2,3,4):
            impulse=df.iloc[end-reds-4:end-reds]
            pull=df.iloc[end-reds:end]
            if len(impulse)!=4 or len(pull)!=reds:continue
            greens=impulse[impulse.Close>impulse.Open]
            if len(greens)<3 or not (pull.Close<pull.Open).all():continue
            rise=float(impulse.Close.iloc[-1]-impulse.Open.iloc[0])
            if rise<=0:continue
            red_vol=float(pull.Volume.mean());green_vol=float(greens.Volume.mean())
            if red_vol<=0 or green_vol/red_vol<1.5:continue
            depth=float(impulse.Close.iloc[-1]-pull.Low.min())/rise
            if not (0<=depth<=0.5):continue
            last=end-1
            if not (close.iloc[last]>ema50.iloc[last] and ema20.iloc[last]>ema20.iloc[last-4] and ema50.iloc[last]>ema50.iloc[last-4]):continue
            decreasing=int(sum(pull.Volume.iloc[i]<pull.Volume.iloc[i-1] for i in range(1,reds)))
            score=round(50+min(25,8*(green_vol/red_vol-1))+8*(4-depth*4)+3*decreasing,1)
            candidates.append({"tf":tf,"time":str(df.index[last]),"reds":reds,"volume_ratio":round(green_vol/red_vol,2),"retracement":round(depth*100,1),"score":score,"phase":"WATCH" if end==len(df) else "RECENT"})
    return candidates

def scan(symbol):
    try:
        h,d=fetch(symbol)
        if h.empty or d.empty:return [],"no data"
        out=[]
        for tf,df in (("1H",h),("4H",four_hour(h,symbol)),("1D",d)):
            for hit in detect(df,tf):out.append({"symbol":symbol,**hit})
        return out,None
    except Exception as e:return [],str(e)[:100]

def main():
    print(f"PRIVATE RESEARCH | {len(SYMBOLS)} symbols | 1H, session-anchored 4H, 1D | no trades")
    found=[];errors=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(scan,s) for s in SYMBOLS]
        for f in as_completed(futures):
            rows,error=f.result();found.extend(rows)
            if error:errors+=1
    found.sort(key=lambda x:(-x["score"],x["symbol"]))
    print(f"Pattern matches: {len(found)} | symbols unavailable: {errors}")
    for hit in found[:10]:
        symbol=hit["symbol"]
        print(f"{hit['phase']} {symbol} {hit['tf']} | {hit['time']} | {hit['reds']} red bars | green/red volume {hit['volume_ratio']}x | retrace {hit['retracement']}% | pattern score {hit['score']} | https://www.tradingview.com/chart/?symbol={symbol}")
    if not found:print("No qualifying setups; do not force candidates.")
    print("CAVEATS: 4H candles are synthetic session blocks, partial bars excluded conservatively; pattern not a trade signal; no public redistribution.")
if __name__=="__main__":main()
