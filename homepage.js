(function () {
 'use strict';
 const byId=id=>document.getElementById(id);
 const stamp=day=>day.split('-').reverse().join('.');
 function validDate(day){return typeof day==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(day)&&new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;}
 async function read(path){const r=await fetch(path+'?stand='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('Abruf');return r.json();}
 async function report(){
  try{
   const r=await read('morgenroutine-freigegeben.json');
   if(r.schema_version!==2||r.status!=='freigegeben'||r.geprueft!==true||!validDate(r.datum)||!r.freigabe||r.freigabe.von!=='Basler15'||r.freigabe.text!=='Bullwerk freigeben'||!Number.isFinite(Date.parse(r.freigabe.zeitpunkt))||!r.ampel||!['rot','gelb','gruen'].includes(r.ampel.farbe)||!['↗','→','↘'].includes(r.ampel.trend)||typeof r.ampel.text!=='string'||!r.ampel.text.trim()||!Array.isArray(r.abschnitte))throw Error('Keine gültige Freigabe');
   const section=r.abschnitte.find(s=>s.id==='2');if(!section||typeof section.html!=='string')throw Error('Marktüberblick fehlt');
   // Read text only from the approved report; never insert its HTML here.
   const parsed=new DOMParser().parseFromString(section.html,'text/html');
   // Der freigegebene Abschnitt 2 verwendet eine HTML-Tabelle (keine .market-line).
   // Alle Werte zuerst prüfen, erst danach die Startseite aktualisieren.
   const rows=Array.from(parsed.querySelectorAll('table tbody tr'));
   const values=Array.from(document.querySelectorAll('[data-market]')).map(cell=>{
     const matches=rows.filter(row=>row.cells[0]?.textContent.trim()===cell.dataset.market);
     if(matches.length!==1)throw Error('Markt fehlt: '+cell.dataset.market);
     const value=matches[0].cells[2]?.textContent.trim();
     if(!/^(?:ca\.\s*)?[+−-]?\\d{1,3}(?:[,.]\\d{1,2})?\\s*%$/.test(value))throw Error('Tagesveraenderung fehlt: '+cell.dataset.market);
     return {cell,value};
   });
   const marketDate='US-Schluss 22.10.2026 / DAX 22.10.2026';
   const color={rot:'ROT',gelb:'GELB',gruen:'GRÜN'}[r.ampel.farbe];
   byId('home-ampel').dataset.farbe=r.ampel.farbe;byId('home-ampel').setAttribute('aria-label','Marktampel '+color);
   byId('home-ampel').querySelector('h3').textContent='MARKTAMPEL · '+color+' '+r.ampel.trend;
   byId('home-ampel').querySelector('p').textContent=r.ampel.text;
   byId('home-report-stand').textContent='Freigegebener Bericht · '+stamp(r.datum);
   const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
   if(r.datum!==today){byId('home-report-stand').textContent='Letzter freigegebener Bericht · '+stamp(r.datum);byId('home-report-stand').classList.add('home-old');}
   byId('home-update').textContent='Morgenroutine · '+stamp(r.datum)+' · freigegeben';
   values.forEach(({cell,value})=>{cell.textContent=value;cell.className=/^(?:ca\.\s*)?[−-]/.test(value)?'home-negative':/^(?:ca\.\s*)?\+/.test(value)?'home-positive':'empty';});
   document.querySelector('.market-caption').textContent=marketDate+' · Tagesveränderung';
  }catch(err){byId('home-report-stand').textContent+=' · Aktualisierung nicht abrufbar; angezeigter Datenstand prüfen';console.warn('Bullwerk Startseite:',err);}
 }
 async function scanner(){
  try{
   const raw=await read('data/scanner-public.json');const d=window.BullwerkMarketGate.apply(raw,await window.BullwerkMarketGate.load());
   if(d.schema_version!==1||!validDate(d.as_of)||!d.coverage||!Number.isInteger(d.coverage.evaluated)||d.coverage.evaluated<1||!d.counts||!['watch','breakout'].every(k=>Number.isInteger(d.counts[k])&&d.counts[k]>=0))throw Error('Scanner-Daten');
   byId('home-scanner-text').textContent='Letzter Scan: '+stamp(d.as_of)+' · '+d.coverage.evaluated+' Aktien bewertet. '+(d.counts.watch+d.counts.breakout===0?'Keine Kandidaten über 80 Punkte.':d.counts.watch+' WATCH · '+d.counts.breakout+' BREAKOUT. Auswahl und Signalbedingungen auf der Scanner-Seite.');
   if(!d.market_gate.allowed)byId('home-scanner-text').textContent+=' '+d.market_gate.reason+'.';
  }catch(_){byId('home-scanner-text').textContent+=' Aktualisierung nicht abrufbar; gespeicherter Scan-Stand.';}
 }
 report();scanner();
})();
