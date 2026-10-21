"""Manual-only capacity benchmark. Pattern detection stays unchanged."""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import pandas as pd
import requests
from pullback_volume_watch import SYMBOLS, scan

def universe():
    url="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response=requests.get(url,headers={"User-Agent":"BullwerkResearch/0.1 (capacity test)"},timeout=15)
    response.raise_for_status()
    table=pd.read_html(StringIO(response.text),match="Symbol")[0]
    symbols=[str(s).replace(".","-") for s in table["Symbol"].dropna().tolist()]
    # Retain all existing 104 symbols, then expand with S&P 500 names.
    return list(dict.fromkeys(SYMBOLS+symbols))[:300]

def main():
    start=time.monotonic()
    try:
        symbols=universe()
    except Exception as exc:
        print(f"Could not obtain the expanded universe: {exc}; benchmark aborted (no misleading 104-stock result).")
        raise SystemExit(1)
    print(f"CAPACITY TEST | requested=300 | unique symbols={len(symbols)} | no orders, no public export",flush=True)
    hits=[]; failures=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(scan,s):s for s in symbols}
        for future in as_completed(futures):
            matches,error=future.result()
            hits.extend(matches)
            if error:failures+=1
    seconds=time.monotonic()-start
    watch=sum(h["category"]=="WATCH" for h in hits)
    early=sum(h["category"]=="FRUEH-WATCH" for h in hits)
    print(f"BENCHMARK seconds={seconds:.1f} | stocks={len(symbols)} | errors_or_no_data={failures} | WATCH={watch} | FRUEH-WATCH={early}",flush=True)
    for h in sorted(hits,key=lambda x:(x["category"]!="WATCH",-x["score"]))[:10]:
        print(f'{h["category"]} {h["symbol"]} {h["tf"]} {h["time"]} | vol={h["volume_ratio"]}x | retrace={h["retracement"]}%',flush=True)
    print("NOTE: A single successful run does not establish hourly reliability or real-time data availability.")

if __name__=="__main__":
    main()
