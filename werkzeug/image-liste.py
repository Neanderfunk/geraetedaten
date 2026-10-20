#!/usr/bin/env python3
"""Holt die Gluon-Geraetenamen eines Firmware-Zweigs vom Download-Server.

    image-liste.py <zweig> [domain]      z. B. image-liste.py stable
    image-liste.py <URL eines Laufs> [domain]
        z. B. https://imageslive.ffdus.de/images2025.1/images-1792163458/21_dias/21_dias
        -> quellen/images-lauf-<datum>.txt (alle gebauten Geraete des Laufs)

Liest die Verzeichnisse sysupgrade/ und factory/ unter
https://download.ffnef.de/firmware/<zweig>/<domain>/ (Vorgabe 21_dias; alle
Domains bauen dieselbe Geraeteliste) und schreibt die Namen sortiert nach
quellen/images-<zweig>-<datum>.txt. Dateinamen sehen so aus:
gluon-nef-<domain>-<version>-<geraet>-sysupgrade.bin; "-bootloader" bleibt
Teil des Namens (eigenes Image), wie in der bisherigen Liste.
"""
import datetime, os, re, sys, urllib.parse, urllib.request

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIS = "https://download.ffnef.de/firmware/{}/{}/{}/"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    zweig = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else "21_dias"
    namen, version = set(), set()
    muster = re.compile(r"gluon-nef-%s-([0-9A-Za-z.+~]+)-(.+?)-(sysupgrade|factory)(\.[A-Za-z0-9.]+)?$" % re.escape(domain))
    if zweig.startswith("http"):
        # Lauf auf imageslive (Buildsystem): .../images-<epoch>/<domain>/<domain>/ -
        # nur sysupgrade/, die Factory-Dateien tragen dort kein "-factory" im Namen.
        # sysupgrade/ enthaelt alle gebauten Geraete, auch BROKEN und disable_manifest.
        quellen = [zweig.rstrip("/") + "/sysupgrade/"]
        zweig = "lauf"
    else:
        quellen = [BASIS.format(zweig, domain, art) for art in ("sysupgrade", "factory")]
    for url in quellen:
        with urllib.request.urlopen(url, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
        for datei in {urllib.parse.unquote(d) for d in re.findall(r'href="[^"]*/(gluon-[^"/]+)"', text)}:
            m = muster.match(datei)
            if m:
                version.add(m.group(1))
                namen.add(m.group(2))
    if not namen:
        sys.exit("keine Images gefunden unter " + BASIS.format(zweig, domain, "*"))
    ziel = os.path.join(WURZEL, "quellen", "images-%s-%s.txt" % (zweig, datetime.date.today().isoformat()))
    with open(ziel, "w") as f:
        f.write("\n".join(sorted(namen)) + "\n")
    print("%s: %d Geraete, Version %s -> %s" % (zweig, len(namen), ", ".join(sorted(version)), ziel))


if __name__ == "__main__":
    main()
