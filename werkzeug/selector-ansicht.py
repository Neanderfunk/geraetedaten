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


UMLAUTE = [('aussen', 'außen'), ('Aussen', 'Außen'), ('rueck', 'rück'), ('Rueck', 'Rück'),
           ('gehaeuse', 'gehäuse'), ('Gehaeuse', 'Gehäuse'), ('schluessel', 'schlüssel'),
           ('Schluessel', 'Schlüssel'), ('loet', 'löt'), ('Loet', 'Löt'), ('luefter', 'lüfter'),
           ('Luefter', 'Lüfter'), ('fuer ', 'für '), ('Fuer ', 'Für '), ('ueber', 'über'),
           ('Ueber', 'Über'), ('waerme', 'wärme'), ('Waerme', 'Wärme'), ('kuehl', 'kühl'),
           ('Kuehl', 'Kühl'), ('haeng', 'häng'), ('unterstuetz', 'unterstütz'), ('geschaetzt', 'geschätzt'),
           ('hoehe', 'höhe'), ('groesse', 'größe'), ('Groesse', 'Größe'), ('laenge', 'länge'),
           ('fuehr', 'führ'), ('Fuehr', 'Führ'), ('oeffn', 'öffn'), ('Oeffn', 'Öffn'), ('moeglich', 'möglich'),
           ('koenn', 'könn'), ('muess', 'müss'), ('waehrend', 'während'), ('naechst', 'nächst'),
           ('Platinenrueck', 'Platinenrück'), ('Knoepf', 'Knöpf'), ('knoepf', 'knöpf'), ('Abstaend', 'Abständ'),
           ('abstaend', 'abständ'), ('Gerae', 'Geräte'[:4]), ('gerae', 'gerä'), ('aehnlich', 'ähnlich'),
           ('spaeter', 'später'), ('frueh', 'früh'), ('Frueh', 'Früh'), ('pruef', 'prüf'), ('Pruef', 'Prüf'),
           ('zurueck', 'zurück'), ('Zurueck', 'Zurück'), ('drueck', 'drück'), ('Drueck', 'Drück'),
           ('Stoer', 'Stör'), ('stoer', 'stör'), ('schraeg', 'schräg'), ('Schraeg', 'Schräg'),
           ('waehl', 'wähl'), ('Waehl', 'Wähl'), ('gross', 'groß'), ('Gross', 'Groß'),
           ('Hoehe', 'Höhe'), ('koerper', 'körper'), ('bestueck', 'bestück'), ('Bestueck', 'Bestück'),
           ('zusaetz', 'zusätz'), ('Zusaetz', 'Zusätz'), ('schliess', 'schließ'), ('Schliess', 'Schließ'),
           ('aendert', 'ändert'), ('Aender', 'Änder'), ('aender', 'änder'), ('saetz', 'sätz')]


def deutsch(t):
    for a, b in UMLAUTE:
        t = t.replace(a, b)
    return t


def text(w):
    """Beliebigen Wert lesbar machen."""
    if w is None:
        return ''
    if isinstance(w, bool):
        return 'ja' if w else 'nein'
    if isinstance(w, float):
        return ('%g' % w)
    if isinstance(w, int):
        return str(w)
    if isinstance(w, str):
        return deutsch(w.strip())
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


def kombi(titel, teile, trenner='; '):
    """Mehrere Felder zu einer Zeile. teile = [(form, sel)]: form ist eine
    Beschriftung vor dem Wert oder eine Funktion Wert -> Text (None = weglassen)."""
    def anwenden(form, t):
        if form is None:
            return None
        if callable(form):
            return form(t)
        return (form + ' ' if form else '') + t
    werte, belege, abw, weitere = [], [], [], []
    for form, sel in teile:
        if not sel:
            continue
        t = anwenden(form, sel['wert'])
        if not t:
            continue
        werte.append(t)
        belege += sel['belege']
        for a in sel['abweichend']:
            x = anwenden(form, a['wert'])
            if x:
                abw.append({'wert': x, 'belege': a['belege']})
        for a in sel.get('weitere', []):
            x = anwenden(form, a['wert'])
            if x:
                weitere.append({'wert': x, 'belege': a['belege']})
    if not werte:
        return None
    return {'titel': titel, 'wert': trenner.join(werte), 'belege': belege, 'abweichend': abw,
            'weitere': weitere}


def ja(t):
    return schluessel(t) in ('ja', 'true', 'yes')


def nein(t):
    return schluessel(t).split(' ')[0].strip('(,;') in ('nein', 'false', 'no', 'keine', 'kein', 'keiner', 'none')


def ort(t):
    k = schluessel(t)
    innen, aus = 'innen' in k or 'indoor' in k, 'außen' in k or 'outdoor' in k
    if innen and aus:
        return 'innen und außen'
    return 'außen' if aus else ('innen' if innen else t)


def poe(t):
    k = schluessel(t)
    if nein(t):
        return 'kein PoE'
    normen = re.findall(r'802\.3(?:af|at|bt)', k)
    passiv = 'passiv' in k or 'passive' in k
    teile = []
    if normen:
        teile.append('PoE nach ' + ' oder '.join(dict.fromkeys(normen)))
    if passiv:
        teile.append('passives PoE')
    return ' oder '.join(teile) if teile else t


def volt(t):
    m = re.search(r'(\d+(?:\.\d+)?)(?:\s*(?:-|bis)\s*(\d+(?:\.\d+)?))?', t)
    if not m:
        return t
    return (m.group(1) + (' bis ' + m.group(2) if m.group(2) else '')) + ' V'


def generation(std):
    k = ' ' + re.sub(r'[^a-z]+', ' ', schluessel(std)) + ' '
    for kurz, gen in (('be', 7), ('ax', 6), ('ac', 5), ('n', 4)):
        if ' %s ' % kurz in k or re.search(r'11%s\b' % kurz, schluessel(std)):
            return 'WLAN %d (802.11%s)' % (gen, kurz)
    if re.search(r'\b[bg]\b', k):
        return 'älterer Standard (802.11b/g)'
    return std


def streams(t):
    m = re.search(r'(\d)\s*[x×]\s*(\d)', t) or re.search(r'(\d)t(\d)r', schluessel(t))
    if m:
        return '%s×%s' % (m.group(1), m.group(2))
    m = re.search(r'\d', t)
    return ('%s Streams' % m.group()) if m else t


def mass(t):
    t = re.sub(r'(\d)\s*[x×*]\s*(?=\d)', r'\1 × ', t)
    return t if 'mm' in t else t + ' mm'


# Speicher fuer Updates. "reichlich" ab 32 MB Flash und 256 MB RAM: Reserve auch fuer kommende
# Versionen (OpenWrt 25 und folgende) [abgeleitet, Schwelle adorfer/Supernode 19.10.2026].
STUFEN = {'reichlich': ('reichlich', 'viel Reserve, auch für künftige Versionen'),
          'reicht': ('ausreichend', 'genug Speicher für die aktuelle Firmware'),
          'knapp': ('knapp', 'läuft noch, aber mit wenig Reserve für künftige Versionen'),
          'sackgasse': ('zu wenig', 'nur noch alte Firmware (Sackgasse)')}
PASSIV_WARNUNG = ('Passives PoE: Nur mit dem passenden Netzteil oder Injektor betreiben und auf die '
                  'Spannung achten. Zu viel Spannung kann das Gerät zerstören, ein normaler PoE-Switch '
                  '(802.3af/at) versorgt es nicht.')
EINE_BUCHSE = ('Nur eine Netzwerkbuchse: Im Betrieb ist sie der Anschluss ans Internet. Geräte per '
               'Kabel lassen sich daran nicht anschließen.')


def sd_karte(s):
    """Startet das Geraet von einer Speicherkarte (Raspberry Pi, NanoPi ...)? Dann zaehlt der
    winzige Onboard-Flash fuer den Bootloader nicht, der Platz fuer die Firmware ist frei waehlbar."""
    sel = s.get('flash_typ')
    if not sel:
        return False
    texte = [sel['wert']] + [a['wert'] for a in sel['abweichend'] + sel.get('weitere', [])]
    return any(re.search(r'\b(micro)?sd(hc|xc)?\b|sd-karte|speicherkarte', schluessel(t)) for t in texte)


KARTE_MB = 32768   # Platzhalter fuer "Speicherkarte": groesser als jeder Onboard-Flash


def speicherstufe(flash, ram):
    if flash >= 32 and ram >= 256:
        return 'reichlich'
    if flash >= 16 and ram >= 128:
        return 'reicht'
    if flash >= 8 and ram >= 64:
        return 'knapp'
    return 'sackgasse'


def ansicht(d, idx):
    f, q = d.get('felder', {}), d.get('quellen', {})
    s = {k: auswahl(v, q, k in FAKT) for k, v in f.items()}
    oben, mitte, technik = [], [], []

    ram, flash = zahl(s.get('ram_mb')), zahl(s.get('flash_mb'))
    karte = sd_karte(s)
    if karte:
        flash = KARTE_MB
    if ram and flash:
        stufe = speicherstufe(flash, ram)
        kennwort, rest = STUFEN[stufe]
        oben.append({'titel': 'Speicher für Updates', 'stufe': stufe, 'kennwort': kennwort, 'wert': rest,
                     'erklaerung': ('Speicherkarte, %g MB RAM' % ram) if karte else ('%g MB Flash, %g MB RAM' % (flash, ram)),
                     'belege': (s['flash_typ']['belege'] if karte else s['flash_mb']['belege']) + s['ram_mb']['belege'],
                     'abweichend': ([] if karte else [{**a, 'wert': 'Flash ' + a['wert'] + ' MB'} for a in s['flash_mb']['abweichend']])
                     + [{**a, 'wert': 'RAM ' + a['wert'] + ' MB'} for a in s['ram_mb']['abweichend']],
                     'weitere': []})
    a = idx.get(d['image'])
    if a:   # sonst ergaenzt ffnef-geraete.js die Zeile aus anleitungen/index.json
        oben.append({'titel': 'Installation', 'level': a.get('level', ''), 'risiko': a.get('risiko', ''),
                     'status': a.get('status', ''), 'wert': a.get('level', ''),
                     'belege': [{'quelle': 'anleitung', 'url': a.get('url', ''), 'stand': '', 'sicherheit': 'hoch'}],
                     'abweichend': [], 'weitere': []})
    eo = s.get('einsatzort')
    aussen = eo and 'außen' in ort(eo['wert'])
    oben.append(kombi('Einsatzort', [(ort, eo)] +
                      ([('Schutzart', s.get('ip_schutzart')), ('Temperatur', s.get('temperatur_betrieb'))]
                       if aussen else []), trenner=', '))
    pe = s.get('poe_eingang')
    passiv = pe and 'passives' in poe(pe['wert'])
    strom = kombi('Stromversorgung', [
        (poe, pe),
        (volt, s.get('poe_spannung_v') if passiv else None),
        (lambda t: 'Netzteil ' + volt(t), s.get('dc_spannung_v')),
        (lambda t: 'Hohlstecker ' + mass(t), s.get('dc_buchse_mass')),
        (lambda t: 'Netzteil liegt bei' if ja(t) else ('ohne Netzteil' if nein(t) else None),
         s.get('netzteil_beiliegend'))], trenner=', ')
    if strom and passiv:
        strom['warnung'] = PASSIV_WARNUNG
    oben.append(strom)
    oben.append(zeile('Hardware-Version erkennen', s.get('erkennung_typenschild')))

    def band(name, std, st):
        if not std or nein(std['wert']) or schluessel(std['wert']) in ('-', '"-"'):
            return []
        return [(lambda t: name + ': ' + generation(t), std), (streams, st)]
    wlan = kombi('WLAN', band('2.4 GHz', s.get('wlan_24_standard'), s.get('wlan_24_streams'))
                 + band('5 GHz', s.get('wlan_5_standard'), s.get('wlan_5_streams'))
                 + band('6 GHz', s.get('wlan_6_standard'), s.get('wlan_6_streams'))
                 + [('Klasse', s.get('wlan_klasse'))], trenner=', ')
    mitte.append(wlan)
    ports = kombi('Anschlüsse', [('', s.get('ports')), (lambda t: (t + (' Buchse' if t == '1' else ' Buchsen')) if t.isdigit() else t,
                                                       s.get('ports_anzahl'))])
    if ports and s.get('nur_eine_buchse') and ja(s['nur_eine_buchse']['wert']):
        ports['warnung'] = EINE_BUCHSE
    mitte.append(ports)

    anschl = s.get('antennen_anschluss')
    def antart(t):
        k = schluessel(t)
        if 'abnehmbar' in k or 'detachable' in k or 'rp-sma' in k:
            return 'extern, abnehmbar' + (' (RP-SMA)' if 'rp-sma' in k or (anschl and 'rp-sma' in schluessel(anschl['wert'])) else '')
        if 'intern' in k and 'extern' not in k:
            return 'intern'
        if 'extern' in k and 'fest' in k and 'intern' not in k:
            return 'extern, fest'
        return t
    mitte.append(kombi('Antennen', [(antart, s.get('antennen_art')),
                                    (lambda t: t + ' Antennen' if t.isdigit() else t, s.get('antennen_anzahl')),
                                    ('Aufteilung', s.get('antennen_je_band'))], trenner=', '))

    einheit = lambda e: (lambda t: t + ' ' + e if re.fullmatch(r'[\d.]+', t) else t)
    for titel, teile, tr in [
        ('Prozessor', [('', s.get('soc')),
                       (lambda t: (t + (' Kern' if t == '1' else ' Kerne')) if t.isdigit() else t, s.get('cpu_kerne')),
                       (None if s.get('soc') and 'mhz' in schluessel(s['soc']['wert']) else einheit('MHz'),
                        s.get('cpu_mhz'))], ', '),
        ('Speicher', [(lambda t: 'RAM ' + einheit('MB')(t), s.get('ram_mb')),
                      (lambda t: 'Flash ' + einheit('MB')(t) + (' (' + s['flash_typ']['wert'] + ')' if s.get('flash_typ') else ''),
                       s.get('flash_mb'))], ', '),
        ('Leistungsaufnahme', [(lambda t: 'typisch ' + einheit('W')(t), s.get('leistung_w_typ')),
                               (lambda t: 'höchstens ' + einheit('W')(t), s.get('leistung_w_max'))], ', '),
        ('Montage', [('', s.get('montage')), ('Befestigung:', s.get('montageloecher'))], '; '),
        ('USB', [(lambda t: 'keiner' if nein(t) else t, s.get('usb'))], '; '),
        ('Serielle Konsole', [
            (lambda t: re.sub(r'^(\d+)(?:\s*8n1)?$', r'\1 Baud', t, flags=re.I) if t else t, s.get('seriell_baud')),
            (einheit('V'), s.get('seriell_pegel_v')), ('', s.get('seriell_zugang')),
            ('Belegung', s.get('seriell_pinbelegung')), ('', s.get('seriell_hinweis'))], '; '),
        ('Lüfter', [('', s.get('luefter'))], '; '),
        ('Reset-Knopf', [('', s.get('reset_knopf'))], '; '),
        ('LEDs abschaltbar', [('', s.get('led_abschaltbar'))], '; '),
        ('Größe und Gewicht', [(mass, s.get('abmessungen_mm')), (einheit('g'), s.get('gewicht_g'))], ', '),
        ('FCC-ID', [('', s.get('fcc_id'))], '; '),
    ]:
        technik.append(kombi(titel, teile, trenner=tr))

    links = []
    for k, name in [('toh_seite', 'OpenWrt-Geräteseite'), ('openwrt_wiki', 'OpenWrt-Wiki'), ('deviwiki', 'DeviWiki'),
                    ('wikidevi', 'WikiDevi'), ('hersteller_seite', 'Hersteller'), ('datenblatt', 'Datenblatt')]:
        if s.get(k) and s[k]['wert'].startswith('http'):
            links.append({'name': name, 'url': s[k]['wert']})
    links.append({'name': 'Alle Daten mit Quellen', 'url': REPO_URL + d['image'] + '.json'})

    return {'modell': d.get('modell', d['image']), 'stand': d.get('lauf', {}).get('datum', ''),
            'oben': [z for z in oben if z], 'mitte': [z for z in mitte if z],
            'technik': [z for z in technik if z], 'links': links}


VERSIONEN = {}   # 'Hersteller|Modell' -> {'bekannt': [...], 'nicht_unterstuetzt': [...]} aus dem Selector
MODELLE = {}     # image -> {'hersteller', 'modell', ...} aus quellen/selector-modelle-*.json


def modell_schluessel(image):
    if image in MODELLE:
        m = MODELLE[image]
        return m['hersteller'] + '|' + m['modell']
    best = None
    for basis, m in MODELLE.items():
        if image.startswith(basis + '-') and (not best or len(basis) > len(best[0])):
            best = (basis, m)
    return (best[1]['hersteller'] + '|' + best[1]['modell']) if best else None


# Bei TP-Link (und Mercusys) bezeichnet die Stelle nach dem Punkt nur Firmware- und Bootloader-Stand
# (v1.1, V1.20), die Hardware ist gleich; zaehlt also nur die Hauptversion (adorfer 20.10.2026).
# Ausnahme: CPE210 v1.1 bekam einen signierten Bootloader mit getrennter EU- und US-Fassung.
NACHKOMMA_ZAEHLT = {'TP-Link|CPE210'}


def hauptversion(v, schluessel):
    v = v.lower().strip()
    if schluessel in NACHKOMMA_ZAEHLT:
        return v
    return re.sub(r'^(v\d+)\.\d+$', r'\1', v)


def versionen_lage(d, s):
    """abgeschlossen: keine andere Hardware-Version bekannt und das Geraet ist eingestellt;
    weitere: es gibt andere Versionen; offen: nur diese bekannt, aber noch im Handel oder unklar."""
    m = re.search(r'-(v\d+(?:\.\d+)?)(?:-|$)', d['image'])
    diese = m.group(1).lower() if m else ''
    schl = modell_schluessel(d['image']) or ''
    e = VERSIONEN.get(schl, {})
    diese = hauptversion(diese, schl)
    andere = {hauptversion(v, schl) for v in (e.get('bekannt') or []) + (e.get('nicht_unterstuetzt') or [])} - {diese, ''}
    if andere:
        return 'weitere'
    texte = [str(d.get('roh', {}).get('toh', {}).get('availability', ''))]
    sel = s.get('verfuegbarkeit')
    if sel:
        texte += [sel['wert']] + [a['wert'] for a in sel['abweichend'] + sel.get('weitere', [])]
    if any(re.search(r'discontinued|eingestellt|\beol\b|end of life', t, re.I) for t in texte):
        return 'abgeschlossen'
    return 'offen'


def nicht_unterstuetzt(d):
    """Andere Hardware-Versionen, fuer die es keine Firmware gibt, mit kurzem Grund
    (aus versionen-anzeige.json des Selectors: Handpflege und OpenWrt-ToH)."""
    m = re.search(r'-(v\d+(?:\.\d+)?)(?:-|$)', d['image'])
    schl = modell_schluessel(d['image']) or ''
    diese = hauptversion(m.group(1), schl) if m else ''
    aus, gesehen = [], set()
    for b in VERSIONEN.get(schl, {}).get('belege') or []:
        # kurz: 'art' aus der ToH-Liste, sonst der erste Satz des handgepflegten Grunds
        grund = b.get('art') or re.split(r'\.\s', re.sub(r'^Grund:\s*', '', b.get('grund') or ''))[0].rstrip('.')
        for v in b.get('nicht_unterstuetzt') or []:
            v = hauptversion(v, schl)
            if v and v != diese and v not in gesehen:
                gesehen.add(v)
                aus.append({'version': v, 'grund': grund})
    return sorted(aus, key=lambda x: [int(n) for n in re.findall(r'\d+', x['version'])])


def facetten(d):
    """Maschinenlesbare Werte fuer die Geraetesuche. None = unbekannt.
    'unsicher' nennt Felder, bei denen sich Quellen widersprechen."""
    f, q = d.get('felder', {}), d.get('quellen', {})
    s = {k: auswahl(v, q, k in FAKT) for k, v in f.items()}
    unsicher = []

    def alle(k):
        sel = s.get(k)
        if not sel:
            return []
        if sel['abweichend']:
            unsicher.append(k)
        return [sel['wert']] + [a['wert'] for a in sel['abweichend']]

    def gen(t):
        m = re.search(r'WLAN (\d)', generation(t))
        return int(m.group(1)) if m else None

    fa = {}
    gens, baender = [], []
    for band, k in (('2.4', 'wlan_24_standard'), ('5', 'wlan_5_standard'), ('6', 'wlan_6_standard')):
        sel = s.get(k)
        if sel and not nein(sel['wert']) and schluessel(sel['wert']).strip('"()- '):
            g = gen(sel['wert'])
            if g or band != '6':
                baender.append(band)
                if g:
                    gens.append(g)
    fa['wlan'] = max(gens) if gens else None
    fa['baender'] = baender or None
    st = []
    for k in ('wlan_24_streams', 'wlan_5_streams', 'wlan_6_streams'):
        for t in alle(k)[:1]:
            m = re.search(r'(\d)', t)
            if m:
                st.append(int(m.group(1)))
    fa['streams'] = max(st) if st else None
    fa['ram'] = zahl(s.get('ram_mb'))
    fa['sd'] = sd_karte(s) or None
    fa['flash'] = KARTE_MB if fa['sd'] else zahl(s.get('flash_mb'))
    if fa['ram'] and fa['flash']:
        fa['speicher'] = STUFEN[speicherstufe(fa['flash'], fa['ram'])][0]
    else:
        fa['speicher'] = None
    fa['kerne'] = zahl(s.get('cpu_kerne'))
    ein = set()
    for t in alle('einsatzort'):
        o = ort(t)
        if 'innen' in o:
            ein.add('innen')
        if 'außen' in o:
            ein.add('außen')
    fa['einsatz'] = sorted(ein) or None
    mon = set()
    for t in alle('montage') + alle('montageloecher'):
        k = schluessel(t)
        for wort, wert in (('tisch', 'Tisch'), ('desk', 'Tisch'), ('wand', 'Wand'), ('wall', 'Wand'),
                           ('decke', 'Decke'), ('ceiling', 'Decke'), ('mast', 'Mast'), ('pole', 'Mast')):
            if wort in k:
                mon.add(wert)
    fa['montage'] = sorted(mon) or None
    ip = None
    for t in alle('ip_schutzart')[:1]:
        m = re.search(r'IP\s*([0-9X])([0-9X])', t.upper())
        if m:
            ip = [0 if m.group(1) == 'X' else int(m.group(1)), 0 if m.group(2) == 'X' else int(m.group(2))]
    fa['ip'] = ip
    pe = set()
    for t in alle('poe_eingang'):
        k = schluessel(t)
        if nein(t):
            pe.add('nein')
        for n in ('af', 'at', 'bt'):
            if '802.3' + n in k:
                pe.add(n)
        if 'passiv' in k or 'passive' in k:
            pe.add('passiv')
    fa['poe'] = sorted(pe) or None
    nb = s.get('netzteil_beiliegend')
    fa['netzteil'] = (True if ja(nb['wert']) else False if nein(nb['wert']) else None) if nb else None
    sp = []
    for t in alle('ports') + alle('ports_anzahl'):
        k = schluessel(t)
        for muster, mbit in ((r'10\s*g', 10000), (r'2[.,]5\s*g', 2500), (r'\b1\s*g|1000|gbit|gbe', 1000),
                             (r'\b100\b|10/100|fast', 100)):
            if re.search(muster, k):
                sp.append(mbit)
                break
    fa['port_mbit'] = max(sp) if sp else None
    fa['ports'] = zahl(s.get('ports_anzahl'))
    u = s.get('usb')
    fa['usb'] = (False if nein(u['wert']) else True) if u else None
    sf = s.get('sfp')
    fa['sfp'] = (False if nein(sf['wert']) or schluessel(sf['wert']) == '0' else True) if sf else None
    an = s.get('antennen_art')
    if an:
        k = schluessel(an['wert'])
        fa['antennen'] = ('abnehmbar' if ('abnehmbar' in k or 'detachable' in k or 'rp-sma' in k) else
                          'intern' if ('intern' in k and 'extern' not in k) else
                          'extern' if 'extern' in k else None)
    else:
        fa['antennen'] = None
    fa['leistung'] = zahl(s.get('leistung_w_max'))
    lu = s.get('luefter')
    fa['luefter'] = (False if nein(lu['wert']) else True if ja(lu['wert']) else None) if lu else None
    fa['versionen'] = versionen_lage(d, s)
    fa['nicht_unterstuetzt'] = nicht_unterstuetzt(d) or None
    gz = s.get('geizhals_url')
    fa['geizhals'] = gz['wert'] if gz and gz['wert'].startswith('https://geizhals.') else None
    fa['unsicher'] = sorted(set(unsicher)) or None
    return fa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', help='anleitungen/html/index.json aus gluon-rampe-installer')
    ap.add_argument('--aus', default=os.path.join(WURZEL, 'ausgabe', 'selector'))
    ap.add_argument('--versionen', default=os.path.expanduser(
        '~/projekte/freifunk/scratch/fsc/ffnef/versionen-anzeige.json'),
        help='versionen-anzeige.json aus firmware-selector-config')
    a = ap.parse_args()
    if os.path.exists(a.versionen):
        VERSIONEN.update(json.load(open(a.versionen, encoding='utf-8')).get('geraete', {}))
    md = sorted(glob.glob(os.path.join(WURZEL, 'quellen', 'selector-modelle-*.json')))
    if md:
        MODELLE.update(json.load(open(md[-1], encoding='utf-8'))['modelle'])
    idx = {}
    if a.index:
        for e in json.load(open(a.index, encoding='utf-8')):
            idx[e['gluon_name']] = e
    os.makedirs(a.aus, exist_ok=True)
    liste, fac = {}, {}
    for p in sorted(glob.glob(os.path.join(WURZEL, 'daten', '*.json'))):
        try:   # waehrend eines Laufs kann eine Datei gerade halb geschrieben sein
            d = json.load(open(p, encoding='utf-8'))
            d['image']
        except (ValueError, KeyError, TypeError) as e:
            print('uebersprungen (unvollstaendig):', os.path.basename(p), e)
            continue
        v = ansicht(d, idx)
        v.update({'image': d['image'], 'quelle': 'https://github.com/Neanderfunk/geraetedaten',
                  'lizenz': 'CC BY-SA 4.0'})
        with open(os.path.join(a.aus, d['image'] + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(v, fh, ensure_ascii=False, separators=(',', ':'))
        liste[d['image']] = {'modell': v['modell'], 'stand': v['stand']}
        fac[d['image']] = dict(modell=v['modell'], **facetten(d))
    with open(os.path.join(a.aus, 'index.json'), 'w', encoding='utf-8') as fh:
        json.dump({'quelle': 'https://github.com/Neanderfunk/geraetedaten', 'lizenz': 'CC BY-SA 4.0',
                   'geraete': liste}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.aus, 'facetten.json'), 'w', encoding='utf-8') as fh:
        json.dump({'quelle': 'https://github.com/Neanderfunk/geraetedaten', 'lizenz': 'CC BY-SA 4.0',
                   'geraete': fac}, fh, ensure_ascii=False, separators=(',', ':'))
    print(a.aus, len(liste), 'Geraete')


if __name__ == '__main__':
    main()
