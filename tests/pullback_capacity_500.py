"""Manual 500-stock capacity test. Existing production and pattern detection untouched."""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pullback_capacity_300 import universe as base_universe
from pullback_volume_watch import scan

# German mid/small-cap candidates, including CTS Eventim. Research universe,
# not a claim of current MDAX/SDAX membership.
GERMAN_EXTRA="""EVD.DE G1A.DE FPE3.DE TUI1.DE KRN.DE JUN3.DE WAF.DE AIXA.DE
SRT3.DE NEM.DE BOSS.DE LEG.DE G24.DE FNTN.DE EVK.DE LHA.DE
NDA.DE PUM.DE SDF.DE KCO.DE DUE.DE BNR.DE RAA.DE HFG.DE
SIX2.DE CEC.DE AT1.DE DEZ.DE FIE.DE HLE.DE JEN.DE
VOS.DE WCH.DE AOF.DE PNE3.DE 2GB.DE HYQ.DE 1U1.DE
SAX.DE MBB.DE S92.DE DBAN.DE DWS.DE BVB.DE
DRW3.DE GFT.DE O2D.DE SZG.DE KWS.DE UTDI.DE
BC8.DE COK.DE TTK.DE VBK.DE
""".split()

def expanded_universe():
    base=base_universe()
    # Base consists of original 104 symbols and the first S&P500 members.
    # Re-fetch full constituent set to fill the remaining slots.
    import requests, pandas as pd
    from io import StringIO
    url="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp=requests.get(url,headers={"User-Agent":"BullwerkResearch/0.1 (capacity benchmark)"},timeout=20)
    resp.raise_for_status()
    table=pd.read_html(StringIO(resp.text),match="Symbol")[0]
    us=[str(x).replace(".","-") for x in table["Symbol"].dropna()]
    symbols=list(dict.fromkeys(base+GERMAN_EXTRA+us))[:500]
    if len(symbols)!=500:raise RuntimeError(f"Only {len(symbols)} unique symbols")
    return symbols

def main():
    start=time.monotonic()
    symbols=expanded_universe()
    print(f"500 STOCK CAPACITY TEST | unique={len(symbols)} | EVD.DE included={'EVD.DE' in symbols} | manual only",flush=True)
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
    print("Manual research only. No modifications to the hourly workflow or public website.",flush=True)

if __name__=="__main__":main()
