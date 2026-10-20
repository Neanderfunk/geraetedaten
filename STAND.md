# Stand (20.10.2026)

## Erledigt
- Pilot mit 10 Geräten (Agenten, 19.10.), Bericht: [laeufe/2026-10-19-pilot.md](laeufe/2026-10-19-pilot.md).
- Selector-Ansicht (`werkzeug/selector-ansicht.py`, je Gerät `ausgabe/selector/<image>.json`),
  Filterdaten (`ausgabe/selector/facetten.json`), Geräteliste ([GERAETE.md](GERAETE.md)).
- routerwahl.ffnef.de (`web/`) ist live, ausgeliefert über `deploy.sh` in firmware-selector-config
  als zweiter Webroot `/var/www/routerwahl.ffnef.de`. Texte von Content (freifunk-content
  `vorschlaege/routerwahl-texte.md`, `selector-geraetedaten-texte.md`).
- Im Selector zeigt `ffnef-geraete.js` nur noch, was für die Installation zählt, und verlinkt auf routerwahl.
- **Volllauf** 19./20.10.: 362 Einträge (alle Images ausser `laeufe/keine-geraete.txt` und zwei
  URL-kodierten Dubletten `%2B`), 17 "fertig", 345 "teilweise". Verteilt auf direkte Abrufe und
  SOCKS-Tunnel (kollektor6, OVH-Kollektor-VM, Mesh-Knoten), 4 Agenten je Stapel. Skripte und
  Sperrliste der Hosts: siehe Workflow-Skripte der Supernode-Session; Kurzfassung der Sperren in
  `schema/felder.md` (Handel).
- Nicht unterstützte Hardware-Versionen mit Grund (Selector `versionen-toh.json`, routerwahl-Kaufhinweis).

## Offen
- **Handelsdaten-Nachlauf** (EAN, Amazon-ASIN, Geizhals-Permalink): 263 Einträge haben noch keins
  der drei Felder, meist aus den Stapeln vor der Handelsdaten-Anweisung. Engpass ist die CDX-API des
  Webarchivs (zeitweise 503/504); geizhals.de, idealo und ean-search.org sperren direkt.
- **Zweiter Durchgang** über FCC-Fotos und Anatel für Hohlstecker-Maß, Netzteil-Typenschild, Lüfter,
  LEDs, serielle Konsole je Charge (offene Fäden in den Einträgen).
- **Eigene Messungen** aus der Router-Werkstatt (`docs/validierung/`) als Quelle "werkstatt" mit hoher
  Sicherheit einpflegen (z. B. MR70X V1.20, Lage der Konsole).
- Werte teils noch englisch oder in ASCII-Umlauten; der Generator bereinigt nur häufige Wörter.
- Modellnamen in GERAETE.md bei Varianten holprig ("AP3000 wall-v1").
- Neu erzeugen nach jeder Datenänderung:
  `werkzeug/selector-ansicht.py` und `werkzeug/geraeteliste.py --index <installer>/anleitungen/html/index.json`,
  dann committen, pushen, Deploy durch adorfer.
