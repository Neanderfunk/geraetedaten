#!/usr/bin/env python3
"""Ersetzt lokale Pfade (/home/.../projekte/freifunk/...) in daten/*.json durch Links.

Anlass (22.10.2026): Agenten haben eigene Belege als Pfad auf dem Arbeitsrechner
eingetragen, routerwahl zeigte sie oeffentlich an. Die Router-Werkstatt verlinken
wir auf unser GitLab, auch wenn dort nicht jeder lesen darf (adorfer: "etwas
Reklame fuer unsere selfhosted Dienste"); was auf GitHub liegt, dorthin.
Ohne Gegenstueck im Netz (uebergaben/) wird es ein Text ohne Pfad.

Aufruf: werkzeug/lokale-pfade.py [--pruefen]
  --pruefen  nur melden, nichts schreiben; Rueckgabe 1, wenn noch Pfade da sind
"""
import glob, json, os, re, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIELE = [   # lokales Verzeichnis unter projekte/freifunk -> (Basis-URL, Art)
    ('router-werkstatt', 'https://git.ideenwerk.me/neanderfunk/routerwerkstatt/-/{art}/main/', 'gitlab'),
    ('firmware-2025.1', 'https://github.com/Neanderfunk/FirmwareConfigs/{art}/v2025.1.x/', 'github'),
    ('FirmwareConfigs-2025.1', 'https://github.com/Neanderfunk/FirmwareConfigs/{art}/v2025.1.x/', 'github'),
    ('neanderfunk/gluon-patches-hardware', 'https://github.com/Neanderfunk/gluon-patches-hardware/{art}/v2025.1.x/', 'github'),
    ('geraetedaten', 'https://github.com/Neanderfunk/geraetedaten/{art}/main/', 'github'),
    ('rampe-anleitungen', 'https://github.com/Neanderfunk/gluon-rampe-installer/{art}/anleitungen/', 'github'),
]
PFAD = re.compile(r'/home/[^/\s"]+/projekte/freifunk/([^\s"#,;)]*)(#[^"]*?)?(?=$|["\s,;)])')


def anker(a, gitlab):
    """GitHub und GitLab bilden Anker aus der Ueberschrift: klein, Satzzeichen weg, Leerzeichen
    zu Bindestrichen."""
    a = a.lstrip('#').strip().lower()
    a = re.sub(r'[^\w\- ]', '', a)
    return '#' + a.replace(' ', '-')


# FirmwareConfigs: patches/ ist am 27.09.2026 nach gluon-patches-hardware umgezogen, gluon/ ist
# der Gluon-Baum im Bauverzeichnis (kein Teil des Repos).
PATCHES = 'https://github.com/Neanderfunk/gluon-patches-hardware/blob/v2025.1.x/'
UMZUG = {'devices': ('erx-ka-imagename',), 'targets': ('targets-',)}


def firmware_baum(pfad):
    if pfad.startswith('patches/'):
        name = pfad[len('patches/'):]
        for ordner, anfaenge in UMZUG.items():
            if name.startswith(anfaenge):
                return PATCHES + ordner + '/' + name
    if pfad.startswith('gluon/output/'):
        return 'eigener Testbau (' + pfad.rsplit('/', 1)[-1] + ')'
    if pfad == 'gluon/openwrt' or pfad.startswith('gluon/openwrt/'):
        rest = pfad[len('gluon/openwrt'):].lstrip('/')
        return 'https://github.com/openwrt/openwrt/' + ('blob' if rest else 'tree') + '/openwrt-24.10/' + rest
    if pfad == 'gluon' or pfad.startswith('gluon/'):
        rest = pfad[len('gluon'):].lstrip('/')
        art = 'blob' if '.' in rest.rsplit('/', 1)[-1] else 'tree'
        return 'https://github.com/freifunk-gluon/gluon/' + art + '/v2025.1.x/' + rest
    return None


def ersetzen(m):
    rest, a = m.group(1), m.group(2)
    for lokal in ('firmware-2025.1', 'FirmwareConfigs-2025.1'):
        if rest.startswith(lokal + '/'):
            url = firmware_baum(rest[len(lokal) + 1:])
            if url:
                return url + (anker(a, False) if a and url.startswith('http') else '')
    for lokal, basis, art in ZIELE:
        if rest == lokal or rest.startswith(lokal + '/'):
            pfad = rest[len(lokal):].lstrip('/')
            ordner = pfad == '' or pfad.endswith('/')
            url = basis.format(art='tree' if ordner else 'blob') + pfad
            return url + (anker(a, art == 'gitlab') if a else '')
    if rest.startswith('uebergaben'):
        return 'interne Uebergabenotiz Neanderfunk'
    return m.group(0)


def main():
    pruefen = '--pruefen' in sys.argv
    offen = 0
    for p in sorted(glob.glob(os.path.join(WURZEL, 'daten', '*.json'))):
        t = open(p, encoding='utf-8').read()
        neu = PFAD.sub(ersetzen, t)
        rest = PFAD.findall(neu)
        offen += len(rest)
        if rest:
            print('  offen', os.path.basename(p), rest[:3])
        if neu != t and not pruefen:
            json.loads(neu)   # bleibt gueltiges JSON?
            open(p, 'w', encoding='utf-8').write(neu)
            print('  ersetzt', os.path.basename(p), t.count('/home/') - neu.count('/home/'))
    print('noch lokale Pfade:', offen)
    return 1 if (pruefen and offen) else 0


if __name__ == '__main__':
    sys.exit(main())
