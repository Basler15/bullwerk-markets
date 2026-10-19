const assert=require('node:assert/strict'),fs=require('node:fs');const {validate,businessAge}=require('./scanner-public.js');
const base=JSON.parse(fs.readFileSync(__dirname+'/scanner-public.json'));validate(base);
for(const change of [d=>d.selection=[{symbol:'PLTR',name:'Palantir',score:80,status:'WATCH',as_of:d.as_of}],d=>d.coverage=null,d=>d.as_of='2026-02-30',d=>d.selection=Array(4).fill({})]){const d=structuredClone(base);change(d);assert.throws(()=>validate(d));}
assert.equal(businessAge('2026-10-16',new Date('2026-10-19T05:00:00Z')),1);assert.equal(businessAge('2026-10-16',new Date('2026-10-20T05:00:00Z')),2);assert.throws(()=>businessAge('2026-10-20',new Date('2026-10-19T05:00:00Z')));
console.log('PASS: Datenvertrag, Score-Schwelle, Fehlerzustand und Wochenend-Datenstand');
