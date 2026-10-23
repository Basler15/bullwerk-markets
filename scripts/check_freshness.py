#!/usr/bin/env python3
"""Bullwerk Markets: prüft werktags Datenfrische, ohne Börsenwerte zu erfinden."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
now = datetime.now(ZoneInfo("Europe/Berlin"))
today = now.date()
previous = today - timedelta(days=1)
while previous.weekday() > 4:
    previous -= timedelta(days=1)
problems = []
notes = []

def problem(text):
    problems.append(text)
    print("::error::" + text)

def check_html(path, pattern, expected, label):
    html = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(pattern, html)
    if not match:
        problem(f"{path}: {label} nicht lesbar")
    elif match.group(1) != expected:
        problem(f"{path}: {label} {match.group(1)}, erwartet {expected}")
    else:
        notes.append(f"{path}: {label} {expected} OK")

report = json.loads((ROOT / "morgenroutine-freigegeben.json").read_text(encoding="utf-8"))
if report.get("datum") != today.isoformat():
    problem(f"Morgenroutine: {report.get('datum')} statt {today.isoformat()} (nur freigegebene Berichte veröffentlichen)")
elif report.get("status") != "freigegeben" or report.get("geprueft") is not True:
    problem("Morgenroutine: Bericht nicht freigegeben/geprüft")
else:
    notes.append("Morgenroutine: Datum und Freigabe OK")

# Der ETF-Vergleich muss mindestens den letzten abgeschlossenen US-Handelstag abdecken.
# Feiertage sind nicht in dieser einfachen Regel berücksichtigt: bei Feiertagen
# ausdrücklich prüfen, nicht ungeprüft aktualisieren.
check_html("etfs.html", r"Vergleichsschluss\s+(\d{2}\.\d{2}\.\d{4})", previous.strftime("%d.%m.%Y"), "ETF-Vergleichsschluss")
# Diese Seiten sollen einen erkennbaren, datierten Status zeigen.
for filename, label in [("krypto.html", "Krypto"), ("rohstoffe.html", "Rohstoffe")]:
    html = (ROOT / filename).read_text(encoding="utf-8")
    match = re.search(r'id="home-update"[^>]*>[^<]*?(\d{2}\.\d{2}\.\d{4})', html)
    if not match:
        problem(f"{label}: Seiten-Datenstand fehlt")
    elif match.group(1) != today.strftime("%d.%m.%Y"):
        problem(f"{label}: Seiten-Datenstand {match.group(1)} statt {today.strftime('%d.%m.%Y')}")
    else:
        notes.append(f"{label}: Tageskennzeichnung vorhanden (inhaltliche Prüfung zusätzlich nötig)")

print("\n".join(notes))
print(f"Ergebnis: {len(problems)} Frischewarnung(en).")
if problems:
    sys.exit(1)
