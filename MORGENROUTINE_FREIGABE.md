# Bullwerk – tägliche Morgenroutine und Freigabe

Stand: 16.10.2026. Repository: Basler15/bullwerk-markets, Hauptbranch main.

## Verbindlicher Ablauf

1. Geplante Morgenroutine um 06:30 Europe/Berlin: vollständig recherchieren und dem Nutzer zur Kontrolle liefern, einschließlich Datenstand, Quellen und fertiger Vorschau. Kein bloßer Reminder.
2. Ausschließlich das bestehende Layout in marktbericht.html verwenden. Die 12 Abschnitte samt Tabellen, Kacheln und Pioneer-Vorschauen sind fest. Daten und Tageskommentare ersetzen, kein neues Layout erzeugen. Grün positiv, Rot negativ, Gold neutrale Zahlen. Quellen-/Prüfhinweis unten; Unsicherheiten zusätzlich an der jeweiligen Angabe.
3. Entwürfe privat als Dateien bereitstellen, NICHT in diesem öffentlichen Repository ablegen. Eine Entwurfsdatei auf GitHub wäre trotz status=entwurf öffentlich lesbar! Keine Pioneer-Vollanalysen in öffentliche JSON-Dateien schreiben.
4. Vollständige JSON-Fassung im Format unten und dazu eine lesbare Vorschau mit derselben report_id liefern. Die Vorschau darf keine anderen Daten als die JSON-Fassung zeigen. Für eine HTML-Vorschau den Renderer ausführen und die fertig gerenderte Seite exportieren, dabei Skripte und Vorschau-Dateiauswahl entfernen. Alternativ kann der Nutzer marktbericht.html?vorschau=1 öffnen und die JSON-Datei lokal auswählen. Dies lädt keine Entwurfsdaten hoch.
5. Auf die explizite Nachricht des Nutzers „Bullwerk freigeben“ für genau diese Fassung warten. Bei Änderungen neue report_id, neue Vorschau, erneute Freigabe. Eine Freigabe für einen alten Bericht ist keine Freigabe für eine neue Ausgabe.
6. Nach Freigabe im interaktiven Chat: aktuelle morgenroutine-freigegeben.json per GitHub lesen, aktuellen Blob-SHA verwenden, exakt die geprüfte Fassung setzen (status=freigegeben, geprueft=true, freigabe ergänzen) und mit update_file nach main committen. Keine neue Recherche, Umschreibung oder Aktualisierung nach Freigabe ohne neue Prüfung. Vorher Berichtsformat mit bericht-renderer.js validate() prüfen und Ausschluss geschützter Pioneer-Inhalte kontrollieren.
7. GitHub-Pages-Lauf für den neuen Commit über Actions prüfen. Erst nach erfolgreichem Deployment Veröffentlichung bestätigen und Link nennen. Ziel: rechtzeitige Freigabe und Veröffentlichung bis 07:30 Europe/Berlin. Laufzeiten und verspätete Freigaben erlauben keine unbedingte Zeitgarantie. Bei Fehlern klar melden, nicht Erfolg behaupten.

Der 06:30-Lauf veröffentlicht nichts selbstständig. Die Chat-Nachricht ist kein GitHub-Webhook: Der Assistent verarbeitet die Freigabe im anschließenden Chat über die GitHub-Verbindung. Es gibt keinen unbeaufsichtigten Dienst, der beliebige Chat-Nachrichten überwacht. Der Nutzer muss keinen HTML-Code mehr kopieren, sobald Vorschau und Freigabe verarbeitet werden.

## Öffentlicher Inhaltsvertrag, Version 2

Die Datei morgenroutine-freigegeben.json enthält diese Felder:

- schema_version: 2
- report_id: eindeutige Kennung, z.B. bullwerk-2026-10-16-v1
- status: entwurf oder freigegeben
- datum: gültiges ISO-Datum YYYY-MM-DD der Berichtsausgabe
- geprueft: true erst bei abgeschlossener Datenprüfung; fehlende Daten dürfen offen bleiben, aber nicht erfunden oder als bestätigt ausgegeben werden
- zusammenfassung: 40–2000 Zeichen, einfacher Text für den vorhandenen Einleitungsbereich
- ampel: {farbe: rot|gelb|gruen, trend: ↗|→|↘, text: einfacher Kurztext}
- abschnitte: exakt zehn Objekte {id: String, html: String}, IDs 1,2,3,4,5,6,7,8,9,12, jede genau einmal. html enthält den gesamten jeweiligen Abschnittsinhalt unterhalb der bestehenden h2-Überschrift. Vorhandene Designklassen beibehalten. Keine h1/h2, section, script, style, iframe, Bilder oder SVG einsetzen. Das Layout behält seine Überschriften.
- datenhinweis: kurzer transparenter Hinweis mit Quellen-/Datenstand und noch offenen Punkten
- freigabe nur nach expliziter Zustimmung: {von: Basler15, text: Bullwerk freigeben, zeitpunkt: ISO-Zeitstempel des tatsächlichen Freigabezeitpunkts}

Die öffentlichen Abschnitte 10 (Pioneer-Trading-Ideen) und 11 (Pioneer-Frühscanner) sind unveränderte Vorschauen. Die öffentliche Fassung enthält KEINE vertraulichen Trading-Pläne. Die Abschnittsreihenfolge folgt der ausdrücklich akzeptierten Vorlage: Wirtschaftskalender zuletzt als Abschnitt 12.

Zulässige Auszeichnungs-Klassen: bw-positive, bw-negative, bw-caution, bw-number sowie vorhandene Komponentenklassen aus marktbericht.html. Lampen der Historie: bw-lamp-green, bw-lamp-yellow, bw-lamp-red. Historische Scores/Änderungen nur bei belastbarer Berechnung zeigen. Fehlende Daten bleiben offen.

Der Renderer entfernt aktive HTML-Inhalte und unbekannte Attribute/Klassen. Quellenlinks ausschließlich als vollständige HTTPS-Links eintragen. HTML-Bereinigung ersetzt keine redaktionelle Daten-/Quellenprüfung. Die Freigabefelder sind ein Protokoll innerhalb des zugriffsgeschützten Schreibprozesses, keine kryptografische Signatur.

## Layout befüllen

Vor jeder Erstellung marktbericht.html und dieses Dokument aus GitHub lesen. Die Inhalte der zehn datenführenden section[data-bericht-abschnitt]-Elemente als Basis verwenden und innerhalb der bestehenden Komponenten befüllen. Keine Rohtext-Liste anstelle der gestalteten Tabellen/Kacheln erzeugen. Neue JSON-Fassung mit allen zehn Abschnitten erstellen. Die Darstellungslogik liegt in bericht-renderer.js; hierfür ist keine neue Daten-API erforderlich.

Bis zur ersten Freigabe einer Version-2-Fassung bleibt die Webseite im vorbereiteten Zustand. Die ältere JSON-Fassung ohne schema_version=2 wird absichtlich nicht mehr angezeigt, damit das Layout nicht wieder durch den alten einfachen Textblock ersetzt wird. Die bestehenden FRED-US-Zinsen bleiben in der noch unbefüllten Vorlage angebunden; nach Freigabe zeigt der Bericht einen konsistenten redaktionell geprüften Snapshot.

## Tests

node tests/bericht-renderer.test.cjs

Prüft Freigabesperre, Datenprüfung, gültige Datumswerte, doppelte/fehlende Abschnitte und den Ausschluss von Pioneer-IDs aus öffentlichen Daten. Die sichtbare Darstellung zusätzlich in der Vorschau kontrollieren.
