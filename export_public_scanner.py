"""Allowlisted public selection from existing scanner results; no raw prices."""
import json
import math
from datetime import date, datetime
from pathlib import Path
from market_gate import market_gate

NAMES = {'AMD':'Advanced Micro Devices','NVDA':'NVIDIA','MSFT':'Microsoft','PLTR':'Palantir','DELL':'Dell Technologies','INTC':'Intel','SNOW':'Snowflake','COHR':'Coherent','KEYS':'Keysight Technologies','APH':'Amphenol'}
LEADERS = ['MSFT','NVDA','DELL','PLTR','AMD','HPE','INTC']


def public_results(data, report=None):
    if not isinstance(data, dict) or not isinstance(data.get('stocks'), list) or not data['stocks']:
        raise ValueError('Keine auswertbare Scanner-Ausgabe')
    stamp = data.get('generated_at')
    dt = datetime.fromisoformat(stamp)
    if dt.tzinfo is None:
        raise ValueError('Zeitstempel ohne Zeitzone')
    gate = market_gate(report, dt)
    valid = []
    seen = set()
    for item in data['stocks']:
        symbol = item.get('symbol')
        if symbol not in NAMES or symbol in seen:
            raise ValueError('Unbekanntes oder doppeltes Symbol')
        seen.add(symbol)
        day = item.get('as_of')
        if date.fromisoformat(day).isoformat() != day or date.fromisoformat(day) > dt.date():
            raise ValueError('Ungueltiger Datenstand')
        score = item.get('quality_score')
        if score is None:
            continue
        if isinstance(score, bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0 <= score <= 100:
            raise ValueError('Ungueltiger Score')
        valid.append((item, day, score))
    if not valid:
        raise ValueError('Keine vollstaendige Bewertung; letzte Web-Ausgabe behalten')
    dates = {day for _,day,_ in valid}
    if len(dates) != 1:
        raise ValueError('Uneinheitlicher Datenstand')
    candidates = []
    for item, day, score in valid:
        if score <= 80:
            continue
        b = item.get('breakout') or {}
        # Der hohe Qualitaetsscore allein ist niemals ein Ausbruchssignal.
        breakout = gate['allowed'] and score > 90 and b.get('signal') is True and b.get('volume_confirmed') is True
        candidates.append({'symbol':item['symbol'],'name':NAMES[item['symbol']],'score':score,'status':'BREAKOUT' if breakout else 'WATCH','as_of':day})
    candidates.sort(key=lambda s:(-s['score'],s['symbol']))
    overview = sorted([{'symbol':item['symbol'],'name':NAMES[item['symbol']],'score':score,'as_of':day} for item, day, score in valid], key=lambda s:(-s['score'],s['symbol']))
    return {'schema_version':1,'scanner':str(data.get('scanner','Bullwerk Gesamtscanner')),'generated_at':stamp,'as_of':dates.pop(),'market_gate':gate,'coverage':{'evaluated':len(valid),'errors':len(data.get('errors',[]))},'counts':{'watch':sum(s['status']=='WATCH' for s in candidates),'breakout':sum(s['status']=='BREAKOUT' for s in candidates)},'overview':overview,'selection':candidates[:3],'leaders':LEADERS,'note':'Tagesauswertung, keine Live-Signale. Qualitaetsscore aus drei berechneten Saeulen; Signal und feste LEADERS-Liste getrennt. Keine Anlageberatung.'}


if __name__ == '__main__':
    source = Path('data/scanner_results.json')
    target = Path('data/scanner-public.json')
    try:
        report = json.loads(Path('morgenroutine-freigegeben.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        report = None
    result = public_results(json.loads(source.read_text(encoding='utf-8')), report)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    temporary.replace(target)
    print('Oeffentliche Auswahl:',len(result['selection']),'| Datenstand:',result['as_of'])
