# Öffentliche Scanner-Anbindung

Stand: 19.10.2026

Der bestehende Gesamtscanner berechnet unverändert seine Ergebnisse. Anschließend erzeugt `export_public_scanner.py` aus `data/scanner_results.json` eine öffentliche, begrenzte Auswahl in `data/scanner-public.json`.

- Nur Qualitätsscores strikt über 80 werden als Kandidaten gezeigt.
- BREAKOUT setzt zusätzlich einen Score strikt über 90, ein bestehendes Ausbruchssignal und bestätigtes Volumen voraus. Hoher Score allein genügt nicht.
- Höchstens drei Kandidaten, nach Score sortiert. Die Zähler berücksichtigen alle qualifizierten Treffer.
- Ohne qualifizierte Treffer erscheint ein ehrlicher Leerzustand.
- Die feste LEADERS-Liste bleibt getrennt von den berechneten Kandidaten.
- Der aktuelle Score verwendet drei berechnete Säulen. Die Scanner-Strategie wurde nicht erweitert.
- Keine Rohkurse, Trigger, Komponentenwerte oder vollständigen Ergebnislisten im öffentlichen Export.

## Aktualisierung und Fehler

Der vorhandene nächtliche Workflow schreibt nach erfolgreichem Scan die öffentliche Auswahl zusammen mit der Score-Historie ins Repository. Die Seite lädt diese kleine Datei direkt aus dem öffentlichen Repository; dadurch ist für neue Daten kein Pages-Neubau durch den Actions-Bot erforderlich.

Datenstand und Tagesauswertung sind sichtbar. Nach mehr als einem weiteren Wochentag werden die Ergebnisse als älter markiert. Börsenfeiertage werden in dieser einfachen Alterskennzeichnung nicht gesondert berücksichtigt. Es handelt sich nicht um Intraday-Alarme.

Ungültige, gemischte oder vollständig fehlende Bewertungen brechen den Export ab; die letzte gültige Datei bleibt erhalten. Nicht abrufbare Web-Daten werden als Fehler angezeigt. Die feste Symbolzuordnung entspricht dem bestehenden Zehner-Universum und muss bei dessen Erweiterung ergänzt werden.

## Prüfung

`python -m unittest test_export.py` und `node test_feed.cjs` prüfen Grenzwerte, Signalvoraussetzungen, öffentliche Felder, Auswahlbegrenzung, ungültige Daten und Wochenend-Alter. Die erste veröffentlichte Auswahl stammt aus dem vollständigen Scan mit Kursdaten vom 16.10.2026: zehn bewertete Aktien, keine über 80 Punkte.

Die abschließende Prüfung von Datenrechten und Veröffentlichungsbedingungen bleibt wie vereinbart vor dem eigentlichen Seitenstart vorgesehen.


## Öffentliche Punkteübersicht – 19.10.2026

Auf ausdrücklichen Nutzerwunsch öffnet der Button „Öffentliche Auswahl“ eine Übersicht aller zehn beobachteten Aktien mit Gesamtqualitätsscore und Datenstand, auch unterhalb der WATCH-Schwelle. Dafür exportiert `overview` nur Symbol, Name, Gesamtpunkte und Datum. Die Liste ist damit ausdrücklich öffentlich; exklusive Komponentenwerte, Rohkurse und Handelspläne werden nicht veröffentlicht. Die eigentliche Kandidatenauswahl bleibt auf drei qualifizierte Treffer begrenzt. Anfangswerte der Punkteübersicht stammen aus der vorhandenen Score-Historie des 16.10.2026; der Nachtworkflow ersetzt sie durch die nächste tatsächliche Auswertung. Keine neu berechneten oder erfundenen Tageswerte.
