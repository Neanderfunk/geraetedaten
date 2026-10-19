#!/usr/bin/env python3
"""Sucht zu einem Gluon-Image-Namen passende Eintraege im OpenWrt-ToH-Dump.

    toh_suche.py <image> [--alle]        Kandidaten (hoechstens 6), mit --alle alle Spalten

Bewertet wird, wie viele Teile des Image-Namens (tp-link, archer, c7, v2)
in Hersteller + Modell + Version des ToH-Eintrags vorkommen. Das Ergebnis
ist ein Vorschlag; welcher Eintrag passt, entscheidet, wer es liest.
"""
import csv, glob, gzip, io, json, os, re, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(t):
    t = t.lower().replace('!', '').replace('+', 'plus')
    return re.sub(r'[^a-z0-9.]+', '-', t).strip('-')


def teile(t):
    return [x for x in norm(t).split('-') if x]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    image, alle = sys.argv[1], '--alle' in sys.argv
    dump = sorted(glob.glob(os.path.join(WURZEL, 'quellen', 'quellen-toh-*.tsv.gz')))[-1]
    rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(dump), encoding='utf-8', errors='replace'),
                               delimiter='\t'))
    ziel = teile(image)
    ziel_ohne_v = [x for x in ziel if not re.fullmatch(r'v\d+(\.\d+)?', x)]
    version = [x for x in ziel if re.fullmatch(r'v\d+(\.\d+)?', x)]
    kand = []
    for r in rows:
        hm = teile(r['brand'] + ' ' + r['model'])
        voll = '-'.join(hm)
        treffer = sum(1 for x in ziel_ohne_v if x in hm or x in voll)
        if not treffer or ziel[0] not in voll:
            continue
        score = treffer / max(len(ziel_ohne_v), 1) - 0.02 * max(0, len(hm) - len(ziel_ohne_v))
        rv = norm(r['version'])
        if version:
            v = version[0].lstrip('v')
            if rv and (rv.lstrip('v').split('.')[0] == v.split('.')[0] or v in rv):
                score += 0.3
            elif rv and rv not in ('null', '-'):
                score -= 0.3
        kand.append((score, r))
    kand.sort(key=lambda x: -x[0])
    aus = []
    for s, r in kand[:6]:
        if alle:
            aus.append({'score': round(s, 2), **r})
        else:
            aus.append({'score': round(s, 2), 'pid': r['pid'], 'brand': r['brand'], 'model': r['model'],
                        'version': r['version'], 'devicepage': r.get('devicepage', ''),
                        'page': r.get('page', '')})
    print(json.dumps({'dump': os.path.basename(dump), 'image': image, 'kandidaten': aus},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
