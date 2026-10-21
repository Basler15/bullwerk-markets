"""Hourly research runner; imports existing, unchanged pattern detection."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pullback_capacity_500 import expanded_universe as universe
from pullback_volume_watch import scan

def main():
    now=datetime.now(timezone.utc)
    berlin=now.astimezone(ZoneInfo("Europe/Berlin"))
    ny=now.astimezone(ZoneInfo("America/New_York"))
    de_open=berlin.weekday()<5 and 9<=berlin.hour<18
    us_open=ny.weekday()<5 and (ny.hour>9 or (ny.hour==9 and ny.minute>=30)) and ny.hour<16
    if not (de_open or us_open):
        print(f"SKIPPED outside cash trading hours | Berlin={berlin.isoformat()} | New York={ny.isoformat()}")
        return
    symbols=universe()
    hits=[];failed=0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(scan,s) for s in symbols]
        for future in as_completed(futures):
            rows,error=future.result()
            hits.extend(rows)
            if error:failed+=1
    # Timestamp is the opening time of the final bar, not the signal time.
    # Do not call an old pattern a fresh intraday alert.
    fresh=[]
    for hit in hits:
        bar=datetime.fromisoformat(hit["time"])
        if bar.tzinfo is None:continue
        age=now-bar.astimezone(timezone.utc)
        limit={"1H":timedelta(hours=3),"4H":timedelta(hours=10),"1D":timedelta(hours=48)}[hit["tf"]]
        if timedelta(0)<=age<=limit:fresh.append(hit)
    # De-duplicate overlapping historical windows within the same run only.
    unique={}
    for hit in fresh:
        key=(hit["symbol"],hit["tf"],hit["time"],hit["category"])
        if key not in unique or hit["score"]>unique[key]["score"]:
            unique[key]=hit
    rows=sorted(unique.values(),key=lambda h:(h["category"]!="WATCH",-h["score"]))
    print(f"HOURLY RESEARCH | checked={len(symbols)} | data failures={failed} | matches={len(hits)} | recent unique={len(rows)} | UTC={now.isoformat()}")
    for hit in rows[:15]:
        print(f'{hit["category"]} {hit["symbol"]} {hit["tf"]} | bar start={hit["time"]} | red={hit["reds"]} | volume={hit["volume_ratio"]}x | retracement={hit["retracement"]}% | https://www.tradingview.com/chart/?symbol={hit["symbol"]}')
    if not rows:print("No recent qualifying formations.")
    print("RESEARCH ONLY: Not an alert service; entries may repeat across runs. GitHub cron can start late. No public export or orders.")
if __name__=="__main__":main()
