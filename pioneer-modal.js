(()=>{'use strict';
const style=document.createElement('style');
style.textContent=`
#bw-pioneer-dialog{box-sizing:border-box;width:min(540px,calc(100vw - 28px));max-height:calc(100dvh - 32px);overflow:auto;padding:0;border:1px solid #b58b43;border-radius:16px;background:#fffaf2;color:#24211b;box-shadow:0 24px 90px #0009;font:15px/1.55 Arial,Helvetica,sans-serif}
#bw-pioneer-dialog::backdrop{background:rgba(0,0,0,.75);backdrop-filter:blur(4px)}
#bw-pioneer-dialog *{box-sizing:border-box}#bw-pioneer-dialog .bw-p-head{position:relative;background:linear-gradient(120deg,#101211,#292318);padding:27px 30px 25px;color:#fff8e7}
#bw-pioneer-dialog .bw-p-kicker{font-size:11px;font-weight:800;letter-spacing:2px;color:#edc772;margin:0 36px 12px 0}
#bw-pioneer-dialog h2{font:700 clamp(27px,5vw,34px)/1.12 Georgia,'Times New Roman',serif;color:#fff8e7;margin:0 0 12px;letter-spacing:-.5px}
#bw-pioneer-dialog h2 em{color:#efcb7b;font-style:normal}
#bw-pioneer-dialog .bw-p-head p:last-child{font-size:14px;color:#ded5c4;margin:0;line-height:1.6}
#bw-pioneer-dialog .bw-p-close{position:absolute;right:15px;top:15px;width:34px;height:34px;border:1px solid #75613d;border-radius:50%;background:#ffffff08;color:#f8dfac;font:25px/1 Arial;cursor:pointer}
#bw-pioneer-dialog .bw-p-body{padding:23px 30px 27px}
#bw-pioneer-dialog .bw-p-main{padding:17px 18px;background:#f5e8cb;border:1px solid #d8b871;border-radius:9px;margin-bottom:18px}
#bw-pioneer-dialog h3{font:800 18px/1.3 Arial,Helvetica,sans-serif;color:#674716;margin:0 0 7px}
#bw-pioneer-dialog p{font-size:14px;line-height:1.6;margin:0;color:#514a3e}
#bw-pioneer-dialog .bw-p-benefit{display:flex;gap:12px;margin:15px 0}
#bw-pioneer-dialog .bw-p-icon{flex:none;color:#9b6f29;font-size:21px;width:25px}
#bw-pioneer-dialog .bw-p-benefit strong{display:block;font-size:14px;color:#28231b;margin-bottom:3px}
#bw-pioneer-dialog .bw-p-benefit p{font-size:13px}
#bw-pioneer-dialog .bw-p-status{border-top:1px solid #e4d6bd;padding-top:15px;margin-top:20px;font-size:12px;color:#746958}
#bw-pioneer-dialog .bw-p-status strong{display:block;color:#92651f;font-size:11px;letter-spacing:1px;margin-bottom:5px}
#bw-pioneer-dialog .bw-p-more{display:block;text-align:center;background:linear-gradient(135deg,#ffe5a2,#e2ad4c);border:1px solid #c99a45;border-radius:7px;color:#2b200e;padding:12px 16px;margin-top:19px;font-size:14px;font-weight:800;text-decoration:none}
#bw-pioneer-dialog :focus-visible{outline:3px solid #bf8b2f;outline-offset:4px}
@media(max-width:500px){#bw-pioneer-dialog .bw-p-head{padding:24px 21px}#bw-pioneer-dialog .bw-p-body{padding:20px 21px}}
`;
document.head.append(style);
const dialog=document.createElement('dialog');dialog.id='bw-pioneer-dialog';dialog.setAttribute('aria-labelledby','bw-p-title');
dialog.innerHTML=`<div class="bw-p-head"><button type="button" class="bw-p-close" aria-label="Fenster schließen" autofocus>×</button><p class="bw-p-kicker">♛ BULLWERK PIONEER</p><h2>Den nächsten<br><em>Ausbruch im Blick.</em></h2><p>Für alle, die starke Aktien früh erkennen und bestätigte Breakouts gezielt verfolgen möchten.</p></div><div class="bw-p-body"><div class="bw-p-main"><h3 id="bw-p-title">Breakout-Alarme im Mittelpunkt</h3><p>Geplant sind Benachrichtigungen, sobald ein geprüfter Kandidat den Ausbruch mit passender Struktur und bestätigtem Volumen zeigt – direkt per E-Mail, später auch im privaten Telegram-Kanal.</p></div><div class="bw-p-benefit"><span class="bw-p-icon" aria-hidden="true">⌕</span><div><strong>Vollständiger Pioneer-Scanner</strong><p>Ausgewählte WATCH- und BREAKOUT-Kandidaten mit Score, relativer Stärke und nachvollziehbarer Einordnung.</p></div></div><div class="bw-p-benefit"><span class="bw-p-icon" aria-hidden="true">↗</span><div><strong>Analysen mit klarem Handelsplan</strong><p>Fundamentale Gründe, Chartstruktur, Einstiegsszenario, Stop und Ziel – einschließlich Chancen und Risiken.</p></div></div><div class="bw-p-status"><strong>IN VORBEREITUNG</strong>Mitgliederbereich, Anmeldung und Alarme werden noch aufgebaut. Aktuell ist kein Abo abschließbar. Zum Start stellen wir den verfügbaren Leistungsumfang vor.</div><a class="bw-p-more" href="ueber-uns.html#pioneer">Mehr über Pioneer erfahren →</a></div>`;
document.body.append(dialog);
let opener=null;
document.addEventListener('click',event=>{const trigger=event.target.closest('.pioneer-cta');if(!trigger)return;event.preventDefault();opener=trigger;if(!dialog.open)dialog.showModal();});
dialog.querySelector('.bw-p-close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();});
dialog.addEventListener('close',()=>{if(opener&&document.contains(opener))opener.focus();});
})();