#!/usr/bin/env python3
"""Selector-Image -> OpenWrt-Profil (Gluon targets/*) -> ToH-Eintrag (ueber Profil im Image-URL), Rest per Name."""
import re,json,gzip,csv,io,sys,glob,collections,os
DEV=os.path.expanduser('~/projekte/freifunk/scratch/fsc/ffnef/devices.js')
TG=sys.argv[2:]
s=open(DEV,encoding='utf-8').read()
imgs=sorted({i for i in set(re.findall(r'"([a-z0-9][a-z0-9.\-]{3,})"',s)) if '-' in i and i!='--ignore--'})
prof={}
for d in TG:
  for f in glob.glob(d+'/*'):
    t=open(f,errors='replace').read()
    for m in re.finditer(r"device\('([^']+)',\s*'([^']+)'",t): prof.setdefault(m[1],m[2])
    for m in re.finditer(r"aliases\s*=\s*\{([^}]*)\}",t): pass
rows=list(csv.DictReader(io.TextIOWrapper(gzip.open(sys.argv[1]),encoding='utf-8',errors='replace'),delimiter='\t'))
byprof=collections.defaultdict(list)
for r in rows:
  for k in ('firmwareopenwrtinstallurl','firmwareopenwrtupgradeurl','firmwareopenwrtsnapshotinstallurl','firmwareopenwrtsnapshotupgradeurl'):
    for u in (r.get(k) or '').split(','):
      m=re.search(r'openwrt-(?:[\d.]+-|snapshot-)?(?:r\d+-\w+-)?[a-z0-9]+-[a-z0-9_]+-(.+?)-(?:squashfs|initramfs|ext4|factory|sysupgrade|ubi|nand)',u.strip())
      if m and r not in byprof[m[1]]: byprof[m[1]].append(r)
hit={};miss=[]
for i in imgs:
  p=prof.get(i); c=byprof.get(p) if p else None
  if c: hit[i]={'profil':p,'toh':c}
  else: miss.append((i,p))
print("Images",len(imgs),"mit Profil",sum(1 for i in imgs if i in prof),"ToH-Treffer",len(hit),"ohne",len(miss))
json.dump(hit,open('toh_treffer.json','w'),ensure_ascii=False)
open('toh_ohne.txt','w').write('\n'.join(f"{i}\t{p}" for i,p in miss)+'\n')
