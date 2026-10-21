#!/usr/bin/env python3
"""Welche Geraete bekommen unsere aktuelle Firmware nur mit Abstrichen?

    werkzeug/abstriche.py <FirmwareConfigs-Klon> <Gluon-Klon>
    z. B. werkzeug/abstriche.py ~/projekte/freifunk/FirmwareConfigs-2025.1 ~/projekte/freifunk/firmware-2025.1/gluon

Liest die Geraetelisten aus templates/common/image-customization.lua (lowmem_dualradio,
lowmem_singleradio, lowflash) und aus den Gluon-Targets die Geraete mit
ath10k-smallbuffers. Schreibt quellen/firmware-abstriche.json. selector-ansicht.py setzt
"Speicher fuer Updates" dieser Geraete hoechstens auf "knapp" und nennt die Abstriche:
Die Felddaten zur RAM-Belegung messen sie schon mit den Kuerzungen, sie zeigen also zu wenig
Bedarf (adorfer 21.10.2026).

Was jede Liste streicht, steht hier von Hand und muss zur Logik in image-customization.lua
passen; geprueft am Stand, der in "quelle" steht.
"""
import datetime, glob, json, os, re, subprocess, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(WURZEL, 'quellen', 'firmware-abstriche.json')

# Listenname in image-customization.lua -> was diese Geraete nicht bekommen
TLS = 'TLS (HTTPS-Verbindungen vom Router aus)'
WPA3 = 'WPA3 (damit auch ohne das WLAN „Freifunk verschlüsselt“)'
USTEER = 'Band-Steering (usteer)'
SQM = 'Bandbreitenbegrenzung fürs VPN (SQM)'
LISTEN = {
    'lowmem_dualradio': [TLS, WPA3, USTEER, SQM],
    'lowmem_singleradio': [WPA3, USTEER],
    'lowflash': [SQM],
}
SMALLBUFFERS = 'WLAN-Treiber mit verkleinerten Puffern (ath10k-smallbuffers)'


def stand(pfad):
    try:
        return subprocess.run(['git', '-C', pfad, 'describe', '--always', '--tags'],
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        return ''


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    fc, gluon = sys.argv[1:]
    lua = open(os.path.join(fc, 'templates', 'common', 'image-customization.lua'), encoding='utf-8').read()
    aus = {}
    for name, was in LISTEN.items():
        m = re.search(r'local\s+%s\s*=\s*device\(\{(.*?)\}\)' % name, lua, re.S)
        if not m:
            sys.exit('Liste %s nicht gefunden: image-customization.lua geaendert?' % name)
        for img in re.findall(r"'([^']+)'", re.sub(r'--[^\n]*', '', m.group(1))):
            e = aus.setdefault(img, {'listen': [], 'ohne': []})
            e['listen'].append(name)
            e['ohne'] += [w for w in was if w not in e['ohne']]
    for p in sorted(glob.glob(os.path.join(gluon, 'targets', '*'))):
        if not os.path.isfile(p):
            continue
        t = open(p, encoding='utf-8').read()
        for m in re.finditer(r"device\('([^']+)'[^)]*?\{(.*?)\}\)", t, re.S):
            if re.search(r'packages\s*=\s*ATH10K_PACKAGES\w*SMALLBUFFERS', m.group(2)):
                e = aus.setdefault(m.group(1), {'listen': [], 'ohne': []})
                e['listen'].append('smallbuffers')
                e['smallbuffers'] = True
    with open(ZIEL, 'w', encoding='utf-8') as f:
        json.dump({'erzeugt': datetime.date.today().isoformat(),
                   'erzeugt_von': 'werkzeug/abstriche.py',
                   'quelle': {'FirmwareConfigs': stand(fc), 'gluon': stand(gluon)},
                   'smallbuffers_text': SMALLBUFFERS,
                   'geraete': aus}, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('geschrieben:', ZIEL, len(aus), 'Geraete')


if __name__ == '__main__':
    main()
