# Scanner-Startprüfung – 19.10.2026

Geprüfter Ausgangsstand: a0a97b06ade212253f0eb744767beabb40cfa61a.

## Bestätigt
- Hauptscanner: zehn Symbole (AMD, NVDA, MSFT, PLTR, DELL, INTC, SNOW, COHR, KEYS, APH), Benchmark QQQ. Keine marktweite Suche.
- Stand 16.10.2026: zehn vollständige Scores, keine Abruffehler. Höchster Score PLTR 80,0; MSFT 73,3. Deshalb keine öffentlichen Kandidaten bei strikt >80.
- Hauptworkflow am 16.10.2026, Lauf 38983208459: tatsächlicher Scannerlauf erfolgreich. Lauf 38987473932: Zeitsperre wirksam, eigentliche Scan-Schritte übersprungen. Ein grüner Workflow allein ist kein Nachweis eines neuen Scans.
- Zwei UTC-Zeitpläne, Auswahl nach Europe/Berlin: geplant 23:30 deutsche Zeit. GitHub kann verzögert starten.
- Export: höchstens drei Aktien, WATCH strikt >80, BREAKOUT zusätzlich strikt >90, Signal=true und volume_confirmed=true. Komponenten und Rohpreise werden im öffentlichen Feed nicht ausgegeben.
- Website lädt öffentlichen Feed direkt aus dem Repository. Freitag ist am Montagvormittag der letzte abgeschlossene Handelstag.
- Export- und Feedtests lokal bestanden. Falschen Feed-Testpfad korrigiert: data/scanner-public.json. Tests künftig im Hauptworkflow vor dem echten Scan.
- Öffentliche Scanner-Seite erläutert begrenzten Prüfumfang einschließlich nicht bewerteter HPE.

## Vor dem offiziellen Start offen
1. Nächsten echten Scan nach dieser Anbindungsänderung prüfen: Export-Schritt, Commit, Datenstand und sichtbare Website müssen zusammenpassen. Die bisherigen grünen Scannerläufe liegen vor der heutigen Anbindungsänderung.
2. Aktienuniversum bewusst festlegen und bei Erweiterung Symbolzuordnung sowie Datenabdeckung prüfen. Keine Schwellen absenken, um Treffer zu erzeugen.
3. Datenquellen: main.py verwendet yfinance für Kurse und SEC für Fundamentals. Nutzungs- und Veröffentlichungsrechte vor kommerziellem Start gesondert prüfen; eine Tiingo-Vereinbarung bestätigt keine Rechte für eine andere Quelle.
4. Rote Marktampel ist derzeit kein technischer Gate im Export. Vor einer verbindlichen Breakout-Freigabe muss die Strategieentscheidung zur Kopplung umgesetzt und getestet werden.
5. Vollständige Score-Historie liegt im öffentlichen Repository. Das ist kein geschützter Pioneer-Speicher; zukünftige exklusive Ergebnisse separat schützen.
6. Aktualität: einfache Wochentagsprüfung, kein Börsenfeiertagskalender. Tagesauswertung, keine Intraday- oder E-Mail-Alarme.

Dies ist eine technische Bestandsaufnahme, keine Freigabe für den kommerziellen Start.
