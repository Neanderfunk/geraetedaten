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
- **`widerlegt`** (optional, je Eintrag): Ein Wert, der sich nach Prüfung als falsch
  herausgestellt hat, wird nicht gelöscht, sondern bekommt `"widerlegt": "<Begründung mit
  Beleg>"`. Die Anzeige übergeht ihn; wer nachliest, sieht, was einmal behauptet wurde
  und warum es nicht stimmt.
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

## Speicher für Updates (abgeleitet, nicht erfasst)

`werkzeug/selector-ansicht.py` bewertet Flash und RAM getrennt, angezeigt wird
die schlechtere der beiden Stufen: zu wenig, knapp, ausreichend, gut, reichlich.

- Flash (adorfer 21.10.2026): ab 8 MB knapp, 16 MB ausreichend, 32 MB gut,
  64 MB reichlich. Startet das Gerät von einer Speicherkarte, zählt der Flash
  als reichlich.
- RAM: Der Bedarf hängt vor allem am WLAN-Treiber, deshalb gelten Schwellen je
  Treiberklasse (Mindest-RAM für knapp / ausreichend / gut / reichlich, MB):

  | Klasse | erkannt an | Schwellen |
  |---|---|---|
  | WLAN 4/5 mit ath9k oder mt76 | alles andere | 64 / 128 / 256 / 512 |
  | WLAN 5 von Qualcomm (ath10k) | IPQ40xx, QCA988x, QCA9886/9888, QCA99xx | 128 / 256 / 512 / 1024 |
  | WLAN 6 von MediaTek | MT7915, MT7916, MT79xx | 128 / 256 / 512 / 1024 |
  | WLAN 6 von Qualcomm (ath11k) | IPQ807x, IPQ60xx, IPQ50xx, QCN90xx/61xx/50xx | 256 / 512 / 1024 / 2048 |
  | WLAN 7 | ath12k, IPQ53xx/95xx, MT799x | wie ath11k [abgeleitet] |

  Erkannt wird an `wlan_chips` und `soc`: zuerst der gewählte Wert, dann
  die übrigen Quellen, dort zählt eine größere Klasse aber nur, wenn
  mindestens zwei Quellen sie nennen (beim OM5P-AN nennt ein einzelnes
  Datenblatt die Chips des OM5P-AC). `wlan_treiber` nur als Rückfall, weil er
  öfter falsch ist. QCA98xx (QCA9880 bis QCA9896, auch AR9880/AR9882 und
  „QCA988x“ geschrieben) sind ath10k. Korrigiert am 22.10.2026 nach einer
  Nutzerfrage (UAP-AC-Pro „knapp“, baugleicher UAP-AC-M-Pro „ausreichend“):
  neun Geräte standen fälschlich eine Stufe zu gut. Drei
  Funkeinheiten (IPQ40xx oder IPQ807x mit Zusatzchip, MT7986 mit MT7915/MT7916)
  verdoppeln die Schwellen. Unter der Klassen-Schwelle bleibt es bei „knapp“,
  „zu wenig“ heißt höchstens 32 MB RAM oder unter 8 MB Flash.
- Geeicht an der RAM-Belegung (`memory_usage` aus meshviewer.json mal RAM laut
  Datenbank) der Knoten auf der Karte am 21.10.2026, Gluon 2023.2 und 2025.1:
  64-MB-Geräte mit ath9k oder mt76 sind um 85 % belegt, auch Single-Band wie
  die CPE210. Archer C7 v5 (ath10k, 128 MB) liegt unter 2025.1 um 87 %
  (2023.2: 66 %), Archer C6 v2 um 86 %. FRITZ!Box 4040 (IPQ4018, 256 MB) liegt
  um 60 %, MediaTek WLAN 6 mit 256 MB bei 40-55 %, Archer AX23 (WLAN 6 von
  MediaTek, 128 MB) bei 92 %, Aruba AP-303 (IPQ4029, 512 MB) um 28 %. ath11k
  mit 256 MB lehnen Gluon und OpenWrt grundsätzlich ab (adorfer).
- Abstriche: Wer die aktuelle Firmware nur gekürzt bekommt, ist höchstens
  „knapp“ und heißt dann „knapp, reduzierte Funktionalität“ (eigener
  Filterwert, adorfer 22.10.2026); die Erklärung nennt die Kürzungen. Die Feldmessung zeigt diese
  Geräte schon ohne die gestrichenen Funktionen, also mit zu wenig Bedarf.
  Quelle ist `quellen/firmware-abstriche.json`, erzeugt von
  `werkzeug/abstriche.py` aus FirmwareConfigs `image-customization.lua`
  (`lowmem_dualradio`, `lowmem_singleradio`, `lowflash`) und den Gluon-Targets
  (ath10k-smallbuffers). Ändern sich die Listen, `abstriche.py` neu laufen lassen.
