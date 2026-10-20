#!/usr/bin/env python3
"""Sucht Unstimmigkeiten in daten/*.json und schreibt einen Bericht.

    werkzeug/pruefen.py [--aus laeufe/pruefung-<datum>.md]

Prueft:
  1. Aufbau: Dateiname = image, felder als Listen von Eintraegen mit wert/quelle
  2. Widersprueche zwischen Quellen bei Fakten (RAM, Flash, Kerne, Streams,
     Buchsen, PoE, Einsatzort, Leistung ...), wie selector-ansicht.py sie sieht
  3. Unplausible Werte (RAM, Flash, Leistung, Streams, Buchsen, Kerne)
  4. Hardware-Version im Image-Namen vs. hw_version-Eintraege
  5. WLAN-Klasse (AX/AC/N) vs. WLAN-Generation
  6. PoE "nein" und trotzdem PoE-Spannung
  7. Geizhals: derselbe Artikel "genau" bei verschiedenen Modellen; Artikelname
     ohne Modellbezeichnung
Der Bericht ist eine Arbeitsliste, kein Urteil: jede Zeile nennt die Werte
und Quellen, entscheiden muss, wer nachsieht.
"""
import argparse, collections, datetime, glob, importlib.util, json, os, re, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("sa", os.path.join(WURZEL, "werkzeug", "selector-ansicht.py"))
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)

WIDERSPRUCH = ["ram_mb", "flash_mb", "cpu_kerne", "cpu_mhz", "soc", "wlan_24_streams", "wlan_5_streams",
               "ports_anzahl", "poe_eingang", "poe_spannung_v", "einsatzort", "dc_spannung_v",
               "leistung_w_max", "ip_schutzart", "netzteil_beiliegend", "antennen_anzahl"]


def kurz(sel):
    return "; ".join("%s (%s)" % (g["wert"], ", ".join(sorted({b["quelle"] for b in g["belege"]})))
                     for g in [sel] + sel["abweichend"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aus", default=os.path.join(WURZEL, "laeufe", "pruefung-%s.md" % datetime.date.today().isoformat()))
    a = ap.parse_args()
    befunde = collections.defaultdict(list)   # abschnitt -> [zeile]
    geizhals = collections.defaultdict(list)
    md = sorted(glob.glob(os.path.join(WURZEL, "quellen", "selector-modelle-*.json")))
    if md:
        sa.MODELLE.update(json.load(open(md[-1], encoding="utf-8"))["modelle"])
    n = 0
    for p in sorted(glob.glob(os.path.join(WURZEL, "daten", "*.json"))):
        name = os.path.basename(p)[:-5]
        try:
            d = json.load(open(p, encoding="utf-8"))
        except ValueError as e:
            befunde["1 Aufbau"].append("`%s`: kein gültiges JSON (%s)" % (name, e))
            continue
        n += 1
        if d.get("image") != name:
            befunde["1 Aufbau"].append("`%s`: image = %r" % (name, d.get("image")))
        f, q = d.get("felder", {}), d.get("quellen", {})
        for k, v in f.items():
            if not isinstance(v, list) or any(not isinstance(e, dict) or "wert" not in e or not e.get("quelle") for e in v):
                befunde["1 Aufbau"].append("`%s`: Feld %s ist keine Liste von {wert, quelle}" % (name, k))
        s = {k: sa.auswahl(v, q, k in sa.FAKT or k in WIDERSPRUCH) for k, v in f.items()}

        # 2 Widersprueche
        for k in WIDERSPRUCH:
            sel = s.get(k)
            if sel and sel["abweichend"]:
                befunde["2 Widersprüche zwischen Quellen"].append("`%s` %s: %s" % (name, k, kurz(sel)))

        # 3 Plausibilitaet
        fa = sa.facetten(d)
        def melde(text):
            befunde["3 Unplausible Werte"].append("`%s`: %s" % (name, text))
        if fa.get("ram") and not 16 <= fa["ram"] <= 8192:
            melde("RAM %s MB" % fa["ram"])
        if fa.get("flash") and not fa.get("sd") and not 2 <= fa["flash"] <= 131072:
            melde("Flash %s MB" % fa["flash"])
        if fa.get("ram") and fa.get("flash") and fa["ram"] >= 64 and fa["flash"] < 4 and not fa.get("sd"):
            melde("Flash %s MB bei %s MB RAM" % (fa["flash"], fa["ram"]))
        if fa.get("leistung") and not 1 <= fa["leistung"] <= 80:
            melde("Leistung %s W" % fa["leistung"])
        if fa.get("streams") and fa["streams"] > 8:
            melde("%s Streams" % fa["streams"])
        if fa.get("ports") and fa["ports"] > 52:
            melde("%s Buchsen" % fa["ports"])
        if fa.get("kerne") and fa["kerne"] > 8:
            melde("%s Kerne" % fa["kerne"])
        if fa.get("ram") and fa["ram"] not in (16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096, 8192):
            melde("RAM %s MB ist keine übliche Größe" % fa["ram"])

        # 4 Hardware-Version
        m = re.search(r"-(v\d+)(?:\.\d+)?(?:-|$)", name)
        if m:
            soll = m.group(1).lower()
            for e in f.get("hw_version", []):
                w = sa.text(e.get("wert") if isinstance(e, dict) else e)
                vs = {x.lower() for x in re.findall(r"\b[vV](?:er(?:sion)?[:.]?\s*)?(\d+)(?:\.\d+)?\b", w)}
                vs = {"v" + x for x in vs}
                if vs and soll not in vs:
                    befunde["4 Hardware-Version passt nicht zum Image"].append(
                        "`%s`: hw_version %r (%s)" % (name, w[:80], e.get("quelle") if isinstance(e, dict) else ""))

        # 5 WLAN-Klasse vs Generation
        kl = s.get("wlan_klasse")
        if kl and fa.get("wlan"):
            k = sa.schluessel(kl["wert"])
            erwartet = 7 if re.search(r"\bbe\d", k) else 6 if re.search(r"\bax\d", k) else 5 if re.search(r"\bac\d", k) else 4 if re.search(r"\bn\d", k) else None
            if erwartet and erwartet != fa["wlan"]:
                befunde["5 WLAN-Klasse vs. Generation"].append(
                    "`%s`: Klasse %s, Generation WLAN %s" % (name, kl["wert"], fa["wlan"]))

        # 6 PoE
        if fa.get("poe") == ["nein"] and s.get("poe_spannung_v"):
            befunde["6 PoE widersprüchlich"].append("`%s`: PoE nein, aber Spannung %s" % (name, s["poe_spannung_v"]["wert"]))

        # 7 Geizhals
        l = d.get("lauf", {}).get("geizhals") or {}
        for e in f.get("geizhals_url", []):
            url = e.get("wert", "")
            geizhals[url].append((name, l.get("zuordnung"), d.get("modell", "")))

    for url, wer in sorted(geizhals.items()):
        genau = [w for w in wer if w[1] == "genau"]
        if len(genau) > 1:
            # Varianten desselben Modells (z. B. -16m/-8m) sind erlaubt: nur melden, wenn Grundnamen verschieden
            grund = {re.sub(r"-(v\d+.*|\d+m|nor|lite|ka)$", "", w[0]) for w in genau}
            if len(grund) > 1:
                befunde["7 Geizhals-Artikel mehrfach als „genau“"].append(
                    "%s: %s" % (url, ", ".join("`%s`" % w[0] for w in genau)))
        slug = re.sub(r"-a\d+\.html$", "", url.rsplit("/", 1)[-1])
        for w in wer:
            teile = [t for t in re.split(r"[-_]", re.sub(r"^[a-z0-9.]+?-", "", w[0])) if re.search(r"\d", t) and not re.fullmatch(r"v\d+", t)]
            if teile and not any(t.replace(".", "") in slug.replace("-", "") for t in teile):
                befunde["7 Geizhals-Artikel ohne Modellnummer im Namen"].append("`%s` → %s" % (w[0], url))

    with open(a.aus, "w", encoding="utf-8") as fh:
        fh.write("# Prüfung der Gerätedaten (%s)\n\n" % datetime.date.today().isoformat())
        fh.write("Erzeugt von `werkzeug/pruefen.py` über %d Einträge. Arbeitsliste, kein Urteil.\n\n" % n)
        for abschnitt in sorted(befunde):
            fh.write("## %s (%d)\n\n" % (abschnitt, len(befunde[abschnitt])))
            for z in befunde[abschnitt]:
                fh.write("- %s\n" % z)
            fh.write("\n")
    for abschnitt in sorted(befunde):
        print("%-50s %d" % (abschnitt, len(befunde[abschnitt])))
    print("Bericht:", a.aus)


if __name__ == "__main__":
    main()
