#!/usr/bin/env python3
"""Erzeugt GERAETE.md: alle Geraete, fuer die wir Images bauen, mit Stand der Daten.

    geraeteliste.py [--index <anleitungen/html/index.json>]

Quellen im Repo:
  quellen/images-testing-*.txt     Image-Namen vom Firmware-Server (neueste Datei, werkzeug/image-liste.py)
  quellen/selector-modelle-*.json  Hersteller/Modell/Version aus devices.js (neueste Datei)
  daten/*.json                     vorhandene Eintraege

Fehlt ein Eintrag, verlinkt die Tabelle auf GitHubs "neue Datei" mit einer
fertig vorbelegten Vorlage, damit Dritte ohne Vorwissen anfangen koennen.
"""
import argparse, glob, json, os, re, urllib.parse

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'https://github.com/Neanderfunk/geraetedaten'


def neueste(muster):
    d = sorted(glob.glob(os.path.join(WURZEL, 'quellen', muster)))
    return d[-1] if d else None


def modell_zu(image, modelle):
    """Image -> (Hersteller, Modell mit Version, Kategorie)."""
    if image in modelle:
        m = modelle[image]
        return m['hersteller'], (m['modell'] + (' ' + m['version'] if m.get('version') else '')).strip(), m['kategorie']
    best = None
    for basis, m in modelle.items():
        if m.get('art') == 'basis' and image.startswith(basis + '-') and (not best or len(basis) > len(best[0])):
            best = (basis, m)
    if best:
        basis, m = best
        return m['hersteller'], m['modell'] + ' ' + image[len(basis) + 1:], m['kategorie']
    return image.split('-')[0].capitalize(), image, ''


def vorlage(image, modell):
    """Knappe Vorlage; Beispiele fuer Quellen und Felder stehen in schema/felder.md."""
    return json.dumps({'image': image, 'modell': modell, 'quellen': {}, 'roh': {}, 'felder': {},
                       'offene_faeden': [],
                       'lauf': {'datum': '', 'status': 'teilweise', 'notiz': 'von Hand, siehe schema/felder.md'}},
                      ensure_ascii=False, indent=1) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', help='anleitungen/html/index.json aus gluon-rampe-installer')
    a = ap.parse_args()
    # Grundlage ist der letzte Lauf des Buildsystems (werkzeug/image-liste.py <URL>):
    # er hat alle gebauten Geraete; Testzweig und aeltere Listen nur als Rueckfall.
    imgdatei = neueste('images-lauf-*.txt') or neueste('images-testing-*.txt') or neueste('images-*.txt')
    modelldatei = neueste('selector-modelle-*.json')
    images = [z.strip() for z in open(imgdatei) if z.strip() and not z.startswith('#')]
    modelle = json.load(open(modelldatei))['modelle']
    idx = {}
    if a.index:
        idx = {e['gluon_name']: e for e in json.load(open(a.index, encoding='utf-8'))}
    daten = {}
    for p in glob.glob(os.path.join(WURZEL, 'daten', '*.json')):
        try:   # waehrend eines Laufs kann eine Datei gerade halb geschrieben sein
            d = json.load(open(p, encoding='utf-8'))
            d['image']
        except (ValueError, KeyError, TypeError) as e:
            print('uebersprungen (unvollstaendig):', os.path.basename(p), e)
            continue
        daten[d['image']] = d

    zeilen = {}
    for img in sorted(set(images) | set(daten)):
        h, m, kat = modell_zu(img, modelle)
        zeilen.setdefault(h, []).append((m, img, kat))

    erfasst = sum(1 for i in images if i in daten)
    out = ['# Geräteliste', '',
           'Alle Geräte, für die Neanderfunk Gluon-Images baut, mit dem Stand ihrer Daten.',
           'Erzeugt von `werkzeug/geraeteliste.py`, nicht von Hand ändern.', '',
           '- Image-Namen: `%s`' % os.path.relpath(imgdatei, WURZEL),
           '- Modellnamen: `%s`' % os.path.relpath(modelldatei, WURZEL),
           '- **%d von %d Geräten erfasst.**' % (erfasst, len(images)), '',
           'Mithelfen: Bei einem Gerät ohne Daten führt „anlegen“ auf GitHub zu einer neuen Datei',
           'mit fertiger Vorlage. Aufbau und Feldnamen stehen in [schema/felder.md](schema/felder.md).',
           'Jeder Wert braucht eine Quelle mit Link; was keine Quelle belegt, bleibt weg.', '']
    for h in sorted(zeilen, key=str.lower):
        out += ['## ' + h, '', '| Gerät | Image | Daten | Level | Kategorie |', '|---|---|---|---|---|']
        for m, img, kat in sorted(zeilen[h], key=lambda x: x[0].lower()):
            if img in daten:
                d = daten[img]
                st = d.get('lauf', {}).get('status', '')
                zelle = '[erfasst](daten/%s.json): %d Felder, %d offene Fäden%s' % (
                    img, len(d.get('felder', {})), len(d.get('offene_faeden', [])), (', ' + st) if st else '')
            else:
                url = '%s/new/main/daten?filename=%s.json&value=%s' % (
                    REPO, urllib.parse.quote(img), urllib.parse.quote(vorlage(img, h + ' ' + m)))
                zelle = '[anlegen](%s)' % url
            lv = idx.get(img, {}).get('level', '')
            if lv and idx[img].get('url'):
                lv = '[%s](%s)' % (lv, idx[img]['url'])
            out.append('| %s | `%s` | %s | %s | %s |' % (m, img, zelle, lv, kat.replace('_', ' ')))
        out.append('')
    with open(os.path.join(WURZEL, 'GERAETE.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out))
    print('GERAETE.md:', len(images), 'Images,', erfasst, 'erfasst')


if __name__ == '__main__':
    main()
