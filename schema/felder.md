# Aufbau eines Geräteeintrags

Ein Eintrag je Gluon-Image-Name, Datei `daten/<image>.json`. Grundsatz:
**Alles mitnehmen, was eine Quelle hergibt, und jeden Wert mit Quelle und
Stand belegen.** Groß werden darf die Datei. Gedeutet und gekürzt wird erst
beim Erzeugen der Selector-Ansicht.

```json
{
  "image": "cudy-wr3000-v1",
  "modell": "Cudy WR3000 v1",
  "quellen": {
    "toh": {"url": "https://openwrt.org/toh/hwdata/cudy/cudy_wr3000_v1",
            "stand": "Dump 2026-10-18", "abgerufen": "2026-10-19"},
    "deviwiki": {"url": "https://deviwiki.com/wiki/...", "stand": "Seitenrevision 2025-03-04",
                 "abgerufen": "2026-10-19"}
  },
  "roh": {
    "toh": {"cpu": "MediaTek MT7981B", "rammb": "256", "...": "..."},
    "deviwiki": {"FCC ID": "...", "...": "..."}
  },
  "felder": {
    "ram_mb": [
      {"wert": 256, "quelle": "toh", "beleg": "https://...", "stand": "Dump 2026-10-18",
       "sicherheit": "hoch", "bemerkung": ""}
    ]
  },
  "offene_faeden": [
    {"url": "https://fccid.io/...", "kategorie": "netzteil", "grund": "Foto des Netzteils, Spannung nicht im Text"}
  ],
  "lauf": {"datum": "2026-10-19", "status": "teilweise", "notiz": "..."}
}
```

- **`quellen`**: jede benutzte Quelle mit URL, Stand der Quelle (Seitenrevision,
  Dump-Datum, Dokumentdatum) und Abrufdatum.
- **`roh`**: je Quelle **alle** Kategorien, die sie hat, unverändert
  (Infobox, Tabellenspalten, Datenblattzeilen), auch solche, für die es unten
  kein Feld gibt.
- **`felder`**: normalisierte Werte. Je Feld eine **Liste**, ein Eintrag je
  Quelle. Widersprechen sich Quellen, stehen beide da. `sicherheit`: `hoch`
  (Datenblatt, Typenschild, eigene Messung), `mittel` (Wiki, ToH), `niedrig`
  (Forum, abgeleitet). Unbekannt ist erlaubt: dann das Feld weglassen und
  einen offenen Faden notieren. **Nie raten**, vor allem nicht bei PoE-Spannung,
  Hardware-Version, Flash und RAM.
- **`offene_faeden`**: jede URL, die noch Daten verspricht, aber nicht
  ausgewertet ist (FCC-Fotos, Anatel, Datenblatt-PDF, Forumsthread).

## Feldnamen (normalisiert)

Die Liste ist nicht abschließend. Weitere Kategorien aus Quellen kommen in
`roh` und dürfen auch als neues Feld in `felder` erscheinen.

| Gruppe | Felder |
|---|---|
| Erkennung | `hersteller`, `modell_name`, `hw_version`, `erkennung_typenschild` (woran man die Version erkennt), `fcc_id`, `anatel_id`, `andere_namen` |
| Rechner | `soc`, `cpu_kerne`, `cpu_mhz`, `cpu_arch`, `ram_mb`, `flash_mb`, `flash_typ` (NOR/NAND/eMMC) |
| WLAN | `wlan_chips`, `wlan_24_standard`, `wlan_24_streams`, `wlan_5_standard`, `wlan_5_streams`, `wlan_6_standard`, `wlan_6_streams`, `wlan_klasse` (z. B. AX3000), `wlan_wave2`, `wlan_sendeleistung_dbm` |
| Antennen | `antennen_art` (intern / extern fest / extern abnehmbar), `antennen_anschluss` (RP-SMA, N ...), `antennen_anzahl`, `antennen_je_band` (dualband / getrennt), `antennen_gewinn_dbi`, `antennen_charakteristik` (rund / Sektor / Richtfunk, Öffnungswinkel) |
| Anschlüsse | `ports` (Liste: Name, Geschwindigkeit, WAN/LAN), `ports_anzahl`, `nur_eine_buchse`, `sfp`, `usb` (Anzahl, Version), `modem` |
| Strom | `poe_eingang` (nein / 802.3af / 802.3at / 802.3bt / passiv), `poe_spannung_v`, `poe_ausgang`, `dc_buchse`, `dc_buchse_mass` (z. B. 5.5x2.1), `dc_spannung_v`, `dc_strom_a`, `netzteil_beiliegend`, `netzteil_daten`, `leistung_w_typ`, `leistung_w_max` |
| Einsatz | `einsatzort` (innen / außen), `ip_schutzart`, `temperatur_betrieb`, `montage` (Tisch / Wand / Decke / Mast), `montageloecher`, `abmessungen_mm`, `gewicht_g`, `luefter`, `led_abschaltbar`, `reset_knopf` (Lage, erreichbar) |
| Serielle Konsole | `seriell_zugang` (außen zugänglich / innen Stiftleiste / innen Lötpunkte / innen erst nach Nachbestücken von Widerständen oder Lötbrücken), `seriell_pinbelegung`, `seriell_pegel_v`, `seriell_baud`, `seriell_hinweis` |
| Firmware | `openwrt_target`, `openwrt_seit`, `bootloader`, `stock_firmware_url` |
| Verweise | `toh_seite`, `openwrt_wiki`, `deviwiki`, `wikidevi`, `hersteller_seite`, `datenblatt` |
| Handel | `ean` (je Variante/Region ein Eintrag, 13 Stellen), `amazon_asin` (je Marktplatz, `bemerkung: "amazon.de"`), `geizhals_url` (Permalink `https://geizhals.de/<name>-a<ID>.html`, ohne Suchparameter) |

**Hardware-Versionen:** Bei TP-Link und Mercusys bezeichnet die Stelle nach
dem Punkt (v1.1, V1.20) nur Firmware- und Bootloader-Stand, die Hardware ist
gleich; es zählt die Hauptversion. Ausnahme: TP-Link CPE210 v1.1 mit
signiertem Bootloader in getrennter EU- und US-Fassung (adorfer, 20.10.2026).

**Handel:** Die Felder dienen später für Preisvergleich und Links zu
Gebrauchtmärkten. Ein Geizhals-Eintrag deckt oft mehrere Hardware-Versionen
ab; das gehört dann in die `bemerkung`. EAN und ASIN nur übernehmen, wenn
die Quelle sie eindeutig diesem Modell und dieser Version zuordnet. Geizhals
selbst sperrt Abrufe; Permalinks findet man über das Webarchiv
(`https://web.archive.org/cdx/search/cdx?url=geizhals.de/<hersteller>-<modell>*&output=json&fl=original&collapse=urlkey`),
die EAN oft im archivierten Geizhals-Datenblatt oder im Hersteller-Datenblatt.

**Geizhals über heise:** `preisvergleich.heise.de` liefert dieselben Seiten wie
Geizhals (gleiche Artikelnummer `-a<ID>.html`) und sperrt nicht. Suche:
`https://preisvergleich.heise.de/?fs=<suchbegriff>&hloc=de`, Produktseite:
`https://preisvergleich.heise.de/<name>-a<ID>.html`. Gespeichert wird der
Geizhals-Permalink `https://geizhals.de/<name>-a<ID>.html`. Die Datenblatt-Tabelle
der Produktseite kommt unverändert nach `roh.geizhals` (Quelle `geizhals`,
`sicherheit: mittel`), daraus z. B. `netzteil_daten`, `leistung_w_max`,
`abmessungen_mm`, `antennen_anzahl`. Gilt ein Geizhals-Eintrag für mehrere
Hardware-Versionen („verschiedene Revisionen“), wird nur der Link übernommen,
keine versionsabhängigen Werte. Preise werden nicht gespeichert, sie veralten
täglich. Abrufe langsam: höchstens 3 je Gerät, mindestens 30 s Abstand
(das Freifunk-Wiki drosselt seinen Preisvergleich auf 5 je Minute).

Level, Risiko, Verwechslung, Kaufstatus und Anleitung kommen nicht von den
Agenten. Sie stehen im RAMpe-Inventar (gluon-rampe-installer) und werden
beim Erzeugen der Selector-Ansicht dazugenommen.
