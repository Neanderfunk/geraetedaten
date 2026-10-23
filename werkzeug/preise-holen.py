#!/usr/bin/env python3
"""Holt Circa-Neupreise fuer routerwahl.ffnef.de (Nutzerwunsch, adorfer 23.10.2026).

Ohne KI, fuer Cron gedacht. Liest die Geizhals-Permalinks aus daten/*.json, holt die
Produktseite ueber preisvergleich.heise.de (gleiche Seiten wie Geizhals, sperrt nicht),
nimmt den niedrigsten Angebotspreis und schreibt eine eigene Datei preise.json. Die
Geraetedaten bleiben unberuehrt: Preise veralten taeglich (schema/felder.md, "Handel").

Regel (adorfer): niedrigster Preis + 10 %, auf volle 10 EUR aufgerundet. Angezeigt
wird "neu ab ca. X EUR" mit Datum; wer es guenstiger findet, freut sich.

Deckt ein Geizhals-Eintrag mehrere Hardware-Versionen oder teilen sich mehrere unserer
Images denselben Eintrag, bekommt nur das Image mit der hoechsten Version den Preis:
verkauft wird praktisch nur die neueste, aeltere Versionen gibt es nur gebraucht.

Abrufe langsam (Vorgabe 30 s Abstand, wie fuer Geizhals vereinbart), Lauf fuer gut
300 Seiten also gut zweieinhalb Stunden. Am Ende ein Bericht. Findet das Skript auf
vielen Seiten mit HTTP 200 weder Angebote noch den Hinweis "keine Angebote", hat heise
das Seitenlayout geaendert: dann Rueckgabe 2 und die alte Datei bleibt stehen.
Laeuft das Skript schon, endet ein zweiter Start sofort mit Rueckgabe 3.

Aufruf:
    werkzeug/preise-holen.py --aus /var/www/routerwahl.ffnef.de/preise.json
    werkzeug/preise-holen.py --nur gl.inet-gl-mt6000 --abstand 0 --aus /tmp/p.json
"""
import argparse, datetime, fcntl, glob, json, math, os, re, sys, time, urllib.request

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'Mozilla/5.0 (X11; Linux x86_64) routerwahl.ffnef.de Preisabruf'
OFFER = re.compile(r'id="offer-index-(\d+)".*?class="gh_price">\s*€\s*([\d.]+,\d\d)', re.S)
ANZAHL = re.compile(r'product-offers-count"\s*>\s*(?:<a[^>]*>\s*)?<span class="count">(\d+)</span>')
KEINE = re.compile(r'\b0 Angebote\b|keine Angebote|derzeit nicht lieferbar|Nicht mehr gelistet|noch keine Angebote', re.I)


def ca(preis):
    return int(math.ceil(preis * 1.10 / 10.0) * 10)


def versionszahl(img):
    m = re.search(r'-v(\d+)(?:\.(\d+))?(?:-|$)', img)
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)


def kandidaten():
    """Geizhals-URL -> Images, plus ob der Eintrag mehrere Hardware-Versionen deckt."""
    je_url = {}
    for p in sorted(glob.glob(os.path.join(WURZEL, 'daten', '*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        for e in d['felder'].get('geizhals_url', [])[:1]:
            url = str(e.get('wert', '')).strip()
            if not url.startswith('https://geizhals.de/'):
                continue
            mehrere = 'mehrere Hardware-Versionen' in (e.get('bemerkung') or '')
            g = je_url.setdefault(url, {'images': [], 'mehrere': False})
            g['images'].append(d['image'])
            g['mehrere'] |= mehrere
    return je_url


def seite(url):
    r = urllib.request.Request(url.replace('https://geizhals.de/', 'https://preisvergleich.heise.de/'),
                               headers={'User-Agent': UA, 'Accept-Language': 'de'})
    with urllib.request.urlopen(r, timeout=60) as a:
        return a.status, a.read().decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--aus', required=True, help='Ziel, z. B. <routerwahl-webroot>/preise.json')
    ap.add_argument('--abstand', type=float, default=30.0, help='Sekunden zwischen zwei Abrufen')
    ap.add_argument('--nur', help='nur dieses Image (zum Pruefen)')
    ap.add_argument('--mindestens', type=int, default=3, help='so viele Angebote, sonst kein Preis')
    a = ap.parse_args()
    # Zeilenweise schreiben, damit ein Cron-Log den Fortschritt zeigt (sonst puffert Python bis zum Ende)
    sys.stdout.reconfigure(line_buffering=True)
    # Schutz gegen doppelten Lauf (Cron plus Handstart): Sperre auf die Skriptdatei
    # selbst, so entsteht keine Sperrdatei im Webroot. Das Kernel-Lock faellt mit
    # dem Prozess, auch nach kill -9 bleibt nichts haengen.
    sperre = open(os.path.abspath(__file__), 'rb')
    try:
        fcntl.flock(sperre, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('### preise-holen laeuft schon, dieser Start endet ohne Abruf.', file=sys.stderr)
        return 3

    heute = datetime.date.today().isoformat()
    aus = {'stand': heute, 'quelle': 'preisvergleich.heise.de (Geizhals)',
           'regel': 'niedrigster Angebotspreis + 10 %, auf volle 10 EUR aufgerundet', 'geraete': {}}
    zaehler = {'abgerufen': 0, 'mit_preis': 0, 'zu_wenig': 0, 'ohne_angebot': 0, 'layout_unklar': 0, 'fehler': 0}
    unklar = []
    gruppen = kandidaten()
    for url, g in sorted(gruppen.items()):
        imgs = sorted(g['images'], key=versionszahl)
        ziel = imgs[-1]
        if a.nur and a.nur not in imgs:
            continue
        if zaehler['abgerufen'] and a.abstand:
            time.sleep(a.abstand)
        zaehler['abgerufen'] += 1
        try:
            status, html = seite(url)
        except Exception as e:   # Netz, 404, Zeitueberschreitung: dieses Geraet ohne Preis
            zaehler['fehler'] += 1
            print('  Fehler   %-45s %s' % (ziel, e), file=sys.stderr)
            continue
        offers = OFFER.findall(html)
        anzahl = ANZAHL.search(html)
        if not offers:
            # Jede Seite eine Zeile, sonst bleibt das Log bei vielen Geraeten ohne
            # Angebot lange leer und man haelt den Lauf fuer haengend
            if (anzahl and anzahl.group(1) == '0') or KEINE.search(html):
                zaehler['ohne_angebot'] += 1
                print('  ohne     %s' % ziel)
            else:
                zaehler['layout_unklar'] += 1
                unklar.append(ziel)
                print('  unklar   %s' % ziel)
            continue
        preise = [float(p.replace('.', '').replace(',', '.')) for _, p in offers]
        if len(preise) < a.mindestens:
            # Ein einzelnes Restangebot eines ausgelaufenen Geraets ist oft absurd teuer
            # (UAP-AC-Lite 23.10.2026: ein Haendler, 416,50 EUR). Lieber kein Preis.
            # Zwei reichen auch nicht: UniFi 6 Lite/6 LR hatten am 23.10. je zwei
            # Restangebote zum doppelten Marktpreis. Seitdem mindestens 3 (adorfer).
            zaehler['zu_wenig'] += 1
            print('  wenig    %-45s %d Angebot(e), ab %.2f' % (ziel, len(preise), min(preise)))
            continue
        ab = min(preise)
        zaehler['mit_preis'] += 1
        eintrag = {'ab_eur': ab, 'ca_eur': ca(ab), 'angebote': len(preise), 'geizhals': url}
        if g['mehrere'] or len(imgs) > 1:
            eintrag['hinweis'] = 'Geizhals-Eintrag deckt mehrere Hardware-Versionen; im Handel meist die neueste'
        aus['geraete'][ziel] = eintrag
        print('  %-45s ab %8.2f  ca %4d  (%d Angebote)' % (ziel, ab, eintrag['ca_eur'], len(preise)))

    print('### %(abgerufen)d Seiten, %(mit_preis)d mit Preis, %(zu_wenig)d mit zu wenig Angeboten, '
          '%(ohne_angebot)d ohne Angebot, '
          '%(fehler)d Fehler, %(layout_unklar)d unklar' % zaehler)
    if zaehler['abgerufen'] >= 10 and zaehler['layout_unklar'] > zaehler['abgerufen'] // 5:
        print('### ABBRUCH: auf %d Seiten weder Angebote noch "keine Angebote" gefunden (%s ...).\n'
              '### heise hat vermutlich das Seitenlayout geaendert; %s bleibt unveraendert.'
              % (zaehler['layout_unklar'], ', '.join(unklar[:5]), a.aus), file=sys.stderr)
        return 2
    tmp = a.aus + '.neu'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(aus, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, a.aus)
    return 0


if __name__ == '__main__':
    sys.exit(main())
