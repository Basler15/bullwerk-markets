(function(root){
'use strict';
function validate(d){
 if(!d||d.schema_version!==1||!/^\d{4}-\d{2}-\d{2}$/.test(d.as_of)||new Date(d.as_of+'T12:00:00Z').toISOString().slice(0,10)!==d.as_of||!Number.isFinite(Date.parse(d.generated_at)))throw Error('Datenstand ungueltig');
 if(!Array.isArray(d.selection)||d.selection.length>3)throw Error('Auswahl ungueltig');
 const seen=new Set();for(const s of d.selection){if(!s||typeof s.symbol!=='string'||!/^[A-Z.\-]{1,12}$/.test(s.symbol)||seen.has(s.symbol)||typeof s.name!=='string'||typeof s.score!=='number'||!Number.isFinite(s.score)||s.score<=80||s.score>100||!['WATCH','BREAKOUT'].includes(s.status)||s.as_of!==d.as_of||(s.status==='BREAKOUT'&&s.score<=90))throw Error('Kandidat ungueltig');seen.add(s.symbol);}
 if(!d.coverage||!Number.isInteger(d.coverage.evaluated)||d.coverage.evaluated<1||!Number.isInteger(d.coverage.errors)||d.coverage.errors<0)throw Error('Abdeckung ungueltig');
 if(typeof d.note!=='string')throw Error('Hinweis fehlt');
 if(!d.counts||!['watch','breakout'].every(k=>Number.isInteger(d.counts[k])&&d.counts[k]>=0)||d.counts.watch+d.counts.breakout<d.selection.length)throw Error('Anzahl ungueltig');
 return d;
}
function businessAge(day,now=new Date()){
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
 let d=new Date(day+'T12:00:00Z'),end=new Date(today+'T12:00:00Z'),n=0;
 if(d>end)throw Error('Daten aus der Zukunft');
 while(d<end){d.setUTCDate(d.getUTCDate()+1);if(d.getUTCDay()!==0&&d.getUTCDay()!==6)n++;if(n>10000)throw Error('Datum zu alt');}return n;
}
if(typeof module!=='undefined'&&module.exports)module.exports={validate,businessAge};
if(!root.document)return;
const doc=root.document;const byId=id=>doc.getElementById(id);
const el=(tag,content,cls)=>{const e=doc.createElement(tag);e.textContent=content;if(cls)e.className=cls;return e;};
async function load(){
 try{
  const r=await fetch('https://raw.githubusercontent.com/Basler15/bullwerk-markets/main/data/scanner-public.json?stand='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error();const d=validate(await r.json());
  const old=businessAge(d.as_of)>1,stamp=d.as_of.split('-').reverse().join('.');
  byId('scanner-datenstand').textContent=(old?'Älterer Datenstand: ':'Datenstand: ')+stamp+' · Tagesauswertung · '+d.coverage.evaluated+' Aktien bewertet'+(d.coverage.errors?' · '+d.coverage.errors+' nicht auswertbar':'');
  byId('scanner-datenstand').classList.toggle('scan-old',old);
  byId('watch-zahl').textContent=(old?'LETZTER SCAN: ':'')+d.counts.watch+' WATCH';
  byId('watch-text').textContent=d.counts.watch?'Kandidaten mit Qualitätsscore über 80. Die öffentliche Auswahl steht weiter unten.':'Im letzten Scan erfüllt keine Aktie die WATCH-Kriterien.';
  byId('breakout-zahl').textContent=(old?'LETZTER SCAN: ':'')+d.counts.breakout+' BREAKOUT';
  byId('breakout-text').textContent=d.counts.breakout?'Tagesausbrüche mit Score über 90 und bestätigtem Volumen. Kein Intraday-Alarm.':'Keine qualifizierten Ausbruchssignale im letzten Scan.';
  byId('ideen-beschreibung').textContent=old?'Ergebnisse eines älteren Scans. Keine aktuellen Handelssignale.':'Bis zu drei ausgewählte Aktien aus dem letzten vollständigen Scan.';
  const target=byId('scanner-auswahl');target.replaceChildren();
  if(!d.selection.length){const box=el('article','', 'idea scan-empty');box.append(el('strong','Keine neuen Kandidaten'),el('p','Keine ausgewertete Aktie überschreitet die Schwelle von 80 Punkten. Wir erzwingen keine Treffer.'),el('div','Letzter Scan: '+stamp,'wait'));target.append(box);}
  for(const [i,s] of d.selection.entries()){
   const box=el('article','', 'idea');box.append(el('span',String(i+1),'number'),el('strong',s.name));
   const info=el('p',s.symbol+' · '+s.status);box.append(info,el('div',s.score.toLocaleString('de-DE',{minimumFractionDigits:1,maximumFractionDigits:1})+' / 100','scan-score'),el('div',(old?'Historischer Stand: ':'Datenstand: ')+stamp,'wait'));target.append(box);
  }
  byId('scanner-quelle').textContent=d.note;
 }catch(_){byId('scanner-datenstand').textContent='Scanner-Daten derzeit nicht abrufbar. Es werden keine aktuellen Signale angezeigt.';}
}
load();
})(typeof window!=='undefined'?window:globalThis);
