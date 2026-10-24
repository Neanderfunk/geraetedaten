/* Routerwahl (routerwahl.ffnef.de): Merkmale anklicken wie bei einer
   Preissuchmaschine, die Liste zeigt die passenden Geraete.

   Daten: geraete/facetten.json aus Neanderfunk/geraetedaten
   (werkzeug/selector-ansicht.py), Level/Risiko/Status frisch aus
   anleitungen/index.json, Hersteller/Modell/Version fuer den Link in den
   Selector aus devices.js (config.vendormodels).

   Regeln: Innerhalb einer Gruppe gilt "oder" (Wand oder Decke), zwischen
   Gruppen "und". Bei "mindestens"-Gruppen ist genau eine Stufe waehlbar.
   Ein Geraet ohne Angabe zu einem gewaehlten Merkmal faellt heraus, ausser
   "auch Geraete mit fehlenden Angaben zeigen" ist an; dann bleibt es drin
   und traegt den Hinweis, was fehlt. */
(function () {
  'use strict';

  var SEP = '⁣';
  var LEVEL_REIHE = ['L0', 'L0.1', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8'];
  var LEVEL = {
    'L0': 'Einfach hochladen', 'L0.1': 'Hochladen, richtige Datei wählen',
    'L1': 'Zwei Schritte im Browser', 'L2': 'Taste beim Einschalten',
    'L3': 'Feste Adresse am Rechner', 'L4': 'Network-Tools',
    'L5': 'Besondere Programme', 'L6': 'Serielles Kabel',
    'L7': 'Gehäuse öffnen', 'L8': 'Löten und Programmer'
  };
  /* Was hinter den Leveln steckt; wortgleich mit der Tabelle "Level und Risiko"
     in gluon-rampe-installer, anleitungen/README.md. */
  var LEVEL_ERKL = {
    'L0': 'Die Freifunk-Firmware wird über die Weboberfläche des Geräts hochgeladen; es gibt nur eine passende Datei.',
    'L0.1': 'Wie L0, aber es gibt zwei Dateien (Erstinstallation und Upgrade), und man muss die richtige nehmen.',
    'L1': 'Erst eine Zwischenfirmware oder eine ältere Herstellerfirmware, dann die Freifunk-Firmware; alles im Browser.',
    'L2': 'Notfall-Modus per Taste, dann Hochladen im Browser; der Rechner bekommt seine Adresse von selbst.',
    'L3': 'Wie L2 oder ein anderer Weg im Browser, aber die Netzwerkeinstellung des Rechners muss von Hand umgestellt werden.',
    'L4': 'TFTP-Server, SSH, curl oder ein Image auf einen Datenträger schreiben; Programme, die es für jedes System gibt.',
    'L5': 'Skripte oder Programme außerhalb des Üblichen, oder Dateien vorher selbst zusammenbauen.',
    'L6': 'Ein Konsolenkabel am Gerät, ohne es zu öffnen.',
    'L7': 'Für die serielle Konsole muss das Gerät aufgeschraubt werden.',
    'L8': 'Klemmen am Speicherchip, Lötarbeiten oder ein Flash-Programmer.'
  };

  /* typ: menge = Wert ist eine Liste, Treffer wenn eine gewaehlte drin ist;
          eins  = Wert ist ein Text, Treffer wenn er gewaehlt ist;
          alle  = jede gewaehlte Option muss in der Liste sein;
          min/max = Zahl, genau eine Stufe;
          ja/nein = Schalter. */
  /* Texte: Content, 19.10.2026 (freifunk-content vorschlaege/routerwahl-texte.md). */
  var GRUPPEN = [
    { titel: 'Einsatz', filter: [
      { id: 'einsatz', titel: 'Einsatzort', typ: 'menge', werte: [['innen', 'innen'], ['außen', 'außen']] },
      { id: 'montage', titel: 'Montage', typ: 'menge',
        werte: [['Tisch', 'Tisch'], ['Wand', 'Wand'], ['Decke', 'Decke'], ['Mast', 'Mast']] },
      { id: 'ip', titel: 'Schutz gegen Wetter', typ: 'min',
        werte: [['54', 'ab IP54 (Spritzwasser)'], ['65', 'ab IP65 (Strahlwasser, staubdicht)']] }
    ] },
    { titel: 'Strom', filter: [
      { id: 'poe', titel: 'Strom über das Netzwerkkabel (PoE)', typ: 'menge',
        werte: [['af', '802.3af (PoE)'], ['at', '802.3at (PoE+)'], ['bt', '802.3bt (PoE++)'],
                ['passiv', 'passives PoE'], ['nein', 'kein PoE']] },
      { id: 'netzteil', titel: 'Netzteil liegt bei', typ: 'ja' }
    ] },
    { titel: 'WLAN', filter: [
      { id: 'wlan', titel: 'WLAN-Generation', typ: 'min',
        werte: [['4', 'ab WLAN 4 (802.11n)'], ['5', 'ab WLAN 5 (802.11ac)'], ['6', 'ab WLAN 6 (802.11ax)'],
                ['7', 'ab WLAN 7 (802.11be)']] },
      { id: 'baender', titel: 'Frequenzbänder', typ: 'alle', werte: [['2.4', '2.4 GHz'], ['5', '5 GHz'], ['6', '6 GHz']] },
      { id: 'streams', titel: 'Datenströme (Streams)', typ: 'min', werte: [['2', 'ab 2×2'], ['3', 'ab 3×3'], ['4', 'ab 4×4']] },
      { id: 'antennen', titel: 'Antennen', typ: 'eins',
        werte: [['intern', 'intern'], ['extern', 'extern, fest'], ['abnehmbar', 'extern, abnehmbar']] }
    ] },
    { titel: 'Anschlüsse', filter: [
      { id: 'port_mbit', titel: 'Geschwindigkeit am Kabel', typ: 'min',
        werte: [['1000', 'ab 1 Gbit/s'], ['2500', 'ab 2.5 Gbit/s']] },
      { id: 'ports', titel: 'Netzwerkbuchsen', typ: 'min', werte: [['2', 'ab 2'], ['4', 'ab 4']] },
      { id: 'usb', titel: 'USB', typ: 'ja' },
      { id: 'sfp', titel: 'SFP-Modul', typ: 'ja' }
    ] },
    { titel: 'Ausstattung', filter: [
      /* Stufen von gut nach schlecht; gewaehlt wird "diese oder besser" (adorfer 24.10.2026).
         Schluessel ohne Komma, weil die Auswahl kommagetrennt in der URL steht. */
      { id: 'speicher', titel: 'Speicher für Updates', typ: 'stufe',
        reihe: ['reichlich', 'gut', 'ausreichend', 'knapp', 'knapp, reduzierte Funktionalität', 'zu wenig'],
        schluessel: { reduziert: 'knapp, reduzierte Funktionalität' },
        werte: [['reichlich', 'reichlich'], ['gut', 'gut oder besser'], ['ausreichend', 'ausreichend oder besser'],
                ['knapp', 'knapp oder besser'], ['reduziert', 'knapp, reduzierte Funktionalität, oder besser']] },
      { id: 'ram', titel: 'Arbeitsspeicher (RAM)', typ: 'min',
        werte: [['128', 'ab 128 MB'], ['256', 'ab 256 MB'], ['512', 'ab 512 MB']] },
      { id: 'flash', titel: 'Flash-Speicher', typ: 'min', werte: [['16', 'ab 16 MB'], ['128', 'ab 128 MB']] },
      { id: 'kerne', titel: 'Prozessor', typ: 'min', werte: [['2', 'ab 2 Kernen'], ['4', 'ab 4 Kernen']] },
      { id: 'mhz', titel: 'Prozessortakt', typ: 'min',
        werte: [['1000', 'ab 1 GHz'], ['1300', 'ab 1.3 GHz'], ['2000', 'ab 2 GHz']] },
      /* Gluon-Target, Namen wie in der Gluon-Doku (supported_devices), Nutzerwunsch 22.10.2026 */
      { id: 'plattform', titel: 'Plattform (Gluon-Target)', typ: 'eins',
        werte: [['mediatek-filogic', 'mediatek-filogic (MediaTek MT7981/MT7986, WLAN 6)'],
                ['mediatek-mt7622', 'mediatek-mt7622 (MediaTek MT7622)'],
                ['ramips-mt7621', 'ramips-mt7621 (MediaTek MT7621)'],
                ['ramips-mt76x8', 'ramips-mt76x8 (MediaTek MT7628/MT7688)'],
                ['ramips-mt7620', 'ramips-mt7620 (MediaTek MT7620)'],
                ['ath79-generic', 'ath79-generic (Qualcomm Atheros)'],
                ['ath79-nand', 'ath79-nand (Qualcomm Atheros, NAND)'],
                ['ath79-mikrotik', 'ath79-mikrotik (MikroTik)'],
                ['ipq40xx-generic', 'ipq40xx-generic (Qualcomm IPQ40xx)'],
                ['ipq40xx-mikrotik', 'ipq40xx-mikrotik (MikroTik)'],
                ['ipq806x-generic', 'ipq806x-generic (Qualcomm IPQ806x)'],
                ['qualcommax-ipq807x', 'qualcommax-ipq807x (Qualcomm IPQ807x, WLAN 6)'],
                ['lantiq-xrx200', 'lantiq-xrx200 (Lantiq, u. a. FRITZ!Box)'],
                ['lantiq-xway', 'lantiq-xway (Lantiq)'],
                ['mpc85xx-p1010', 'mpc85xx-p1010 (NXP)'],
                ['mpc85xx-p1020', 'mpc85xx-p1020 (NXP)'],
                ['rockchip-armv8', 'rockchip-armv8 (Rockchip, NanoPi)'],
                ['bcm27xx-bcm2710', 'bcm27xx-bcm2710 (Raspberry Pi 3)'],
                ['bcm27xx-bcm2711', 'bcm27xx-bcm2711 (Raspberry Pi 4)']] },
      { id: 'leistung', titel: 'Leistungsaufnahme', typ: 'max', werte: [['10', 'bis 10 W'], ['15', 'bis 15 W']] },
      { id: 'luefter', titel: 'lautlos (ohne Lüfter)', typ: 'nein' }
    ] },
    /* Circa-Neupreis aus preise.json (werkzeug/preise-holen.py, Cron); Regler in 10-EUR-Schritten
       (adorfer 23.10.2026). Geraete ohne Preis zaehlen als "Angabe fehlt". */
    { titel: 'Preis', filter: [
      { id: 'preis', titel: 'Neupreis höchstens (circa)', typ: 'regler', schritt: 10 }
    ] },
    { titel: 'Einrichtung', filter: [
      { id: 'level', titel: 'Schwierigkeit', typ: 'max',
        werte: [['L1', 'bis L1: nur im Browser'], ['L3', 'bis L3: mit fester Adresse am Rechner'],
                ['L4', 'bis L4: mit Network-Tools (TFTP, SSH)'], ['L6', 'bis L6: auch mit seriellem Kabel'],
                /* umgekehrt, fuer Bastelnde: nur die schwierigeren */
                ['ab:L5', 'ab L5: besondere Programme und mehr'], ['ab:L6', 'ab L6: serielles Kabel und mehr'],
                ['ab:L7', 'ab L7: Gehäuse öffnen und mehr']] },
      { id: 'erprobt', titel: 'von uns am Gerät erprobt', typ: 'ja' },
      { id: 'ohne_bootloader', titel: 'Bootloader bleibt unangetastet', typ: 'ja' }
    ] }
  ];
  var FELDNAMEN = {
    ram_mb: 'Arbeitsspeicher', flash_mb: 'Flash-Speicher', cpu_mhz: 'Prozessortakt',
    cpu_kerne: 'Prozessorkerne', poe_spannung_v: 'PoE-Spannung', dc_spannung_v: 'Netzteil-Spannung',
    ip_schutzart: 'Schutzart', temperatur_betrieb: 'Temperatur', antennen_anzahl: 'Zahl der Antennen',
    ports_anzahl: 'Zahl der Buchsen', leistung_w_typ: 'Leistungsaufnahme', leistung_w_max: 'Leistungsaufnahme',
    einsatzort: 'Einsatzort', poe_eingang: 'PoE',
    wlan_24_streams: 'Streams 2.4 GHz', wlan_5_streams: 'Streams 5 GHz', wlan_6_streams: 'Streams 6 GHz',
    wlan_24_standard: 'WLAN-Standard 2.4 GHz', wlan_5_standard: 'WLAN-Standard 5 GHz',
    wlan_6_standard: 'WLAN-Standard 6 GHz', dc_strom_a: 'Netzteil-Strom', dc_buchse_mass: 'Hohlstecker-Maß'
  };
  var ALLE = [];
  GRUPPEN.forEach(function (g) { g.filter.forEach(function (f) { ALLE.push(f); }); });

  /* Nicht unterstuetzte Versionen eines Modells, von dem wir eine andere
     Version bauen (geraete/nicht-unterstuetzt.json): schlichte Karten hinter
     den Geschwistern, damit klar ist, dass genau diese Version nicht geht. */
  var nichtKarten = [];
  var geraete = [];      // [{image, modell, ...facetten, level, ...}]
  var preiseStand = '';  // Datum der preise.json, z. B. 23.10.2026
  var wahl = {};         // id -> [werte]
  /* Geraete mit fehlenden Angaben werden standardmaessig gezeigt (adorfer
     20.10.); das Haekchen blendet sie aus. */
  var mitUnbekannt = true;
  /* Nicht unterstuetzte Geraete einblenden (adorfer 20.10.): die Karten
     nicht unterstuetzter Versionen und die "noch nicht unterstuetzten" (Image
     nur im Testzweig, stable: false). Standardmaessig aus. */
  var mitNicht = false;
  /* Suche nach Namen (adorfer 20.10.): Teilwort irgendwo im Modellnamen, Image-Namen
     oder in weiteren Namen (andere_namen, Geizhals-Artikel), ohne Gross-/Kleinschreibung,
     Leerzeichen und Bindestriche. */
  var namensSuche = '';
  function dicht(t) { return String(t || '').toLowerCase().replace(/[\s\-_./()]+/g, ''); }
  function passtName(g) {
    if (!namensSuche) return true;
    var n = dicht(namensSuche);
    /* freie Zeichenkette, irgendwo im Namen (adorfer) */
    return [g.modell, g.image].concat(g.namen || []).some(function (t) { return dicht(t).indexOf(n) > -1; });
  }
  var sortierung = 'einfach';
  var nurGeraet = null;     // ?geraet=<image>: nur dieses Geraet, Daten gleich offen

  function $(w, wo) { return (wo || document).querySelector(w); }
  function el(art, klasse, text) {
    var k = document.createElement(art);
    if (klasse) k.className = klasse;
    if (text !== undefined && text !== null) k.textContent = text;
    return k;
  }

  function holen(url, fertig) {
    var r = new XMLHttpRequest();
    r.open('GET', url, true);
    r.onload = function () {
      var d = null;
      if (r.status >= 200 && r.status < 300) { try { d = JSON.parse(r.responseText); } catch (e) { d = null; } }
      fertig(d);
    };
    r.onerror = function () { fertig(null); };
    r.send();
  }

  /* Image-Name -> Hersteller, Modell, Version fuer ?q= im Selector. */
  function selectorOrt(image) {
    var vm = (window.config && window.config.vendormodels) || {};
    for (var kat in vm) for (var v in vm[kat]) for (var m in vm[kat][v]) {
      var x = vm[kat][v][m];
      if (typeof x === 'string') {
        if (image === x) return { vendor: v, model: m, rev: '', basis: x };
        if (image.indexOf(x + '-') === 0) return { vendor: v, model: m, rev: image.slice(x.length + 1), basis: x };
      } else {
        for (var img in x) {
          if (image === img) return { vendor: v, model: m, rev: x[img] || '', basis: img };
          if (image.indexOf(img + '-') === 0) return { vendor: v, model: m, rev: image.slice(img.length + 1), basis: img };
        }
      }
    }
    return null;
  }

  function q(o) {
    var t = function (s) { return String(s).replace(/ /g, ' '); };
    return '?q=' + encodeURIComponent(t(o.vendor) + SEP + t(o.model) + SEP + (o.rev ? t(o.rev) + SEP : ''));
  }

  /* Trifft Geraet g den Filter f mit den gewaehlten Werten w?
     Rueckgabe: true, false oder null (Angabe fehlt). */
  function trifft(g, f, w) {
    if (!w || !w.length) return true;
    var v = g[f.id];
    if (f.id === 'erprobt') return g.status ? g.status === 'erprobt' : null;
    if (f.id === 'ohne_bootloader') return g.risiko ? g.risiko !== 'bootloader' : null;
    if (f.id === 'level') {
      if (!g.level) return null;
      if (w[0].indexOf('ab:') === 0) return LEVEL_REIHE.indexOf(g.level) >= LEVEL_REIHE.indexOf(w[0].slice(3));
      return LEVEL_REIHE.indexOf(g.level) <= LEVEL_REIHE.indexOf(w[0]);
    }
    if (v === null || v === undefined) return null;
    switch (f.typ) {
      case 'menge': return w.some(function (x) { return v.indexOf(x) > -1; });
      case 'alle': return w.every(function (x) { return v.indexOf(x) > -1; });
      case 'eins': return w.indexOf(v) > -1;
      case 'min':
        if (f.id === 'ip') return v[0] >= +w[0].charAt(0) && v[1] >= +w[0].charAt(1);
        return v >= +w[0];
      case 'max': return v <= +w[0];
      case 'regler': return v <= +w[0];
      case 'stufe':
        var stufe = (f.schluessel && f.schluessel[w[0]]) || w[0];
        return f.reihe.indexOf(v) > -1 && f.reihe.indexOf(v) <= f.reihe.indexOf(stufe);
      case 'ja': return v === true;
      case 'nein': return v === false;
    }
    return true;
  }

  /* Alle Filter ausser "ohne" anwenden; Rueckgabe: Geraete mit Liste fehlender Angaben. */
  function filtern(ohne, ersatz) {
    var aus = [];
    geraete.forEach(function (g) {
      if (nurGeraet && g.image !== nurGeraet) return;
      if (!passtName(g)) return;
      if (!mitNicht && g.stable === false && g.image !== nurGeraet) return;
      var fehlt = [];
      for (var i = 0; i < ALLE.length; i++) {
        var f = ALLE[i];
        var w = (ohne && f.id === ohne) ? ersatz : wahl[f.id];
        var r = trifft(g, f, w);
        if (r === false) return;
        if (r === null) {
          if (!mitUnbekannt) return;
          fehlt.push(f.titel);
        }
      }
      aus.push({ g: g, fehlt: fehlt });
    });
    return aus;
  }

  function zaehle(f, wert) {
    var w;
    if (f.typ === 'menge' || f.typ === 'eins') w = [wert];
    else if (f.typ === 'alle') w = (wahl[f.id] || []).concat([wert]);
    else if (f.typ === 'ja' || f.typ === 'nein') w = [true];
    else w = [wert];
    return filtern(f.id, w).length;
  }

  function filterZeichnen() {
    var ziel = $('#finder-filter');
    ziel.textContent = '';
    GRUPPEN.forEach(function (gr) {
      var fs = el('fieldset', 'finder-gruppe');
      fs.appendChild(el('legend', null, gr.titel));
      gr.filter.forEach(function (f) {
        var block = el('div', 'finder-block');
        var bekannt = geraete.filter(function (g) {
          if (f.id === 'erprobt' || f.id === 'level') return !!g.level || !!g.status;
          if (f.id === 'ohne_bootloader') return !!g.risiko;
          return g[f.id] !== null && g[f.id] !== undefined;
        }).length;
        var kopf = el('div', 'finder-titel', f.titel);
        kopf.appendChild(el('span', 'finder-abdeckung', ' Angaben für ' + bekannt + ' von ' + geraete.length + ' Geräten'));
        block.appendChild(kopf);
        var gewaehlt = wahl[f.id] || [];
        if (f.typ === 'regler') {
          block.appendChild(regler(f, gewaehlt));
        } else if (f.typ === 'ja' || f.typ === 'nein') {
          block.appendChild(option(f, 'checkbox', true, 'ja', gewaehlt.length > 0, zaehle(f, true)));
        } else {
          var art = (f.typ === 'min' || f.typ === 'max' || f.typ === 'stufe') ? 'radio' : 'checkbox';
          f.werte.forEach(function (wv, i) {
            /* Zwischenzeile vor den umgekehrten Stufen ("ab L5"), damit "bis" und "ab" nicht verwirren */
            if (String(wv[0]).indexOf('ab:') === 0 && !(i && String(f.werte[i - 1][0]).indexOf('ab:') === 0))
              block.appendChild(el('p', 'finder-zwischen', 'Für Bastelfreudige:'));
            block.appendChild(option(f, art, wv[0], wv[1], gewaehlt.indexOf(wv[0]) > -1, zaehle(f, wv[0])));
          });
          if (art === 'radio' && gewaehlt.length) {
            var weg = el('button', 'finder-weg', 'egal');
            weg.type = 'button';
            weg.addEventListener('click', function () { delete wahl[f.id]; neu(); });
            block.appendChild(weg);
          }
        }
        fs.appendChild(block);
      });
      ziel.appendChild(fs);
    });
  }

  /* Schieberegler fuer Hoechstwerte: Spanne aus den vorhandenen Werten, auf den Schritt
     gerundet. Ganz rechts heisst "egal". Gefiltert wird erst beim Loslassen ("change"),
     beim Ziehen wird nur die Beschriftung samt Trefferzahl nachgefuehrt. */
  function regler(f, gewaehlt) {
    var schritt = f.schritt || 10;
    var werte = geraete.map(function (g) { return g[f.id]; }).filter(function (v) { return typeof v === 'number'; });
    var box = el('div', 'finder-regler');
    if (!werte.length) { box.appendChild(el('span', 'finder-leer', 'noch keine Angaben')); return box; }
    var min = Math.floor(Math.min.apply(null, werte) / schritt) * schritt;
    var max = Math.ceil(Math.max.apply(null, werte) / schritt) * schritt;
    var inp = document.createElement('input');
    inp.type = 'range'; inp.min = min; inp.max = max; inp.step = schritt;
    inp.value = gewaehlt.length ? Math.min(max, Math.max(min, +gewaehlt[0])) : max;
    inp.setAttribute('aria-label', f.titel);
    var text = el('span', 'finder-regler-wert');
    function beschriften() {
      var v = +inp.value;
      text.textContent = v >= max ? 'egal' : 'bis ' + v + ' € (' + zaehle(f, String(v)) + ')';
    }
    inp.addEventListener('input', beschriften);
    inp.addEventListener('change', function () {
      if (+inp.value >= max) delete wahl[f.id]; else wahl[f.id] = [String(inp.value)];
      neu();
    });
    beschriften();
    box.appendChild(inp);
    box.appendChild(text);
    return box;
  }

  function option(f, art, wert, text, an, zahl) {
    var lab = el('label', 'finder-option' + (zahl === 0 && !an ? ' finder-leer' : ''));
    var inp = document.createElement('input');
    inp.type = art;
    inp.name = 'f-' + f.id;
    inp.checked = an;
    inp.addEventListener('change', function () {
      var w = wahl[f.id] || [];
      if (art === 'radio') w = [wert];
      else if (f.typ === 'ja' || f.typ === 'nein') w = inp.checked ? [true] : [];
      else if (inp.checked) w = w.concat([wert]);
      else w = w.filter(function (x) { return x !== wert; });
      if (w.length) wahl[f.id] = w; else delete wahl[f.id];
      neu();
    });
    lab.appendChild(inp);
    lab.appendChild(document.createTextNode(' ' + text + ' '));
    lab.appendChild(el('span', 'finder-zahl', '(' + zahl + ')'));
    return lab;
  }

  function feldName(k) {
    if (FELDNAMEN[k]) return FELDNAMEN[k];
    var basis = k.replace(/_(mb|v|w|mhz|typ|max|betrieb|anzahl)$/, '');
    for (var i = 0; i < ALLE.length; i++) if (ALLE[i].id === k || ALLE[i].id === basis) return ALLE[i].titel;
    return k.replace(/_/g, ' ');
  }

  /* Kaufen und Preise: Geizhals-Permalink, wenn bekannt, sonst Suche; eBay und Kleinanzeigen
     immer als Suche. Gesucht wird ohne Hardware-Version, weil Angebote sie selten nennen;
     die Version steht deshalb als Hinweis dabei. */
  function suchname(modell) {
    return modell.replace(/\s+\(.*\)$/, '').replace(/\s+v\d+(\.\d+)?(\s.*)?$/i, '').trim();
  }
  function kaufLinks(g) {
    var name = suchname(g.modell);
    var version = (/\s(v\d+(\.\d+)?)\b/i.exec(g.modell) || [])[1];
    var p = el('p', 'finder-kaufen');
    if (g.preis) {
      var pr = el('span', 'finder-preis', 'Neu ab ca. ' + g.preis + ' €');
      pr.title = 'Niedrigster Angebotspreis bei Geizhals ' + String(g.preis_ab).replace('.', ',') + ' € plus etwa 10 %, aufgerundet; Stand ' +
        preiseStand + (g.preis_hinweis ? '. ' + g.preis_hinweis : '');
      p.appendChild(pr);
      p.appendChild(document.createTextNode(' (Stand ' + preiseStand + '). '));
    }
    p.appendChild(document.createTextNode('Neu oder gebraucht suchen: '));
    var ziele = [
      ['Geizhals', g.geizhals || 'https://geizhals.de/?fs=' + encodeURIComponent(name) + '&hloc=de'],
      ['eBay', 'https://www.ebay.de/sch/i.html?_nkw=' + encodeURIComponent(name)],
      ['Kleinanzeigen', 'https://www.kleinanzeigen.de/s-' +
        encodeURIComponent(name.toLowerCase().replace(/[^a-z0-9äöüß]+/g, '-').replace(/^-|-$/g, '')) + '/k0']
    ];
    ziele.forEach(function (z, i) {
      if (i) p.appendChild(document.createTextNode(' · '));
      var a = el('a', null, z[0]);
      a.href = z[1];
      a.rel = 'noopener noreferrer';
      a.target = '_blank';
      p.appendChild(a);
    });
    /* Andere Versionen ohne Firmware nur kurz nennen; warum sie nicht gehen,
       ist bei diesem Geraet egal (adorfer 20.10.). */
    var nicht = (g.nicht_unterstuetzt || []).map(function (n) { return n.version; });
    /* "nicht für v2 und v5": "gehen nicht" klaenge nach kaputtem Geraet (Content) */
    var nichtText = nicht.length ? 'nicht für ' + (nicht.length === 1 ? nicht[0] :
      nicht.slice(0, -1).join(', ') + ' und ' + nicht[nicht.length - 1]) : '';
    /* Gibt es nur diese Version und ist das Geraet eingestellt, hilft der Hinweis niemandem. */
    if (version && g.versionen !== 'abgeschlossen') p.appendChild(el('span', 'finder-kaufen-hinweis',
      ' Achte beim Kauf auf die Hardware-Version ' + version + (nichtText ? ' (' + nichtText + ')' : '') +
      '. Sie steht auf dem Typenschild; fehlt sie im Angebot, frag nach.'));
    else if (nichtText) p.appendChild(el('span', 'finder-kaufen-hinweis', ' ' + nichtText.charAt(0).toUpperCase() + nichtText.slice(1) + '.'));
    return p;
  }

  function chips(g) {
    var c = [];
    if (g.wlan) c.push('WLAN ' + g.wlan);
    if (g.streams) c.push(g.streams + '×' + g.streams);
    /* Prozessor als Kerne x Takt neben dem RAM, z. B. 4×1300 MHz (adorfer 22.10.2026) */
    if (g.mhz) c.push((g.kerne ? g.kerne + '×' : '') + g.mhz + ' MHz');
    if (g.ram) c.push(g.ram + ' MB RAM');
    if (g.sd) c.push('Speicherkarte');
    else if (g.flash) c.push(g.flash + ' MB Flash');
    if (g.einsatz) c.push(g.einsatz.join(' und '));
    if (g.montage) c.push(g.montage.join(', '));
    if (g.outdoor_optional) c.push('Mast/Outdoor: optional');
    if (g.poe && g.poe.indexOf('nein') < 0) c.push('PoE ' + g.poe.map(function (p) {
      return p === 'passiv' ? 'passiv' : '802.3' + p; }).join('/'));
    if (g.port_mbit) c.push(g.port_mbit >= 1000 ? (g.port_mbit / 1000) + ' Gbit/s' : g.port_mbit + ' Mbit/s');
    if (g.ports) c.push(g.ports === 1 ? '1 Buchse' : g.ports + ' Buchsen');
    if (g.usb) c.push('USB');
    if (g.leistung) c.push('bis ' + g.leistung + ' W Leistungsaufnahme');
    return c;
  }

  function sortieren(liste) {
    var lv = function (g) { var i = LEVEL_REIHE.indexOf(g.level); return i < 0 ? 99 : i; };
    var cmp = {
      einfach: function (a, b) { return lv(a.g) - lv(b.g) || (b.g.status === 'erprobt') - (a.g.status === 'erprobt'); },
      ram: function (a, b) { return (b.g.ram || 0) - (a.g.ram || 0); },
      wlan: function (a, b) { return (b.g.wlan || 0) - (a.g.wlan || 0) || (b.g.streams || 0) - (a.g.streams || 0); },
      leistung: function (a, b) { return (a.g.leistung || 999) - (b.g.leistung || 999); },
      name: function () { return 0; }
    }[sortierung];
    return liste.sort(function (a, b) {
      return cmp(a, b) || a.g.modell.localeCompare(b.g.modell, 'de');
    });
  }

  /* "Einrichtung: L0.1 Hochladen, richtige Datei wählen" mit
     Erklaerung beim Darueberfahren; die Legende aller Level steht im Seitenkopf. */
  /* Legende aller Level im Seitenkopf (#finder-legende), einmal fuer alle Karten. */
  function legendeZeichnen() {
    var d = $('#finder-legende-tabelle');
    if (!d || d.querySelector('dl')) return;
    var dl = el('dl');
    LEVEL_REIHE.forEach(function (l) {
      dl.appendChild(el('dt', null, l + ' ' + (LEVEL[l] || '')));
      dl.appendChild(el('dd', null, LEVEL_ERKL[l] || ''));
    });
    d.appendChild(dl);
  }

  function levelZeile(g) {
    var p = el('div', 'finder-level');
    p.appendChild(document.createTextNode('Einrichtung: '));
    var k = el('span', 'finder-level-kenn', g.level + ' ' + (LEVEL[g.level] || ''));
    if (LEVEL_ERKL[g.level]) k.title = LEVEL_ERKL[g.level];
    p.appendChild(k);
    if (g.status === 'erprobt') p.appendChild(document.createTextNode(', am Gerät erprobt'));
    return p;
  }

  function nichtKarte(nk) {
    var k = el('article', 'finder-karte finder-nicht');
    var rumpf = el('div', 'finder-rumpf');
    rumpf.appendChild(el('h2', null, nk.modell));
    rumpf.appendChild(el('p', 'finder-nicht-marke', 'Nicht unterstützt'));
    if (nk.grund) rumpf.appendChild(el('p', null, 'Grund: ' + nk.grund + '.'));
    if (nk.erkennung) rumpf.appendChild(el('p', 'finder-level', nk.erkennung));
    var p = el('p', null, 'Freifunk-Firmware gibt es nur für ');
    nk.geschwister.forEach(function (img, i) {
      if (i) p.appendChild(document.createTextNode(i === nk.geschwister.length - 1 ? ' und ' : ', '));
      var g = geraete.filter(function (x) { return x.image === img; })[0];
      var a = el('a', null, g ? g.modell : img);
      a.href = '?geraet=' + encodeURIComponent(img);
      p.appendChild(a);
    });
    p.appendChild(document.createTextNode('.'));
    rumpf.appendChild(p);
    if (nk.quelle) {
      var q = el('p', 'finder-level');
      var qa = el('a', null, 'Quelle');
      qa.href = nk.quelle; qa.rel = 'noopener'; qa.target = '_blank';
      q.appendChild(qa);
      rumpf.appendChild(q);
    }
    k.appendChild(rumpf);
    return k;
  }

  function listeZeichnen() {
    var einzeln = nurGeraet && nichtKarten.filter(function (nk) { return nk.id === nurGeraet; })[0];
    if (einzeln) {
      $('#finder-anzahl').textContent = 'Diese Version wird nicht unterstützt';
      $('#finder-liste').textContent = '';
      $('#finder-liste').appendChild(nichtKarte(einzeln));
      return;
    }
    var treffer = sortieren(filtern(null));
    $('#finder-anzahl').textContent = treffer.length === 1 ? '1 Gerät passt' : treffer.length + ' Geräte passen';
    var alle = $('#finder-alle');
    if (nurGeraet && !alle) {
      alle = el('button', null, 'Alle Geräte zeigen');
      alle.id = 'finder-alle';
      alle.type = 'button';
      alle.addEventListener('click', function () { nurGeraet = null; alle.parentNode.removeChild(alle); neu(); });
      $('#finder-anzahl').parentNode.insertBefore(alle, $('#finder-anzahl').nextSibling);
    }
    var ziel = $('#finder-liste');
    ziel.textContent = '';
    if (!treffer.length) {
      ziel.appendChild(el('p', 'finder-nichts',
        'Kein Gerät hat alle gewählten Merkmale. Nimm eins heraus: Die Zahl hinter jeder Auswahl zeigt, wie viele Geräte dann passen.' +
        (mitUnbekannt ? '' : ' Oder nimm den Haken bei „Geräte ausblenden, bei denen Angaben fehlen“ heraus.')));
      return;
    }
    var kartenVon = {};
    treffer.forEach(function (t) {
      var g = t.g;
      var k = el('article', 'finder-karte');
      var ort = selectorOrt(g.image);
      if (ort) {
        var bild = document.createElement('img');
        bild.className = 'finder-bild';
        bild.alt = '';
        bild.loading = 'lazy';
        bild.src = 'pictures/' + ort.basis + '.svg';
        bild.onerror = function () { bild.style.visibility = 'hidden'; };
        k.appendChild(bild);
      }
      var rumpf = el('div', 'finder-rumpf');
      rumpf.appendChild(el('h2', null, g.modell));
      /* Nichts versprechen (adorfer 20.10.): "eventuell", kein Termin */
      if (g.stable === false) {
        rumpf.appendChild(el('p', 'finder-nicht-marke', 'Kommt eventuell in zukünftiger Firmware'));
        rumpf.appendChild(el('p', 'finder-naechste-hinweis',
          'Für dieses Gerät gibt es noch keine freigegebene Freifunk-Firmware. Ob und wann sie kommt, steht noch nicht fest.'));
      }
      if (g.speicher) {
        var sp = el('p', 'finder-speicher');
        var stufe = { 'reichlich': 'reichlich', 'gut': 'gut', 'ausreichend': 'reicht', 'knapp': 'knapp', 'zu wenig': 'sackgasse' }[g.speicher] || 'knapp';
        sp.appendChild(document.createTextNode('Speicher für Updates: '));
        sp.appendChild(el('span', 'ffnef-stufe ffnef-stufe-' + stufe, g.speicher));
        rumpf.appendChild(sp);
      }
      if (g.level) rumpf.appendChild(levelZeile(g));
      var ul = el('ul', 'finder-chips');
      chips(g).forEach(function (c) { ul.appendChild(el('li', null, c)); });
      rumpf.appendChild(ul);
      if (t.fehlt.length) rumpf.appendChild(el('p', 'finder-fehlt', 'Es fehlen Angaben zu: ' + t.fehlt.join(', ')));
      if (g.unsicher) rumpf.appendChild(el('p', 'finder-unsicher',
        'Quellen widersprechen sich bei: ' + g.unsicher.map(feldName).join(', ')));
      rumpf.appendChild(kaufLinks(g));
      var knoepfe = el('p', 'finder-knoepfe');
      if (ort) {
        var a = el('a', 'finder-knopf', 'Firmware');
        a.href = 'https://routersoftware.ffnef.de/' + q(ort);
        knoepfe.appendChild(a);
      }
      if (g.url) {
        var b = el('a', 'finder-knopf finder-knopf-zwei', 'Anleitung');
        b.href = g.url;
        knoepfe.appendChild(b);
      }
      var det = el('button', 'finder-details-knopf', 'Alle Daten');
      det.type = 'button';
      knoepfe.appendChild(det);
      rumpf.appendChild(knoepfe);
      var platz = el('div', 'finder-details');
      rumpf.appendChild(platz);
      det.addEventListener('click', function () {
        if (platz.firstChild) { platz.textContent = ''; det.textContent = 'Alle Daten'; return; }
        det.textContent = 'Daten ausblenden';
        holen('geraete/' + g.image + '.json', function (d) {
          platz.textContent = '';
          platz.appendChild(d ? details(d) : el('p', null, 'Die Daten ließen sich nicht laden. Lade die Seite bitte neu.'));
        });
      });
      k.appendChild(rumpf);
      ziel.appendChild(k);
      kartenVon[g.image] = k;
      if (nurGeraet) det.click();
    });
    /* Nicht unterstuetzte Versionen hinter die letzte angezeigte Geschwisterkarte */
    var letzte = {};
    if (mitNicht || nurGeraet) nichtKarten.forEach(function (nk) {
      var nach = letzte[nk.geschwister.join(' ')];
      if (!nach) {
        treffer.forEach(function (t) { if (nk.geschwister.indexOf(t.g.image) > -1) nach = kartenVon[t.g.image]; });
      }
      if (!nach) return;
      var k = nichtKarte(nk);
      nach.parentNode.insertBefore(k, nach.nextSibling);
      letzte[nk.geschwister.join(' ')] = k;
    });
  }

  /* Volle Geraetedaten wie im Selector (geraete/<image>.json), mit Quellen. */
  var QUELLEN = [
    [/^(openwrt_forum|forum|instanton_community)/, 'Forum'], [/^(toh|openwrt_wiki)/, 'OpenWrt'],
    [/^(openwrt_|gh_pr_)/, 'OpenWrt-Quelltext'], [/^deviwiki/, 'DeviWiki'], [/^wikidevi/, 'WikiDevi'],
    [/^fcc/, 'FCC-Unterlagen'], [/^anatel/, 'Anatel'],
    [/^(hersteller|datenblatt|tplink_|avm_|dlink_|tpcdb)/, 'Hersteller'], [/^(haendler|markt)/, 'Händler'],
    [/^(blog|true_systems)/, 'Bericht'], [/^gluon/, 'Gluon'], [/^werkstatt/, 'eigener Test'],
    [/^anleitung/i, 'Anleitung']
  ];
  function quellName(k) {
    for (var i = 0; i < QUELLEN.length; i++) if (QUELLEN[i][0].test(String(k || ''))) return QUELLEN[i][1];
    return 'Quelle';
  }
  function quellen(belege) {
    var p = el('span', 'finder-quellen'), gesehen = {}, n = 0, rest = 0;
    (belege || []).forEach(function (b) {
      var name = quellName(b.quelle);
      if (!b.url || gesehen[b.url] || gesehen['n:' + name]) return;
      gesehen[b.url] = gesehen['n:' + name] = true;
      if (n >= 3) { rest++; return; }
      if (n++) p.appendChild(document.createTextNode(' '));
      var a = el('a', null, name);
      a.href = b.url; a.rel = 'noopener'; a.target = '_blank';
      a.title = (b.quelle || '') + (b.stand ? ', Stand ' + b.stand : '');
      p.appendChild(a);
    });
    if (rest) p.appendChild(document.createTextNode(' +' + rest));
    return n ? p : null;
  }
  function details(d) {
    var box = el('div');
    ['oben', 'mitte', 'technik'].forEach(function (teil) {
      var dl = el('dl', 'finder-dl');
      (d[teil] || []).forEach(function (z) {
        dl.appendChild(el('dt', null, z.titel));
        var dd = el('dd');
        if (z.kennwort) {
          dd.appendChild(el('span', 'ffnef-stufe ffnef-stufe-' + z.stufe, z.kennwort + ':'));
          dd.appendChild(document.createTextNode(' '));
        }
        dd.appendChild(document.createTextNode(z.wert));
        if (z.erklaerung) dd.appendChild(el('span', 'finder-erkl', ' (' + z.erklaerung + ')'));
        if (z.warnung) dd.appendChild(el('p', 'finder-warnung', z.warnung));
        (z.abweichend || []).forEach(function (a) {
          var p = el('p', 'finder-unsicher', 'Andere Angabe: ' + a.wert + ' ');
          var qq = quellen(a.belege); if (qq) p.appendChild(qq);
          dd.appendChild(p);
        });
        var q2 = quellen(z.belege); if (q2) { dd.appendChild(document.createTextNode(' ')); dd.appendChild(q2); }
        dl.appendChild(dd);
      });
      if (dl.firstChild) box.appendChild(dl);
    });
    var f = el('p', 'finder-daten');
    (d.links || []).forEach(function (l, i) {
      if (i) f.appendChild(document.createTextNode(' · '));
      var a = el('a', null, l.name); a.href = l.url; a.rel = 'noopener'; a.target = '_blank';
      f.appendChild(a);
    });
    box.appendChild(f);
    /* "Fehler melden" (fehler-melden.js aus firmware-selector-config) */
    if (window.ffnefFehlerMelden && d.image) {
      var titel = [];
      ['oben', 'mitte', 'technik'].forEach(function (t) {
        (d[t] || []).forEach(function (z) { if (z.titel && titel.indexOf(z.titel) < 0) titel.push(z.titel); });
      });
      window.ffnefFehlerMelden(box, { image: d.image, modell: d.modell, zeilen: titel });
    }
    return box;
  }

  function zustandSchreiben() {
    var teile = [];
    Object.keys(wahl).forEach(function (k) {
      teile.push(encodeURIComponent(k) + '=' + wahl[k].map(function (x) { return encodeURIComponent(String(x)); }).join(','));
    });
    if (!mitUnbekannt) teile.push('unbekannt=0');
    if (mitNicht) teile.push('nicht=1');
    if (namensSuche) teile.push('name=' + encodeURIComponent(namensSuche));
    if (sortierung !== 'einfach') teile.push('sort=' + sortierung);
    if (nurGeraet) teile.push('geraet=' + encodeURIComponent(nurGeraet));
    history.replaceState(null, '', teile.length ? '?' + teile.join('&') : location.pathname);
  }

  function zustandLesen() {
    location.search.substring(1).split('&').forEach(function (p) {
      if (!p) return;
      var kv = p.split('=');
      var k = decodeURIComponent(kv[0]), v = decodeURIComponent(kv[1] || '');
      if (k === 'unbekannt') { mitUnbekannt = v !== '0'; return; }
      if (k === 'name') { namensSuche = v; return; }
      if (k === 'nicht' || k === 'naechste') { mitNicht = v === '1'; return; }   // naechste: alter Name
      if (k === 'sort') { sortierung = v; return; }
      if (k === 'geraet') { nurGeraet = v; return; }
      var f = ALLE.filter(function (x) { return x.id === k; })[0];
      if (!f) return;
      wahl[k] = (f.typ === 'ja' || f.typ === 'nein') ? [true] : v.split(',');
    });
    $('#finder-unbekannt').checked = !mitUnbekannt;
    $('#finder-nicht').checked = mitNicht;
    $('#finder-name').value = namensSuche;
    $('#finder-sortierung').value = sortierung;
  }

  function neu() {
    zustandSchreiben();
    filterZeichnen();
    listeZeichnen();
  }

  function los() {
    holen('geraete/facetten.json', function (d) {
      if (!d || !d.geraete) {
        $('#finder-liste').appendChild(el('p', 'finder-nichts', 'Die Daten ließen sich nicht laden. Lade die Seite bitte neu.'));
        return;
      }
      holen('anleitungen/index.json', function (anl) {
        var a = {};
        (anl || []).forEach(function (e) { a[e.gluon_name] = e; });
        Object.keys(d.geraete).forEach(function (img) {
          var g = d.geraete[img];
          g.image = img;
          var x = a[img];
          if (x) { g.level = x.level; g.risiko = x.risiko; g.status = x.status; g.url = x.url; }
          /* Ohne Anleitung ist das Geraet auch nicht von uns erprobt; "unbekannt" wuerde
             es bei eingeblendeten unvollstaendigen Angaben als Treffer zaehlen (adorfer). */
          if (!g.status) g.status = 'ungeprüft';
          geraete.push(g);
        });
        legendeZeichnen();
        holen('preise.json', function (pz) {
        /* Fehlt die Datei (noch kein Cron-Lauf), bleibt alles wie vorher. */
        if (pz && pz.geraete) {
          preiseStand = (pz.stand || '').split('-').reverse().join('.');
          geraete.forEach(function (g) {
            var x = pz.geraete[g.image];
            if (x) { g.preis = x.ca_eur; g.preis_ab = x.ab_eur; g.preis_hinweis = x.hinweis || ''; }
          });
        }
        holen('geraete/nicht-unterstuetzt.json', function (n) {
        nichtKarten = (n && n.karten) || [];
        zustandLesen();
        $('#finder-unbekannt').addEventListener('change', function (e) { mitUnbekannt = !e.target.checked; neu(); });
        $('#finder-nicht').addEventListener('change', function (e) { mitNicht = e.target.checked; neu(); });
        $('#finder-sortierung').addEventListener('change', function (e) { sortierung = e.target.value; neu(); });
        var warte = null;
        $('#finder-name').addEventListener('input', function (e) {
          clearTimeout(warte);
          warte = setTimeout(function () { namensSuche = e.target.value.trim(); neu(); }, 200);
        });
        $('#finder-leeren').addEventListener('click', function () {
          wahl = {}; nurGeraet = null; namensSuche = ''; $('#finder-name').value = ''; neu();
        });
        neu();
        });
        });
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', los);
  else los();
})();
