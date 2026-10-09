# BULLWERK MARKETS – PROJEKTSTAND

Stand: 09.10.2026
Slogan: Bullen finden, bevor sie ausbrechen.

## 1. Projektziel
Bullwerk Markets wird eine deutschsprachige Aktien-, ETF-, Rohstoff- und Krypto-Plattform. Schwerpunkt: starke Unternehmen, aufkommende Trends und mögliche Ausbrüche frühzeitig erkennen. Die Plattform kombiniert fundamentale Beschleunigung, technische Signale, relative Stärke, Kapitalflüsse und das Marktumfeld.

## 2. Marke und Design – beschlossen
- Hochwertiges Schwarz-Gold-Design mit cremefarbenen Lesebereichen.
- Markanter goldener Bulle als Markenmotiv.
- Navigation: Startseite, Morgenroutine, Scanner, ETFs, Rohstoffe, Krypto, Über uns.
- Startseite: Marktampel, Morgenroutine-Kurzfassung, Scanner-Kandidaten und Bullen-ETF.
- Morgenroutine: ausführliche, gut lesbare Textanalyse.
- Einzelaktienseite: freigegebene AMD-Designvorlage mit dunklem Chartbereich, goldener Darvas-Box, Bullwerk-Score und Textanalyse.
- Die AMD-Vorlage war ein Designbeispiel, kein echter interaktiver Chart und keine bestätigten Kursdaten.
- Bestehendes Design nicht unnötig neu gestalten.

## 3. Scanner – bestehende Strategie
- Schwerpunkt Long-Trading und frühe Trend-/Breakout-Erkennung.
- Kombination aus Fundamental-Momentum, Kurs-Momentum, Trendqualität, Marktumfeld und technischer Struktur.
- Bullwerk-Score: fünf Säulen mit jeweils maximal 20 Punkten, insgesamt 100.
- WATCH bei Score über 80 bis einschließlich 90.
- BREAKOUT bei Score über 90 und passendem Trigger; ein klar rotes Marktregime kann die Freigabe verhindern. Diese Regel ist noch zu testen.
- LEADERS für etablierte starke Aktien mit eigenen Pullback-/Breakout-Chancen.
- Keine Pharmaunternehmen in den Kandidatenlisten.
- Technische Ansätze: Darvas-Box, Breakout, Buy-Stop über letzter roter Kerze, Stop unter Struktur, Volumen, relative Stärke, EMA50/EMA200, 4h/1h.
- Die Erkennung echter Darvas-Boxen ist noch zu verbessern und anhand realer Charts zu prüfen.
- Bestehenden GitHub-Scanner nicht unnötig umbauen.

## 4. Technischer Stand
- GitHub-Projekt: Basler15/bullwerk-markets.
- GitHub Actions wurden erfolgreich für Scanner-Läufe eingesetzt.
- Scanner-Score-Historie wird in data/score_history.json geführt.
- Scanner-Ergebnisse sind noch nicht vollständig in die öffentliche Website integriert.
- Die öffentliche Startseite darf daher nicht als bereits vollständig live angebundener Scanner beschrieben werden.
- Weitere Programmierung erst nach Design- und Datenquellenklärung.

## 5. Tiingo – schriftlich bestätigte Lizenzbedingungen
Kontakt mit Tiingo, Antwort von Blair, zu Commercial-Plan ca. 50 USD/Monat und Terms of Service Abschnitt 1.6.

Nach der erhaltenen Auskunft unter Bedingungen erlaubt:
- Einzelne isolierte tägliche prozentuale Veränderungen von Aktien oder Indizes.
- Grobe Wochen-, Monats- und YTD-Renditen als einzelne Zusammenfassungen.
- Eigene, nicht rekonstruierbare Scores, Rankings und Signale.
- Voraussetzung: Rohkurse dürfen daraus nicht rekonstruierbar sein und das Angebot darf keinen Marktdatenfeed ersetzen.

Unter diesem Plan nicht erlaubt:
- Historische tägliche Renditereihen und daraus rekonstruierbare Kurven.
- Echte historische Kurscharts auf Grundlage von Tiingo-Daten.
- Konkrete Tiingo-Kursmarken, Preisanker, Einstiegspreise und Stop-Preise.
- Eine eigene Chartbibliothek hebt die Datenlizenzpflicht nicht auf.

Tiingo nannte für weitergehende Redistribution einen Standard Startup Redistribution Plan ab ca. 250 USD/Monat. Vertragsdetails vor Abschluss erneut prüfen.

Bei Kündigung müssen Tiingo-Rohdaten gelöscht werden. Nicht rekonstruierbare abgeleitete Analysen dürfen laut Auskunft bestehen bleiben. Tiingo-Daten nicht zur Validierung eines anderen Datensatzes verwenden, da dies zusätzliche Löschpflichten auslösen kann.

## 6. Beschlossene Lösung für Einstieg und Stop
- Öffentlich keine konkreten Einstiegskurse oder Stop-Preise aus Tiingo veröffentlichen.
- Stattdessen: Buy-Stop über der letzten roten Kerze; Stop unter der roten Kerze bzw. unter der relevanten Struktur.
- Leser prüfen genaue Marken im eigenen Broker oder rechtmäßig eingebetteten Chart.
- Langfristig eine separat passend lizenzierte Kursdatenquelle für konkrete Preislevel prüfen.
- Diese Lösung wurde ausdrücklich freigegeben.

## 7. Echte Charts auf der Website – offen
- Freigegebenes AMD-Layout beibehalten.
- Prüfen, ob ein offizielles TradingView-Widget oder ein anderer rechtmäßig nutzbarer Chartdienst eingebettet werden kann.
- Nutzungsbedingungen für kommerzielle Websites und mögliche Börsenrechte prüfen.
- Prüfen, ob Bullwerk-Darvas-Boxen, Einstiegszonen und Stop-Zonen technisch im Chart dargestellt werden dürfen und können.
- TradingView-Widget und Tiingo-Daten sauber trennen.
- Bis zur Klärung keine echten historischen Tiingo-Kerzencharts veröffentlichen.

## 8. Morgenroutine und Marktampel
Ziel: täglich etwa 07:30 Uhr Berlin.
- Nasdaq/Gesamtmarkttrend und Marktbreite.
- US-Renditen 2Y/10Y, Fed-Erwartungen, Inflation, Arbeitsmarkt.
- Öl, Gold, Silber, Dollar und weitere wichtige Rohstoffe.
- Earnings, Gewinnrevisionen, AI-/Capex-Dynamik.
- Geopolitik, Saisonalität, Fear & Greed.
- Crash-Frühwarnung: VIX, Kreditspreads, Liquidität, Marktbreite und Warnketten.
- Kapitalflüsse mit echter Quelle, Berichtsperiode und Datenstand; grundsätzlich wöchentlich statt tägliche Zuflüsse zu erfinden.
- Trading-Ideen, wichtige Termine und nachvollziehbare Gesamtbewertung.
- Geplante 5-Tage-Ampelhistorie, Advance/Decline, Up/Down-Volumen und Distribution Days sind noch zu prüfen.
- Datenverfügbarkeit und kommerzielle Veröffentlichungsrechte für jeden Baustein prüfen.
- Historische Berichte sind keine Bestätigung aktueller Marktdaten.

## 9. ETF- und Themen-Frühscanner
- Sektor- und Themen-ETFs dynamisch beobachten, nicht nur eine starre Liste.
- Mehrere Kandidaten parallel: Früh-WATCH, WATCH, TRIGGER, LEADER, FAIL.
- Relative Stärke und Beschleunigung gegen QQQ/Nasdaq.
- Fundamentale Treiber, ETF-Flows, EMA50/EMA200, Boxen und Volumen berücksichtigen.
- Themen: Halbleiter/KI, Robotics, Cybersecurity, Defense, Kernenergie, Stromnetze, Rechenzentren, Space, Rohstoffe, Energie und weitere neue Trends.
- ETF-Signale können Einzelaktien-Setups bestätigen.
- Historische Monat-für-Monat-Tests wurden diskutiert; keine unüberprüften Rückblickergebnisse als reale Backtests ausgeben.

## 10. Quantum- und Krypto-Frühscanner
- Quantum: gesamte Wertschöpfungskette von Hardware über Photonik, Kryotechnik, Messtechnik, Halbleiter und HPC bis Software und Post-Quantum-Sicherheit.
- Echte Aufträge, Umsatzbeschleunigung, Guidance und Gewinnrevisionen von Hype unterscheiden.
- Krypto: insbesondere SOL und ETH, Netzwerkaktivität, Stablecoins, RWA, Flows, relative Stärke und Ausbruchsstrukturen.
- Wöchentliche Beobachtung vorgesehen.

## 11. Geschäftsmodell
- Bullwerk Pioneer als bevorzugtes frühes Abo-Modell.
- Geplant: erste 200–500 Abonnenten dauerhaft 4,99 EUR/Monat bei ununterbrochenem Abo.
- Später regulär etwa 7,99–9,99 EUR/Monat.
- Preisgestaltung und Umsetzung noch nicht endgültig live.
- Vor kostenpflichtigen Datenquellen stets Nutzungsrechte und Wirtschaftlichkeit prüfen.

## 12. Offene Aufgaben – Reihenfolge
1. Dieses Projektprotokoll in GitHub sichern und fortschreiben.
2. Chartanbieter und kommerzielle Einbettungsrechte prüfen.
3. Lizenzmatrix aller für Bullwerk benötigten Datenquellen erstellen.
4. Finales Seitendesign mit echten, rechtmäßig nutzbaren Inhalten umsetzen.
5. Scanner-Ergebnisse sicher an die Website anbinden.
6. Morgenroutine und wöchentliche Kapitalflussberichte automatisieren.
7. Website testen, danach Preis-/Abo-Modell technisch umsetzen.

## 13. Arbeitsregeln
- Schrittweise arbeiten, maximal zwei bis drei kleine Anweisungen gleichzeitig.
- Für Codeänderungen möglichst vollständige Ersatzdateien liefern.
- Bestehenden funktionierenden Scanner schützen.
- Keine Beispieldaten als echte Marktdaten ausgeben.
- Neue Entscheidungen und Fortschritte in dieser Datei nachtragen.
- GitHub-Projektprotokoll dient als verlässliche Dokumentation des Projektstands.
