#!/usr/bin/env python3
"""Sanity-check extracted TDCK assets and generated parser indexes."""
import json, sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'build'
inv=json.loads((B/'analysis/inventory.json').read_text(encoding='utf-8'))
maps=json.loads((B/'analysis/map-index.json').read_text(encoding='utf-8'))
acts=json.loads((B/'analysis/act-index.json').read_text(encoding='utf-8'))
ms_index=json.loads((B/'analysis/ms-index.json').read_text(encoding='utf-8'))
decoded=list((B/'assets/script/decoded').rglob('*.ms'))
errors=[]
if inv['extensions'].get('.map')!=124: errors.append('Expected 124 map files')
if inv['extensions'].get('.act')!=123: errors.append('Expected 123 ACT files')
if inv['extensions'].get('.ms')!=820: errors.append('Expected 820 MS files')
if len(maps)!=124: errors.append(f'Map JSON count is {len(maps)}')
if len(acts)!=123: errors.append(f'ACT JSON count is {len(acts)}')
if len(decoded)!=820: errors.append(f'Decoded MS count is {len(decoded)}')
if ms_index.get('scriptCount')!=820: errors.append(f"MS index script count is {ms_index.get('scriptCount')}")
if ms_index.get('sceneCount')!=127: errors.append(f"Expected 127 scene records, got {ms_index.get('sceneCount')}")
map_ids={int(m['id']):m for m in maps}
for scene in ms_index.get('scenes',[]):
    map_data=map_ids.get(int(scene['mapId']))
    if map_data is not None and scene.get('spawn') is not None:
        spawn=scene['spawn']
        if not (0<=spawn['x']<=map_data['worldWidth'] and 0<=spawn['y']<=map_data['worldHeight']):
            errors.append(f"Scene {scene['script']} spawn is outside map {map_data['id']}")
for m in maps:
    if not (B/'assets/map'/m['tileset']).exists(): errors.append(f"Map {m['id']} missing tileset {m['tileset']}")
    if len(m['layer1'])!=m['rows'] or any(len(r)!=m['columns'] for r in m['layer1']): errors.append(f"Map {m['id']} matrix dimension mismatch")
for a in acts:
    names=a['imageFiles'] or [a['file'][:-4]+'.png']
    sizes=[]
    for n in names:
        p=B/'assets/sprite'/n
        if not p.exists(): errors.append(f"ACT {a['file']} missing atlas {n}")
        else:
            with Image.open(p) as im: sizes.append(im.size)
    for i,r in enumerate(a['rectangles']):
        x,y,w,h,*rest=r; ai=rest[0] if rest else 0
        if w<=0 or h<=0: continue # preserve zero-size legacy sentinels
        if ai>=len(sizes) or min(x,y)<0 or x+w>sizes[ai][0] or y+h>sizes[ai][1]:
            errors.append(f"ACT {a['file']} rectangle {i} falls outside its atlas")
full=sum(1 for a in acts if a['unparsedTailBytes']==0)
print(f'MS decoded/indexed: {len(decoded)}/820; scene definitions: {ms_index.get("sceneCount")}')
print(f'Maps parsed: {len(maps)}/124 (each parser run checks exact EOF)')
print(f'ACT parsed: {len(acts)}/123; fully consumed: {full}/123')
print(f'Archive pngs copied: {sum(1 for _ in (B/"assets").rglob("*.png"))}/157')
if errors:
    print('FAIL:');print('\n'.join('- '+e for e in errors));sys.exit(1)
print('PASS: required files/references/dimensions are present.')
