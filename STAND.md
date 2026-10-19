# Stand (19.10.2026)

## Erledigt
- Pilot mit 10 Geräten (Agenten, 19.10.), Bericht: [laeufe/2026-10-19-pilot.md](laeufe/2026-10-19-pilot.md).
- Selector-Ansicht (`werkzeug/selector-ansicht.py`, je Gerät `ausgabe/selector/<image>.json`),
  Filterdaten (`ausgabe/selector/facetten.json`), Geräteliste ([GERAETE.md](GERAETE.md)).
- routerwahl.ffnef.de (`web/`) ist live, ausgeliefert über `deploy.sh` in firmware-selector-config
  als zweiter Webroot `/var/www/routerwahl.ffnef.de`. Texte von Content (freifunk-content
  `vorschlaege/routerwahl-texte.md`, `selector-geraetedaten-texte.md`).
- Im Selector zeigt `ffnef-geraete.js` nur noch, was für die Installation zählt, und verlinkt auf routerwahl.

## Offen
- **Volllauf** für die übrigen 374 Geräte: Recherche ruht auf Anweisung von adorfer (19.10.).
  Vorschläge für den Lauf: zweiter Anlauf nur bei "festgefahren" oder fehlendem Strom/Einsatzort/
  Hardware-Version (die Schwelle "≥ 5 Lücken" griff bei allen 10), GitHub-Token gegen das Rate-Limit,
  3 Agenten gleichzeitig. Pilot: rund 350 000 Tokens und 10 Minuten je Gerät mit zweitem Anlauf.
- **Zweiter Durchgang** über FCC-Fotos und Anatel für Hohlstecker-Maß, Netzteil-Typenschild, Lüfter,
  LEDs, serielle Konsole je Charge (offene Fäden in den Einträgen).
- **Eigene Messungen** aus der Router-Werkstatt (`docs/validierung/`) als Quelle "werkstatt" mit hoher
  Sicherheit einpflegen (z. B. MR70X V1.20, Lage der Konsole).
- Werte teils noch englisch oder in ASCII-Umlauten; der Generator bereinigt nur häufige Wörter.
- Modellnamen in GERAETE.md bei Varianten holprig ("AP3000 wall-v1").
- Neu erzeugen nach jeder Datenänderung:
  `werkzeug/selector-ansicht.py` und `werkzeug/geraeteliste.py --index <installer>/anleitungen/html/index.json`,
  dann committen, pushen, Deploy durch adorfer.
