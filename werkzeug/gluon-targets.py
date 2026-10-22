#!/usr/bin/env python3
"""Ordnet jedem Gluon-Image sein Gluon-Target zu (mediatek-filogic, ath79-generic, ...).

Quelle sind die Target-Dateien eines Gluon-Klons (targets/<target>, device('name', ...) samt
aliases) und die Geraete, die unsere Patches dazulegen (gluon-patches-hardware, alle *.patch mit Abschnitten fuer targets/,
Zeilen "+device('name'" in "+++ b/targets/<target>"). Ergebnis: quellen/gluon-targets.json,
daraus setzt selector-ansicht.py die Facette "plattform" (Filter auf routerwahl, Nutzerwunsch
22.10.2026: "alle mediatek-filogic-Geraete").

Aufruf: werkzeug/gluon-targets.py <gluon-klon> <gluon-patches-hardware-klon>
"""
import glob, json, os, re, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV = re.compile(r"device\(\s*'([^']+)'")
ALIAS = re.compile(r"aliases\s*=\s*\{([^}]*)\}")


def aus_text(text, target, ziel):
    # Aliase auch ausserhalb eines device(...) (Patch fuegt nur die Alias-Zeile hinzu)
    for a in ALIAS.findall(text):
        for n in re.findall(r"'([^']+)'", a):
            ziel[n] = target
    # device(...)-Bloecke grob trennen: alles bis zum naechsten device(
    teile = re.split(r"(?=device\(\s*')", text)
    for t in teile:
        m = DEV.match(t)
        if not m:
            continue
        ziel[m.group(1)] = target
        for a in ALIAS.findall(t):
            for n in re.findall(r"'([^']+)'", a):
                ziel[n] = target


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    gluon, patches = sys.argv[1], sys.argv[2]
    ziel = {}
    for p in sorted(glob.glob(os.path.join(gluon, 'targets', '*'))):
        name = os.path.basename(p)
        if name in ('generic', 'targets.mk') or name.endswith('.inc') or os.path.isdir(p):
            continue
        aus_text(open(p, encoding='utf-8').read(), name, ziel)
    for p in sorted(glob.glob(os.path.join(patches, '**', '*.patch'), recursive=True)):
        target, plus = None, []
        for z in open(p, encoding='utf-8'):
            m = re.match(r'\+\+\+ b/targets/(\S+)', z)
            if m:
                if target and plus:
                    aus_text(''.join(plus), target, ziel)
                target, plus = m.group(1), []
            elif target and z.startswith('+') and not z.startswith('+++'):
                plus.append(z[1:])
        if target and plus:
            aus_text(''.join(plus), target, ziel)
    aus = os.path.join(WURZEL, 'quellen', 'gluon-targets.json')
    json.dump(dict(sorted(ziel.items())), open(aus, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(aus, 'a').write('\n')
    print(len(ziel), 'Images ->', aus)


if __name__ == '__main__':
    main()
