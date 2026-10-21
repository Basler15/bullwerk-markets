"""Manual benchmark of 500 Nasdaq/Dow/MDAX/SDAX stocks. No production changes."""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import pandas as pd
import requests
from pullback_volume_watch import scan

HEADERS={"User-Agent":"Mozilla/5.0 (compatible; BullwerkResearch/0.1)"}
# Financial and biotech/pharma names are excluded only where identified by
# explicit industry data; additional filters are heuristic and not exhaustive.
EXCLUDE=re.compile(r"pharma|biotech|biopharma|therapeutic|drug manufacturer|biological product",re.I)

def html_tables(url):
    response=requests.get(url,headers=HEADERS,timeout=25)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))

def wikipedia_index(page):
    tables=html_tables("https://en.wikipedia.org/wiki/"+page)
    for table in tables:
        table.columns=[" ".join(map(str,c)) if isinstance(c,tuple) else str(c) for c in table.columns]
        cols=[c for c in table.columns if re.search(r"ticker|symbol",c,re.I)]
        if not cols or len(table)<20:continue
        col=cols[0]
        out=[]
        for _,row in table.iterrows():
            sym=str(row[col]).strip().split(" ")[0]
            if not re.fullmatch(r"[A-Za-z0-9.\-]{1,12}",sym):continue
            desc=" ".join(str(x) for x in row.values)
            if EXCLUDE.search(desc):continue
            out.append(sym.replace(".","-"))
        if len(out)>=20:return list(dict.fromkeys(out))
    raise RuntimeError("No reliable constituent table on "+page)

def german_index(page):
    """Inspect actual library schema before accepting German index tickers."""
    from pytickersymbols import PyTickerSymbols
    stocks=PyTickerSymbols()
    members=list(stocks.get_stocks_by_index(page))
    print(f"INDEX DIAGNOSTIC {page}: members={len(members)}",flush=True)
    print(f"INDEX SAMPLE {page}: {repr(members[:2])[:2500]}",flush=True)
    out=[]
    for stock in members:
        if EXCLUDE.search(str(stock.get("name",""))):
            continue
        direct=str(stock.get("symbol") or "")
        if re.fullmatch(r"[A-Za-z0-9]{1,8}\.DE",direct):
            out.append(direct.upper())
            continue
        for item in stock.get("symbols",[]):
            if not isinstance(item,dict):
                continue
            candidates=[str(v) for v in item.values() if isinstance(v,str)]
            match=next((v.upper() for v in candidates if re.fullmatch(r"[A-Za-z0-9]{1,8}\.DE",v)),None)
            if not match:
                match=next((v.upper() for v in candidates if re.fullmatch(r"[A-Za-z0-9]{1,8}\.F",v)),None)
            if match:
                out.append(match)
                break
    out=list(dict.fromkeys(out))
    print(f"INDEX MAPPED {page}: {len(out)} tickers; examples={out[:10]} | Frankfurt .F fallback={sum(x.endswith(chr(46)+chr(70)) for x in out)}",flush=True)
    if len(out)<25:
        raise RuntimeError(f"{page}: only {len(out)} mapped Yahoo tickers of {len(members)} members")
    return out

def nasdaq_symbols():
    url="https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    response=requests.get(url,headers=HEADERS,timeout=30)
    response.raise_for_status()
    lines=response.text.strip().splitlines()
    if not lines or not lines[0].startswith("Symbol|"):raise RuntimeError("Nasdaq directory format changed")
    df=pd.read_csv(StringIO("\n".join(lines)),sep="|",dtype=str)
    required={"Symbol","Security Name","Test Issue","ETF"}
    if not required.issubset(df.columns):raise RuntimeError("Nasdaq directory columns missing")
    df=df[(df["Test Issue"]=="N")&(df["ETF"]=="N")]
    # Common shares only, exclude warrants/units/rights and obvious funds.
    bad=re.compile(r"warrant|unit|rights|preferred|depositary|ETF|fund|trust|acquisition corp|biotech|pharma|therapeutic",re.I)
    df=df[~df["Security Name"].fillna("").str.contains(bad)]
    symbols=[s for s in df["Symbol"].dropna().astype(str) if re.fullmatch(r"[A-Z]{1,5}",s)]
    if len(symbols)<500:raise RuntimeError("Nasdaq directory too small or inaccessible")
    return symbols

def expanded_universe():
    mdax=german_index("MDAX")
    sdax=german_index("SDAX")
    dow=wikipedia_index("Dow_Jones_Industrial_Average")
    nasdaq=nasdaq_symbols()
    if not 35<=len(mdax)<=60:raise RuntimeError(f"MDAX constituents unexpected: {len(mdax)}")
    if not 35<=len(sdax)<=85:raise RuntimeError(f"SDAX constituents unexpected: {len(sdax)}")
    if not 25<=len(dow)<=35:raise RuntimeError(f"Dow constituents unexpected: {len(dow)}")
    # Priority: German indices and Dow first, then liquid Nasdaq names.
    # NasdaqTrader does not provide turnover; prefer larger established
    # Nasdaq constituents using Nasdaq-100 as a proxy, then the remaining
    # exchange directory. Do not claim remaining directory order is liquidity.
    nasdaq100=wikipedia_index("Nasdaq-100")
    ordered=list(dict.fromkeys(mdax+sdax+dow+[s for s in nasdaq100 if s in nasdaq]+nasdaq))
    symbols=ordered[:500]
    if len(symbols)!=500:raise RuntimeError(f"Only {len(symbols)} unique symbols")
    print(f"UNIVERSE | MDAX={len(mdax)} | SDAX={len(sdax)} | Dow={len(dow)} | Nasdaq directory={len(nasdaq)} | Nasdaq100={len(nasdaq100)}",flush=True)
    print(f"CTS Eventim included={'EVD.DE' in symbols}",flush=True)
    return symbols

def main():
    import sys
    if "--validate-universe" in sys.argv:
        symbols=expanded_universe()
        print(f"VALIDATED {len(symbols)} unique tickers; sample={symbols[:20]}",flush=True)
        return
    start=time.monotonic()
    symbols=expanded_universe()
    print(f"500 STOCK CAPACITY TEST | unique={len(symbols)} | manual only",flush=True)
    hits=[];errors=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(scan,s) for s in symbols]
        for f in as_completed(futures):
            rows,error=f.result()
            hits.extend(rows)
            if error:errors+=1
    watch=sum(h["category"]=="WATCH" for h in hits)
    early=sum(h["category"]=="FRUEH-WATCH" for h in hits)
    print(f"BENCHMARK duration={time.monotonic()-start:.1f}s | symbols={len(symbols)} | data_errors={errors} | WATCH={watch} | FRUEH-WATCH={early}",flush=True)
    evd=[h for h in hits if h["symbol"]=="EVD.DE"]
    print(f"CTS EVENTIM | matches={len(evd)}",flush=True)
    for h in evd:print(f'CTS EVENTIM {h["category"]} {h["tf"]} | bar={h["time"]} | vol={h["volume_ratio"]}x | retrace={h["retracement"]}%',flush=True)
    for h in sorted(hits,key=lambda x:(x["category"]!="WATCH",-x["score"]))[:15]:
        print(f'{h["category"]} {h["symbol"]} {h["tf"]} | bar={h["time"]} | vol={h["volume_ratio"]}x | retrace={h["retracement"]}%',flush=True)
    print("Manual research only; hourly workflow and public website unchanged.",flush=True)

if __name__=="__main__":main()
