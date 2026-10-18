#!/usr/bin/env python3
"""Erzeugt aus daten/*.json die kompakte Ansicht fuer den Firmware-Selector.

    selector-ansicht.py [--index <anleitungen/html/index.json>] [--aus <verzeichnis>]

Ausgabe: <verzeichnis>/<image>.json je Geraet und <verzeichnis>/index.json
(Liste der Images mit Modellname). Der Selector laedt die Geraetedatei erst,
wenn das Geraet gewaehlt ist. Level und Risiko holt er selbst aus
anleitungen/index.json; --index nimmt sie zusaetzlich in die Dateien auf.

Je Feld wird ein Wert ausgewaehlt: die Gruppe gleicher Werte mit der hoechsten
Sicherheit, bei Gleichstand die mit den meisten Quellen. Andere Werte bleiben
als "abweichend" sichtbar, mit ihren Quellen. Level und Risiko kommen aus der
index.json der Anleitungen (gluon-rampe-installer), wenn sie angegeben ist.
"""
import argparse, glob, json, os, re

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
REPO_URL = 'https://github.com/Neanderfunk/geraetedaten/blob/main/daten/'
RANG = {'hoch': 3, 'mittel': 2, 'niedrig': 1}


def text(w):
    """Beliebigen Wert lesbar machen."""
    if w is None:
        return ''
    if isinstance(w, bool):
        return 'ja' if w else 'nein'
    if isinstance(w, float):
        return ('%g' % w)
    if isinstance(w, (int, str)):
        return str(w).strip()
    if isinstance(w, list):
        return ', '.join(t for t in (text(x) for x in w) if t)
    if isinstance(w, dict):
        return ' '.join(t for t in (text(v) for v in w.values()) if t)
    return str(w)


def schluessel(t):
    t = t.lower().strip().rstrip('.')
    t = re.sub(r'(\d)\.0\b', r'\1', t)
    return re.sub(r'\s+', ' ', t)


FAKT = {'ram_mb', 'flash_mb', 'cpu_mhz', 'cpu_kerne', 'poe_spannung_v', 'dc_spannung_v', 'dc_strom_a',
        'dc_buchse_mass', 'ip_schutzart', 'temperatur_betrieb', 'einsatzort', 'wlan_24_streams',
        'wlan_5_streams', 'antennen_anzahl', 'ports_anzahl', 'fcc_id', 'leistung_w_max', 'leistung_w_typ',
        'netzteil_beiliegend', 'nur_eine_buchse'}


def auswahl(eintraege, quellen, fakt=False):
    """Liste von Quellen-Eintraegen -> {wert, abweichend, belege} oder None."""
    gruppen = {}
    for e in eintraege if isinstance(eintraege, list) else [eintraege]:
        if not isinstance(e, dict):
            e = {'wert': e}
        t = text(e.get('wert'))
        if not t or schluessel(t).strip('"()- ') in ('unbekannt', 'unknown', 'none', 'null', '', '?',
                                                    'keins', 'keine', 'kein', 'keins ("-")'):
            continue
        q = e.get('quelle') or ''
        qinfo = quellen.get(q, {}) if isinstance(quellen.get(q), dict) else {}
        beleg = {'quelle': q, 'url': e.get('beleg') or e.get('url') or qinfo.get('url', ''),
                 'stand': e.get('stand') or qinfo.get('stand', ''),
                 'sicherheit': e.get('sicherheit') or ''}
        g = gruppen.setdefault(schluessel(t), {'wert': t, 'belege': [], 'rang': 0})
        g['belege'].append(beleg)
        g['rang'] = max(g['rang'], RANG.get(beleg['sicherheit'], 0))
    if not gruppen:
        return None
    sortiert = sorted(gruppen.values(), key=lambda g: (-g['rang'], -len(g['belege'])))
    beste = sortiert[0]
    belege, abweichend = list(beste['belege']), []
    weitere = []
    for g in sortiert[1:]:
        if vertraeglich(beste['wert'], g['wert']):
            belege += g['belege']        # dasselbe, nur anders oder genauer gesagt
        elif fakt:
            abweichend.append({'wert': g['wert'], 'belege': g['belege']})
        else:
            weitere.append({'wert': g['wert'], 'belege': g['belege']})   # ergaenzt, widerspricht nicht
    return {'wert': beste['wert'], 'belege': belege, 'abweichend': abweichend, 'weitere': weitere}


def zahlen(t):
    return set(re.findall(r'\d+(?:\.\d+)?', t.replace(',', '.')))


def vertraeglich(a, b):
    """Widersprechen sich zwei Angaben? Nein, wenn die eine in der anderen
    steckt oder die Zahlen der kuerzeren alle in der laengeren vorkommen."""
    ka, kb = schluessel(a), schluessel(b)
    if ka in kb or kb in ka:
        return True
    za, zb = zahlen(ka), zahlen(kb)
    kurz, lang = (za, zb) if len(ka) <= len(kb) else (zb, za)
    return bool(kurz) and kurz <= lang


def zahl(sel):
    if not sel:
        return None
    m = re.search(r'\d+(?:\.\d+)?', sel['wert'])
    return float(m.group()) if m else None


def zeile(titel, sel, zusatz=None):
    if not sel:
        return None
    z = {'titel': titel, 'wert': sel['wert'], 'belege': sel['belege'],
         'abweichend': sel['abweichend'], 'weitere': sel.get('weitere', [])}
    if zusatz:
        z['wert'] += ' ' + zusatz
    return z


def kombi(titel, teile):
    """Mehrere Felder zu einer Zeile: teile = [(beschriftung, sel)]."""
    werte, belege, abw, weitere = [], [], [], []
    for besch, sel in teile:
        if not sel:
            continue
        vor = besch + ' ' if besch else ''
        werte.append(vor + sel['wert'])
        belege += sel['belege']
        for a in sel['abweichend']:
            abw.append({'wert': vor + a['wert'], 'belege': a['belege']})
        for a in sel.get('weitere', []):
            weitere.append({'wert': vor + a['wert'], 'belege': a['belege']})
    if not werte:
        return None
    return {'titel': titel, 'wert': '; '.join(werte), 'belege': belege, 'abweichend': abw,
            'weitere': weitere}


def ansicht(d, idx):
    f, q = d.get('felder', {}), d.get('quellen', {})
    s = {k: auswahl(v, q, k in FAKT) for k, v in f.items()}
    oben, mitte, technik = [], [], []

    ram, flash = zahl(s.get('ram_mb')), zahl(s.get('flash_mb'))
    if ram and flash:
        if flash >= 16 and ram >= 128:
            stufe = 'reicht'
        elif flash >= 8 and ram >= 64:
            stufe = 'knapp'
        else:
            stufe = 'sackgasse'
        oben.append({'titel': 'Firmware-Zukunft', 'stufe': stufe,
                     'wert': {'reicht': 'reicht für die aktuelle Firmware',
                              'knapp': 'knapp: läuft, aber wenig Reserve für künftige Versionen',
                              'sackgasse': 'nur noch alte Firmware (Sackgasse)'}[stufe],
                     'erklaerung': '%g MB Flash, %g MB RAM' % (flash, ram),
                     'belege': (s['flash_mb']['belege'] + s['ram_mb']['belege']),
                     'abweichend': [{**a, 'wert': 'Flash ' + a['wert'] + ' MB'} for a in s['flash_mb']['abweichend']] + [{**a, 'wert': 'RAM ' + a['wert'] + ' MB'} for a in s['ram_mb']['abweichend']], 'weitere': []})
    a = idx.get(d['image'])
    if a:
        oben.append({'titel': 'Installation', 'wert': 'Level %s, Risiko %s, %s' % (
            a.get('level', '?'), a.get('risiko', '?'), a.get('status', '?')),
            'belege': [{'quelle': 'anleitung', 'url': a.get('url', ''), 'stand': '', 'sicherheit': 'hoch'}],
            'abweichend': [], 'weitere': []})
    aussen = s.get('einsatzort') and 'au' in schluessel(s['einsatzort']['wert'])
    oben.append(kombi('Einsatzort', [('', s.get('einsatzort'))] +
                      ([('Schutzart', s.get('ip_schutzart')), ('Betrieb', s.get('temperatur_betrieb'))]
                       if aussen else [])))
    oben.append(kombi('Stromversorgung', [
        ('PoE', s.get('poe_eingang')), ('PoE-Spannung', s.get('poe_spannung_v')),
        ('Netzteil', s.get('dc_spannung_v') and {**s['dc_spannung_v'], 'wert': s['dc_spannung_v']['wert'] + ' V'}),
        ('Buchse', s.get('dc_buchse_mass')), ('Netzteil dabei', s.get('netzteil_beiliegend'))]))
    oben.append(zeile('Hardware-Version erkennen', s.get('erkennung_typenschild')))

    mitte.append(kombi('WLAN', [
        ('2.4 GHz', s.get('wlan_24_standard')), ('Streams', s.get('wlan_24_streams')),
        ('5 GHz', s.get('wlan_5_standard')), ('Streams', s.get('wlan_5_streams')),
        ('6 GHz', s.get('wlan_6_standard')), ('Klasse', s.get('wlan_klasse'))]))
    ports = kombi('Anschlüsse', [('', s.get('ports')), ('Anzahl', s.get('ports_anzahl'))])
    if ports and s.get('nur_eine_buchse') and schluessel(s['nur_eine_buchse']['wert']) == 'ja':
        ports['warnung'] = 'Nur eine Netzwerkbuchse: Sie ist der Uplink.'
    mitte.append(ports)
    mitte.append(kombi('Antennen', [('', s.get('antennen_art')), ('Anzahl', s.get('antennen_anzahl')),
                                    ('Anschluss', s.get('antennen_anschluss')),
                                    ('je Band', s.get('antennen_je_band'))]))

    for titel, teile in [
        ('Prozessor', [('', s.get('soc')), ('Kerne', s.get('cpu_kerne')), ('MHz', s.get('cpu_mhz'))]),
        ('Speicher', [('RAM MB', s.get('ram_mb')), ('Flash MB', s.get('flash_mb')), ('', s.get('flash_typ'))]),
        ('Leistungsaufnahme', [('typisch W', s.get('leistung_w_typ')), ('max. W', s.get('leistung_w_max'))]),
        ('Montage', [('', s.get('montage')), ('Löcher', s.get('montageloecher'))]),
        ('USB', [('', s.get('usb'))]),
        ('Serielle Konsole', [('', s.get('seriell_zugang')), ('Belegung', s.get('seriell_pinbelegung')),
                              ('', s.get('seriell_baud')), ('Pegel V', s.get('seriell_pegel_v')),
                              ('Hinweis', s.get('seriell_hinweis'))]),
        ('Lüfter', [('', s.get('luefter'))]),
        ('Reset-Knopf', [('', s.get('reset_knopf'))]),
        ('LEDs abschaltbar', [('', s.get('led_abschaltbar'))]),
        ('Abmessungen mm', [('', s.get('abmessungen_mm')), ('Gewicht g', s.get('gewicht_g'))]),
        ('FCC-ID', [('', s.get('fcc_id'))]),
    ]:
        technik.append(kombi(titel, teile))

    links = []
    for k, name in [('toh_seite', 'OpenWrt-ToH'), ('openwrt_wiki', 'OpenWrt-Wiki'), ('deviwiki', 'DeviWiki'),
                    ('wikidevi', 'WikiDevi'), ('hersteller_seite', 'Hersteller'), ('datenblatt', 'Datenblatt')]:
        if s.get(k) and s[k]['wert'].startswith('http'):
            links.append({'name': name, 'url': s[k]['wert']})
    links.append({'name': 'Alle Daten mit Quellen', 'url': REPO_URL + d['image'] + '.json'})

    return {'modell': d.get('modell', d['image']), 'stand': d.get('lauf', {}).get('datum', ''),
            'oben': [z for z in oben if z], 'mitte': [z for z in mitte if z],
            'technik': [z for z in technik if z], 'links': links}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', help='anleitungen/html/index.json aus gluon-rampe-installer')
    ap.add_argument('--aus', default=os.path.join(WURZEL, 'ausgabe', 'selector'))
    a = ap.parse_args()
    idx = {}
    if a.index:
        for e in json.load(open(a.index, encoding='utf-8')):
            idx[e['gluon_name']] = e
    os.makedirs(a.aus, exist_ok=True)
    liste = {}
    for p in sorted(glob.glob(os.path.join(WURZEL, 'daten', '*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        v = ansicht(d, idx)
        v.update({'image': d['image'], 'quelle': 'https://github.com/Neanderfunk/geraetedaten',
                  'lizenz': 'CC BY-SA 4.0'})
        with open(os.path.join(a.aus, d['image'] + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(v, fh, ensure_ascii=False, separators=(',', ':'))
        liste[d['image']] = {'modell': v['modell'], 'stand': v['stand']}
    with open(os.path.join(a.aus, 'index.json'), 'w', encoding='utf-8') as fh:
        json.dump({'quelle': 'https://github.com/Neanderfunk/geraetedaten', 'lizenz': 'CC BY-SA 4.0',
                   'geraete': liste}, fh, ensure_ascii=False, indent=1)
    print(a.aus, len(liste), 'Geraete')


if __name__ == '__main__':
    main()
