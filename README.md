# Gerätedaten für Freifunk-Router

Eine Geräte-Datenbank für die Router, für die Neanderfunk Gluon-Images baut.
Sie liefert die Gerätedaten, die der Firmware-Selector
(routersoftware.ffnef.de) nach der Gerätewahl einblendet: RAM, Flash, CPU,
WLAN mit Standard und Streams, Antennen, Anschlüsse, Stromversorgung (PoE,
DC-Buchse, Leistung), innen oder außen, Montage, serielle Konsole.

**Stand:** Aufbau ab 19.10.2026, zuerst ein Pilot mit 10 Geräten.

## Grundsätze

- Ein Eintrag je Gluon-Image-Name (`daten/<image>.json`).
- Alles mitnehmen, was eine Quelle hergibt (`roh`), und jeden normalisierten
  Wert mit Quelle, Beleg-URL und Stand der Quelle führen (`felder`).
  Einzelheiten in [schema/felder.md](schema/felder.md).
- Widersprechen sich Quellen, stehen beide Werte da. Was keine Quelle belegt,
  fehlt, statt geraten zu werden.
- URLs, die noch Daten versprechen (FCC-Fotos, Anatel, Datenblätter), stehen
  als offene Fäden im Eintrag.

## Quellen

- OpenWrt Table of Hardware (Tab-Dump, `quellen/`), OpenWrt-Wiki
- DeviWiki (Nachfolger von WikiDevi), WikiDevi-Spiegel
- FCC ID (Fotos, Handbücher), Anatel
- Herstellerseiten und Datenblätter
- eigene Messungen am Testplatz (Router-Werkstatt)

## Lizenz

Die Daten stehen unter **CC BY-SA 4.0** (Datei `LICENSE`), weil sie zum Teil
aus der OpenWrt-ToH und DeviWiki stammen, die ebenfalls unter CC BY-SA 4.0
stehen. Die Quelle jedes Werts steht im Eintrag.
Die Werkzeuge unter `werkzeug/` stehen unter BSD-3-Clause
(`werkzeug/LICENSE`).
