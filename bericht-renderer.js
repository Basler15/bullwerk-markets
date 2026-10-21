/* Bullwerk: Daten in das freigegebene Layout einsetzen. Keine Zugangsdaten. */
(function (root) {
  'use strict';
  const ids = ['1','2','3','4','5','6','7','8','9','12'];
  function validate(report, preview) {
    const fail = message => { throw new Error(message); };
    if (!report || report.schema_version !== 2) fail('Berichtsformat nicht unterstützt.');
    if (!['entwurf','freigegeben'].includes(report.status)) fail('Status ungültig.');
    if (!preview && report.status !== 'freigegeben') fail('Keine freigegebene Fassung vorhanden.');
    if (typeof report.datum !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(report.datum)) fail('Datum fehlt.');
    const date = new Date(report.datum + 'T12:00:00Z');
    if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0,10) !== report.datum) fail('Datum ungültig.');
    if (typeof report.report_id !== 'string' || !/^[a-zA-Z0-9_-]{6,80}$/.test(report.report_id)) fail('Berichtskennung fehlt.');
    if (typeof report.zusammenfassung !== 'string' || report.zusammenfassung.length < 40 || report.zusammenfassung.length > 2000) fail('Zusammenfassung fehlt.');
    if (!report.ampel || !['rot','gelb','gruen'].includes(report.ampel.farbe) || !['↗','→','↘'].includes(report.ampel.trend) || typeof report.ampel.text !== 'string' || report.ampel.text.length > 500) fail('Ampel unvollständig.');
    if (!Array.isArray(report.abschnitte) || report.abschnitte.length !== ids.length) fail('Die zehn öffentlichen Inhaltsabschnitte müssen vollständig sein.');
    const seen = new Set();
    report.abschnitte.forEach(s => {
      if (!s || !ids.includes(s.id) || seen.has(s.id) || typeof s.html !== 'string' || s.html.length < 20 || s.html.length > 80000) fail('Inhaltsabschnitt fehlt, ist doppelt oder ungültig.');
      seen.add(s.id);
    });
    if (typeof report.datenhinweis !== 'string' || report.datenhinweis.length < 10 || report.datenhinweis.length > 2000) fail('Datenhinweis fehlt.');
    if (!preview && (report.geprueft !== true || !report.freigabe || report.freigabe.von !== 'Basler15' || report.freigabe.text !== 'Bullwerk freigeben' || !Number.isFinite(Date.parse(report.freigabe.zeitpunkt)))) fail('Explizite Freigabe und Datenprüfung fehlen.');
    return report;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {validate};
  if (!root.document) return;
  const doc = root.document;
  // Nur vorhandene Designklassen, keine Styles oder frei wählbare Attribute.
  const classes = new Set(doc.body.dataset.reportClasses.split(' '));
  const tags = new Set(['P','H3','H4','STRONG','B','EM','I','UL','OL','LI','TABLE','THEAD','TBODY','TR','TH','TD','BLOCKQUOTE','HR','A','BR','SMALL','DIV','SPAN']);
  function clean(markup) {
    const t = doc.createElement('template'); t.innerHTML = markup;
    function scrub(parent) {
      for (const el of Array.from(parent.children)) {
        if (!tags.has(el.tagName)) { el.remove(); continue; }
        for (const a of Array.from(el.attributes)) {
          if (a.name === 'class') {
            const safe = a.value.split(/\s+/).filter(v => classes.has(v));
            if (safe.length) el.className = safe.join(' '); else el.removeAttribute('class');
          } else if (a.name === 'href' && el.tagName === 'A') {
            try { const u = new URL(a.value); if (u.protocol !== 'https:') throw Error(); el.setAttribute('href',u.href); }
            catch (_) { el.removeAttribute('href'); }
          } else el.removeAttribute(a.name);
        }
        if (el.tagName === 'A' && el.hasAttribute('href')) { el.rel = 'noopener noreferrer'; el.target = '_blank'; }
        scrub(el);
      }
    }
    scrub(t.content); return t.content;
  }
  function render(report, preview) {
    validate(report,preview);
    // Alle Fragmente vorbereiten, bevor sichtbare Inhalte ersetzt werden.
    const updates = report.abschnitte.map(s => {
      const target=doc.querySelector('[data-bericht-abschnitt="'+s.id+'"]');
      if (!target) throw Error('Layoutabschnitt fehlt.');
      return {target,heading:target.querySelector('h2').cloneNode(true),fragment:clean(s.html)};
    });
    updates.forEach(u=>u.target.replaceChildren(u.heading,u.fragment));
    const stamp = new Date(report.datum+'T12:00:00Z').toLocaleDateString('de-DE',{timeZone:'UTC'});
    doc.querySelector('.editorial-lead').textContent=report.zusammenfassung;
    const color={rot:'ROT',gelb:'GELB',gruen:'GRÜN'}[report.ampel.farbe];
    doc.querySelector('.traffic-message strong').textContent=color+' '+report.ampel.trend;
    doc.querySelector('.traffic-message p').textContent=report.ampel.text;
    doc.querySelector('.traffic-panel').setAttribute('aria-label','Marktampel '+color);
    doc.querySelector('.traffic-panel').dataset.farbe=report.ampel.farbe;
    doc.querySelector('.traffic-heading span').textContent=(preview?'VORSCHAU':'FREIGEGEBEN')+' · '+stamp;
    doc.querySelector('.editorial-dateline').textContent=stamp+' · '+(preview?'ENTWURF – FREIGABE AUSSTEHEND':'Redaktionell freigegeben')+' · '+report.report_id;
    doc.querySelector('main > p.notice').textContent=report.datenhinweis;
    doc.title='Bullwerk Markets – Morgenroutine '+stamp+(preview?' · Vorschau':'');
    root.bullwerkRenderedReport=report.report_id;
  }
  root.BullwerkReport={validate,render};
  const preview = new URLSearchParams(root.location.search).get('vorschau')==='1';
  // Pioneer 10/11 bleiben nur in der privaten Berichtsvorschau sichtbar.
  // Die öffentliche Morgenroutine verweist auf die separate Tradingideen-Seite.
  if (!preview) {
    ['10','11'].forEach(id => {
      const section = doc.querySelector('[data-bericht-abschnitt="'+id+'"]');
      if (section) section.remove();
    });
  }
  if (preview) {
    const bar=doc.createElement('div');bar.className='bw-preview-bar';
    const title=doc.createElement('strong');title.textContent='Private Vorschau: Berichtsdatei vom Gerät öffnen';
    const note=doc.createElement('p');note.textContent='Die ausgewählte JSON-Datei wird nur in diesem Browser angezeigt. Hierdurch wird nichts veröffentlicht.';
    const input=doc.createElement('input');input.type='file';input.accept='.json,application/json';input.setAttribute('aria-label','Berichtsdatei auswählen');
    const status=doc.createElement('p');status.setAttribute('role','status');
    input.addEventListener('change',async()=>{try {const file=input.files[0];if(!file)return;if(file.size>1000000)throw Error('Datei zu groß.');render(JSON.parse(await file.text()),true);status.textContent='Vorschau geladen. Veröffentlichung erst nach deiner Chat-Freigabe.';}catch(e){status.textContent='Nicht geladen: '+e.message;}});
    bar.append(title,note,input,status);doc.querySelector('main').prepend(bar);
    doc.querySelector('.editorial-dateline').textContent='VORSCHAU · Noch keine Berichtsdatei ausgewählt';
    return;
  }
  fetch('morgenroutine-freigegeben.json?stand='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(r=>render(r,false)).catch(()=>{
    doc.querySelector('.editorial-dateline').textContent='Noch kein Bericht im neuen Layout freigegeben · Datenbereiche in Vorbereitung';
  });
})(typeof window !== 'undefined' ? window : globalThis);
