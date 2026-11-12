#!/usr/bin/env python3
import json, argparse
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'

def render(map_id,out,scale=1):
    maps=json.loads((BUILD/'analysis/map-index.json').read_text(encoding='utf-8'))
    m=next(x for x in maps if x['id']==str(map_id))
    atlas=Image.open(BUILD/'assets/map'/m['tileset']).convert('RGBA')
    cols=atlas.width//m['tileWidth']; tw=m['tileWidth']; th=m['tileHeight']
    canvas=Image.new('RGBA',(m['worldWidth'],m['worldHeight']),(20,28,37,255))
    for r in range(m['rows']):
        for c in range(m['columns']):
            v=m['layer1'][r][c]
            if not v: continue
            idx=abs(v)-1
            tile=atlas.crop(((idx%cols)*tw,(idx//cols)*th,(idx%cols+1)*tw,(idx//cols+1)*th))
            t=m['layer2'][r][c]
            if t==1: tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            elif t==2: tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif t==3: tile=tile.transpose(Image.Transpose.ROTATE_180)
            elif t==4: tile=tile.transpose(Image.Transpose.TRANSPOSE)
            elif t==5: tile=tile.transpose(Image.Transpose.ROTATE_270)
            elif t==6: tile=tile.transpose(Image.Transpose.ROTATE_90)
            elif t==7: tile=tile.transpose(Image.Transpose.TRANSVERSE)
            canvas.alpha_composite(tile,(c*tw,r*th))
    d=ImageDraw.Draw(canvas)
    for ob in m['objects']:
        x,y=ob['x'],ob['y']
        color=(231,184,87,255) if ob['descriptor'].startswith('名称+') else (96,208,220,255)
        d.ellipse((x-4,y-4,x+4,y+4),fill=color,outline=(5,12,18,255),width=1)
    if scale!=1: canvas=canvas.resize((canvas.width*scale,canvas.height*scale),Image.Resampling.NEAREST)
    Path(out).parent.mkdir(parents=True,exist_ok=True); canvas.convert('RGB').save(out)
    print(f'Map {map_id}: {m["worldWidth"]}x{m["worldHeight"]}, {len(m["objects"])} entities -> {out}')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('map_id'); ap.add_argument('--out',default='previews/map-preview.png'); ap.add_argument('--scale',type=int,default=1); a=ap.parse_args(); render(a.map_id,ROOT/a.out,a.scale)
