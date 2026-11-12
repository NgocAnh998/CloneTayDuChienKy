#!/usr/bin/env python3
"""Unpack and inspect Tay Du Chien Ky (Java ME) assets.

Verified formats:
- *.ms: each byte is XORed with 0x01 before the game parses it.
- *.map: Java DataInputStream format parsed below; two tile layers and object descriptors.
- LXA2 *.act: sprite atlas/animation metadata parsed below.

Usage: python tools/tdck_unpack.py input.jar --out output_dir
"""
from __future__ import annotations
import argparse, json, struct, zipfile, shutil
from pathlib import Path
from collections import Counter

class Reader:
    def __init__(self, data: bytes): self.data=data; self.pos=0
    def take(self,n):
        if n<0 or self.pos+n>len(self.data): raise ValueError(f"Unexpected EOF at {self.pos}: need {n}, size {len(self.data)}")
        x=self.data[self.pos:self.pos+n]; self.pos+=n; return x
    def u8(self): return self.take(1)[0]
    def i8(self):
        x=self.u8(); return x if x<128 else x-256
    def i16(self): return struct.unpack('>h',self.take(2))[0]
    def u16(self): return struct.unpack('>H',self.take(2))[0]
    def i32(self): return struct.unpack('>i',self.take(4))[0]
    def utf(self):
        # Game files use Java DataInputStream.writeUTF; current resource strings decode as UTF-8.
        n=self.u16(); return self.take(n).decode('utf-8','replace')

def parse_map(path: Path):
    r=Reader(path.read_bytes())
    signature=[r.i16(),r.i16()]
    image=r.utf()
    rows=r.i16(); cols=r.i16(); tile_w=r.u8(); tile_h=r.u8()
    if not (0<rows<=256 and 0<cols<=512 and 0<rows*cols<=100000):
        raise ValueError(f"Implausible dimensions {rows}x{cols}")
    # The original game stores matrices as [row][column].
    layer1=[[r.i8() for _ in range(cols)] for __ in range(rows)]
    layer2=[[r.i8() for _ in range(cols)] for __ in range(rows)]
    static_count=r.i16()
    if not 0<=static_count<=10000: raise ValueError(f"Bad static count: {static_count}")
    static=[]
    for _ in range(static_count): static.append({"rect_data":r.utf(),"metadata":r.utf()})
    object_count=r.i16()
    if not 0<=object_count<=10000: raise ValueError(f"Bad object count: {object_count}")
    objects=[]
    for _ in range(object_count):
        x=r.i16(); y=r.i16(); desc=r.utf()
        objects.append({"x":x,"y":y,"descriptor":desc,"tokens":desc.split('+')})
    if r.pos != len(r.data):
        raise ValueError(f"Parser left {len(r.data)-r.pos} bytes unread")
    return {
        "id":path.stem,"signature":signature,"tileset":image,"rows":rows,"columns":cols,
        "tileWidth":tile_w,"tileHeight":tile_h,"worldWidth":cols*tile_w,
        "worldHeight":rows*tile_h,"layer1":layer1,"layer2":layer2,
        "staticObjects":static,"objects":objects,"bytes":len(r.data)
    }

def parse_act(path: Path):
    r=Reader(path.read_bytes()); signature=r.data[:4]; is_lxa2=(signature==b'LXA2')
    image_names=[]
    if is_lxa2:
        r.take(4)              # read() of the signature again, as in lx.game.ar
        _empty=r.utf()         # empty UTF metadata field in this version
        image_count=r.i16()
        if not 0<=image_count<=64: raise ValueError(f"Bad image count: {image_count}")
        image_names=[r.utf() for _ in range(image_count)]
    rect_count=r.i16()
    if not 0<=rect_count<=5000: raise ValueError(f"Bad rectangle count: {rect_count}")
    rectangles=[]
    for _ in range(rect_count):
        rec=[r.i16() for __ in range(4)]
        if is_lxa2: rec.append(r.i8())
        rectangles.append(rec)
    anim_count=r.i16()
    if not 0<=anim_count<=5000: raise ValueError(f"Bad animation count: {anim_count}")
    animations=[]
    for _ in range(anim_count):
        frame_count=r.i16()
        if not 0<=frame_count<=5000: raise ValueError(f"Bad frame count: {frame_count}")
        r1=[r.i16() for __ in range(4)]; r2=[r.i16() for __ in range(4)]
        frames=[[r.i16() for __ in range(4)] for ___ in range(frame_count)]
        animations.append({"frameCount":frame_count,"boundsA":r1,"boundsB":r2,"frames":frames})
    seq_count=r.i16()
    if not 0<=seq_count<=5000: raise ValueError(f"Bad sequence count: {seq_count}")
    sequences=[]
    for _ in range(seq_count):
        n=r.i16()
        if not 0<=n<=10000: raise ValueError(f"Bad sequence length: {n}")
        sequences.append([r.i16() for __ in range(n)])
    extra=[]
    if is_lxa2:
        for _ in range(anim_count):
            n=r.i16()
            if not 0<=n<=5000: raise ValueError(f"Bad auxiliary count: {n}")
            group=[]
            for __ in range(n):
                name=r.utf(); source=r.utf(); duration=r.i16()
                rect=[r.i16() for ___ in range(4)]
                flags=[r.i16() for ___ in range(4)]
                group.append({"name":name,"source":source,"duration":duration,"rect":rect,"flags":flags})
            extra.append(group)
    remaining=r.data[r.pos:]
    return {
        "file":path.name,"signature":signature.decode('latin1'),"format":"LXA2" if is_lxa2 else "legacy",
        "imageFiles":image_names,"rectangleCount":rect_count,"rectangles":rectangles,
        "animationCount":anim_count,"animations":animations,"sequenceCount":seq_count,
        "sequences":sequences,"auxiliaryGroups":extra,"unparsedTailBytes":len(remaining),
        "unparsedTailHex":remaining.hex()
    }

def copy_tree_files(src: Path, dst: Path, suffixes):
    dst.mkdir(parents=True,exist_ok=True)
    for p in src.rglob('*'):
        if p.is_file() and p.suffix.lower() in suffixes:
            target=dst/p.name
            shutil.copy2(p,target)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('jar',type=Path)
    ap.add_argument('--out',type=Path,default=Path('TDCK-extracted'))
    args=ap.parse_args(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    raw=out/'raw'; raw.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.jar) as z: z.extractall(raw)
    script_src=raw/'script'; dec=out/'assets/script/decoded'
    if dec.exists(): shutil.rmtree(dec)
    dec.mkdir(parents=True,exist_ok=True)
    # Decode every .ms in the archive, including the five UI scripts stored at the archive root.
    for p in raw.rglob('*.ms'):
        rel=p.relative_to(raw)
        target=dec/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(bytes(v^1 for v in p.read_bytes()))
    map_src=raw/'map'; sprite_src=raw/'sprite'
    copy_tree_files(map_src,out/'assets/map',{'.png','.map'})
    copy_tree_files(sprite_src,out/'assets/sprite',{'.png','.act'})
    copy_tree_files(raw/'image',out/'assets/ui',{'.png'})
    copy_tree_files(raw/'data',out/'assets/data',{'.dat'})
    # Root-level UI images are also part of the original game package.
    for p in raw.glob('*.png'):
        shutil.copy2(p,out/'assets/ui'/p.name)
    maps=[]
    for p in sorted(map_src.glob('*.map'),key=lambda q:int(q.stem)):
        maps.append(parse_map(p))
    acts=[]
    for p in sorted(sprite_src.glob('*.act')):
        acts.append(parse_act(p))
    inventory=Counter(p.suffix.lower() for p in raw.rglob('*') if p.is_file())
    (out/'analysis').mkdir(exist_ok=True)
    (out/'analysis/map-index.json').write_text(json.dumps(maps,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'analysis/act-index.json').write_text(json.dumps(acts,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'analysis/inventory.json').write_text(json.dumps({"entries":sum(inventory.values()),"extensions":dict(inventory)},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Extracted {sum(inventory.values())} files to {out}")
    print(f"Parsed maps: {len(maps)}; ACT files: {len(acts)}; decoded MS scripts: {len(list(dec.rglob('*.ms')))}")
    print(f"Map parser exact-consumption check: PASS for all {len(maps)} maps")
    complete=sum(1 for a in acts if a['unparsedTailBytes']==0)
    print(f"ACT parser consumed fully: {complete}/{len(acts)} (legacy tail bytes preserved in JSON)")

if __name__=='__main__': main()
