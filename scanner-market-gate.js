(function(root){'use strict';
function validDay(day){if(typeof day!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(day))return false;const d=new Date(day+'T12:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===day;}
function latestDay(now){const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);const d=new Date(day+'T12:00:00Z');while([0,6].includes(d.getUTCDay()))d.setUTCDate(d.getUTCDate()-1);return d.toISOString().slice(0,10);}
function evaluate(report,now=new Date()){
 const blocked={allowed:false,farbe:null,datum:null,reason:'Keine aktuelle freigegebene Marktampel'};
 try{const r=report,a=r?.freigabe,t=a?.zeitpunkt;
 if(!r||r.schema_version!==2||r.status!=='freigegeben'||r.geprueft!==true||!validDay(r.datum)||r.datum!==latestDay(now)||typeof r.report_id!=='string'||!/^[a-zA-Z0-9_-]{6,80}$/.test(r.report_id)||a?.von!=='Basler15'||a?.text!=='Bullwerk freigeben'||typeof t!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(t)||!Number.isFinite(Date.parse(t))||Date.parse(t)>+now||!['rot','gelb','gruen'].includes(r.ampel?.farbe))return blocked;
 const color=r.ampel.farbe;return {allowed:color!=='rot',farbe:color,datum:r.datum,reason:color==='rot'?'Marktampel ROT: keine Breakout-Freigabe':'Marktampel erlaubt die technische Signalprüfung'};
 }catch(_){return blocked;}
}
function apply(feed,gate,now=new Date()){
 if(!feed||!Array.isArray(feed.selection)||!feed.counts)throw Error('Scanner-Auswahl fehlt');
 const d=new Date(latestDay(now)+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-1);while([0,6].includes(d.getUTCDay()))d.setUTCDate(d.getUTCDate()-1);
 if(!validDay(feed.as_of)||feed.as_of<d.toISOString().slice(0,10)||feed.as_of>latestDay(now))gate={...gate,allowed:false,reason:'Scanner-Datenstand nicht aktuell: keine Breakout-Freigabe'};
 if(gate.allowed)return {...feed,market_gate:gate};
 return {...feed,market_gate:gate,counts:{watch:feed.counts.watch+feed.counts.breakout,breakout:0},selection:feed.selection.map(s=>s.status==='BREAKOUT'?{...s,status:'WATCH'}:s)};
}
async function load(now=new Date()){try{const response=await fetch('https://raw.githubusercontent.com/Basler15/bullwerk-markets/main/morgenroutine-freigegeben.json?stand='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('Abruf');return evaluate(await response.json(),now);}catch(_){return evaluate(null,now);}}
const api={evaluate,apply,load};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.BullwerkMarketGate=api;
})(typeof window!=='undefined'?window:globalThis);