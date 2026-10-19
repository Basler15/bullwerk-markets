const assert=require('node:assert/strict');
const {evaluate,apply}=require('./scanner-market-gate.js');
const now=new Date('2026-10-19T10:00:00Z');
const report={schema_version:2,report_id:'bullwerk-2026-10-19-v1',status:'freigegeben',geprueft:true,datum:'2026-10-19',freigabe:{von:'Basler15',text:'Bullwerk freigeben',zeitpunkt:'2026-10-19T04:30:00Z'},ampel:{farbe:'gruen'}};
const feed={as_of:'2026-10-16',counts:{watch:4,breakout:2},selection:[{symbol:'AMD',status:'BREAKOUT',score:95},{symbol:'MSFT',status:'WATCH',score:85}]};
for(const color of ['rot','gelb','gruen']){
 const r=structuredClone(report);r.ampel.farbe=color;
 const d=apply(feed,evaluate(r,now),now);
 assert.equal(d.counts.breakout,color==='rot'?0:2);
 assert.equal(d.selection[0].status,color==='rot'?'WATCH':'BREAKOUT');
 assert.equal(d.selection[0].score,95);
}
for(const r of [null,{}, {...report,status:'entwurf'},{...report,geprueft:false},{...report,datum:'2026-10-16'},{...report,datum:'2026-02-30'},{...report,freigabe:{...report.freigabe,von:'fremd'}},{...report,freigabe:{...report.freigabe,zeitpunkt:'2026-10-19T15:00:00Z'}},{...report,freigabe:{...report.freigabe,zeitpunkt:'2026-10-19T04:30:00'}}]){
 assert.equal(evaluate(r,now).allowed,false);
 assert.equal(apply(feed,evaluate(r,now),now).counts.breakout,0);
}
assert.equal(apply({...feed,as_of:'2026-10-15'},evaluate(report,now),now).counts.breakout,0);
assert.equal(apply({...feed,as_of:'2026-10-20'},evaluate(report,now),now).counts.breakout,0);
assert.equal(feed.selection[0].status,'BREAKOUT');
assert.equal(evaluate({...report,datum:'2026-10-16',freigabe:{...report.freigabe,zeitpunkt:'2026-10-16T04:30:00Z'}},new Date('2026-10-18T10:00:00Z')).allowed,true);
console.log('PASS: Ampel-Freigabe, Sperre, veraltete/future Daten, Scores und Wochenende');
