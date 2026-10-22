#!/usr/bin/env python3
"""Traegt WireGuard-Durchsatzwerte aus vier Quellen in daten/*.json ein (Nutzerfrage 22.10.2026).

Quellen (quellen/vpn-durchsatz-<datum>.json, Abzug der Seiten):
  ffmuc_gluon     FFMUC-Wiki: Gluon mit WireGuard + VXLAN + batman-adv, Durchsatz uebers Internet
  wg_bench_forum  OpenWrt-Forum "A Wireguard comparison DB": wg-bench, nur Verschluesselung
  wg_bench        github.com/cyyself/wg-bench README: dito
  toh_vpn         OpenWrt-ToH-Ansicht "VPN performance", Feld WireGuard performance
Zuordnung Name -> Image von Hand: quellen/vpn-zuordnung.tsv.

Felder: wireguard_gluon (echte Gluon-Messung) und wireguard_geraet (nur Verschluesselung auf
dem Geraet). Der Lauf ersetzt nur Eintraege dieser vier Quellen, alles andere bleibt.
Aufruf: werkzeug/vpn-werte.py
"""
import glob, json, os, re

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLEN = ('ffmuc_gluon', 'wg_bench_forum', 'wg_bench', 'toh_vpn')
FELDER = ('wireguard_gluon', 'wireguard_geraet')


def mbit(t):
    """'1.01 Gbps' -> '1010 Mbit/s', '413 Mbps' -> '413 Mbit/s'; sonst None."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(g|m)?', str(t).lower())
    if not m:
        return None
    z = float(m.group(1).replace(',', '.'))
    if m.group(2) == 'g' or (m.group(2) is None and 'gbit' in str(t).lower()):
        z *= 1000
    return '%g Mbit/s' % round(z)


def main():
    q = json.load(open(sorted(glob.glob(os.path.join(WURZEL, 'quellen', 'vpn-durchsatz-*.json')))[-1], encoding='utf-8'))
    zu = {}
    for z in open(os.path.join(WURZEL, 'quellen', 'vpn-zuordnung.tsv'), encoding='utf-8'):
        if z.startswith('#') or not z.strip():
            continue
        quelle, name, imgs = z.rstrip('\n').split('\t')
        zu[(quelle, name.strip())] = imgs.split(',')
    neu = {}
    for r in q['zeilen']:
        imgs = zu.get((r['quelle'], r['name'].strip()))
        if not imgs:
            continue
        info = q['quellen'][r['quelle']]
        if r['quelle'] == 'ffmuc_gluon':
            feld = 'wireguard_gluon'
            dt = lambda t: (t.replace('gw-capped', 'Gateway begrenzt').replace('capped?', 'Anschluss begrenzt?')
                            .replace('capped', 'Anschluss begrenzt').replace('N/A', '?'))
            wert = '%s ↓ / %s ↑ Mbit/s' % (dt(r['down']), dt(r['up']))
            zus = [x for x in ((r.get('verbindung') or '').replace('on-device', 'auf dem Gerät'), r.get('messung'), 'Gluon ' + r['firmware'] if r.get('firmware') else '') if x]
            if 'UDP' in r['name']:
                zus.append('UDP')
            if r.get('historisch'):
                zus.append('ältere Messung')
            wert += ' (' + ', '.join(zus) + ')' if zus else ''
            beleg = info['url']
        elif r['quelle'] == 'toh_vpn':
            feld = 'wireguard_geraet'
            w = mbit(r['wireguard']) if re.search(r'\d', r['wireguard']) else None
            if not w:
                continue
            wert, beleg = w, r.get('url') or info['url']
        else:
            feld = 'wireguard_geraet'
            w = mbit(r['wert'])
            if not w:
                continue
            os_ = r.get('openwrt', '')
            if os_ and not re.match(r'(?i)openwrt|alpine|debian|ubuntu|arch|turris', os_):
                os_ = 'OpenWrt ' + os_
            wert = w + (' (' + os_ + ')' if os_ else '')
            beleg = info['url']
        for img in imgs:
            neu.setdefault(img, []).append((feld, {'wert': wert, 'quelle': r['quelle'], 'beleg': beleg,
                                                   'stand': q['stand'], 'sicherheit': 'mittel',
                                                   'bemerkung': info['art']}))
    geaendert = 0
    for p in sorted(glob.glob(os.path.join(WURZEL, 'daten', '*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        f = d['felder']
        vorher = json.dumps(d, ensure_ascii=False, sort_keys=True)
        for k in FELDER:
            if k in f:
                f[k] = [e for e in f[k] if e.get('quelle') not in QUELLEN]
                if not f[k]:
                    del f[k]
        for feld, e in neu.get(d['image'], []):
            if e not in f.setdefault(feld, []):
                f[feld].append(e)
            d['quellen'].setdefault(e['quelle'], {'url': q['quellen'][e['quelle']]['url'], 'stand': q['stand'],
                                                   'abgerufen': q['stand'], 'bemerkung': q['quellen'][e['quelle']]['art']})
        if json.dumps(d, ensure_ascii=False, sort_keys=True) != vorher:
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
            geaendert += 1
    print(len(neu), 'Images mit Werten,', geaendert, 'Dateien geaendert')


if __name__ == '__main__':
    main()
