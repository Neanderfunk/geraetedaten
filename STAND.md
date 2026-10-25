# Stand (25.10.2026)

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
- Nicht unterstützte Hardware-Versionen mit Grund (Selector `versionen-toh.json`, Hersteller-Downloadseiten
  `versionen-hersteller.json`), auf routerwahl als eigene Karten hinter den Geschwistern.
- **Geizhals über preisvergleich.heise.de** (20.10.): 362 Geräte, 308 mit `geizhals_url` (188 genau, 119
  mehrere Versionen), Datenblatt-Tabelle in `roh.geizhals`; 51 nicht gelistet. heise antwortete zweimal 403.

## Offen
- **Prüfung** (`werkzeug/pruefen.py`, Bericht `laeufe/pruefung-<datum>.md`): 20.10. 145 Geräte mit
  Zahlenwidersprüchen von Agenten entschieden (auch Fotos), 209 Werte `widerlegt`, 89 Fälle „beide
  richtig“ (Variante/Messart, mit Bemerkung), 3 offen (OM2P-HS v3 PoE-Spannung, NBG6716 Flash, RBS50 Flash).
- **EAN/ASIN:** Geizhals-Seiten (über heise) nennen keine EAN; 0 von 362 bisher. Offen, falls je gebraucht.
- **Zweiter Durchgang** über FCC-Fotos und Anatel für Hohlstecker-Maß, Netzteil-Typenschild, Lüfter,
  LEDs, serielle Konsole je Charge (offene Fäden in den Einträgen).
- **Eigene Messungen** aus der Router-Werkstatt (`docs/validierung/`) als Quelle "werkstatt" mit hoher
  Sicherheit einpflegen (z. B. MR70X V1.20, Lage der Konsole).
- Werte teils noch englisch oder in ASCII-Umlauten; der Generator bereinigt nur häufige Wörter.
- Modellnamen in GERAETE.md bei Varianten holprig ("AP3000 wall-v1").
- Geräteliste: `werkzeug/image-liste.py <URL des letzten Laufs auf imageslive>` (z. B.
  `https://imageslive.ffdus.de/images2025.1/images-<epoch>/21_dias/21_dias`) schreibt
  `quellen/images-lauf-<datum>.txt` mit allen gebauten Geräten (auch BROKEN). Die Download-Zweige
  reichen dafür nicht: neue Targets (ipq50xx) fehlten dort, z. B. die MR80X.
- Nach jedem neuen stable (z. B. Rollout 2025.1): `werkzeug/image-liste.py stable` holt die
  Gerätenamen vom Firmware-Server nach `quellen/images-stable-<datum>.txt`. Daraus setzt
  `selector-ansicht.py` die Facette `stable`; routerwahl blendet Geräte ohne stable-Image
  zunächst aus („Firmware erst mit der nächsten Version“).
- „Speicher für Updates“ seit 21.10.2026 fünfstufig (neu: „gut“), RAM je WLAN-Treiberklasse,
  Geräte mit Firmware-Abstrichen höchstens „knapp“. Regeln und Eichung in schema/felder.md.
  Nach Änderungen an image-customization.lua: `werkzeug/abstriche.py <FirmwareConfigs> <gluon>`.
- Circa-Neupreise (seit 23.10.2026): `werkzeug/preise-holen.py` schreibt `preise.json` in den
  routerwahl-Webroot, Regel und Betrieb in `schema/felder.md` („Circa-Neupreise“). Cron seit 24.10.2026
  in `/etc/cron.d/preise-holen` auf dem Firmware-Server (montags 3 Uhr); erster Serverlauf
  23./24.10.: 262 Seiten, 84 mit Preis, 34 zu wenig Angebote, 144 ohne Angebot, 0 Fehler.
- WireGuard-Durchsatz (seit 22.10.2026): `werkzeug/vpn-werte.py` aus `quellen/vpn-durchsatz-<datum>.json`
  (FFMUC-Wiki, OpenWrt-Forum wg-bench, wg-bench README, ToH-VPN-Ansicht) und der Handzuordnung
  `quellen/vpn-zuordnung.tsv`. Neue Geräte in den Quellen: Abzug erneuern, Zuordnung ergänzen.
- Gluon-Target je Image (Filter „Plattform“ auf routerwahl, seit 22.10.2026):
  `werkzeug/gluon-targets.py <gluon-klon> <gluon-patches-hardware-klon>` schreibt
  `quellen/gluon-targets.json`; nach neuen Geräten oder Patches neu laufen lassen.
- Bedienung routerwahl (24./25.10.2026, adorfer), alles in `web/`:
  - Voreinstellung ohne URL-Parameter: WLAN 6, Speicher ab „ausreichend“, Einrichtung bis L1,
    Geräte mit fehlenden Angaben ausgeblendet; gelber Hinweis oben, solange sie unverändert ist
    (`VORGABE`, `istVorgabe()`). „Auswahl zurücksetzen“ leert alles, blendet nicht unterstützte
    Geräte ein und schreibt `?alle` bzw. `?nicht=1`, damit ein Neuladen nicht wieder vorbelegt.
  - Sortierung: Vorgabe „günstigster Neupreis (circa)“, Geräte ohne Preis am Ende.
  - „Speicher für Updates“ als Radio-Buttons „Stufe oder besser“ (Filtertyp `stufe`, Schlüssel
    `reduziert` für den Wert mit Komma, weil die Auswahl kommagetrennt in der URL steht).
  - Filterreihenfolge: Einrichtung, WLAN, Preis, Ausstattung, Anschlüsse, Einsatz, Strom, Plattform
    (Filter „Gluon-Target“, Klammern nur Hersteller/Chip, kein „WLAN 6“).
  - Filter „Bootloader bleibt unangetastet“ entfernt; `risiko` bleibt in den Daten.
  - Kaufzeile der Karten „Kaufen: Geizhals · eBay · Kleinanzeigen“ (keine Floskel „neu oder
    gebraucht“ auf den Karten; in der Einleitung bleibt sie, adorfer).
  - `preise-holen.py`: mindestens 3 Angebote, jede Seite eine Logzeile, Sperre gegen doppelten Lauf.
- Neu erzeugen nach jeder Datenänderung: zuerst `werkzeug/lokale-pfade.py` (lokale Pfade aus
  Agentenläufen werden Links, Router-Werkstatt aufs GitLab, seit 22.10.2026), dann
  `werkzeug/selector-ansicht.py` und `werkzeug/geraeteliste.py --index <installer>/anleitungen/html/index.json`,
  dann committen, pushen, Deploy durch adorfer.
