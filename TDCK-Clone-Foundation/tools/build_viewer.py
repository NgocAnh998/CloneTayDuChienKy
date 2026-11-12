#!/usr/bin/env python3
"""Build a self-contained offline HTML map inspector from the verified parser output."""
import base64, json, mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
OUT = ROOT / 'viewer' / 'index.html'
maps = json.loads((BUILD/'analysis'/'map-index.json').read_text(encoding='utf-8'))
images = {}
for name in sorted({m['tileset'] for m in maps}):
    raw = (BUILD/'assets'/'map'/name).read_bytes()
    mime = mimetypes.guess_type(name)[0] or 'image/png'
    images[name] = f'data:{mime};base64,' + base64.b64encode(raw).decode('ascii')

html = r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tây Du Chiến Ký — Map Inspector</title>
<style>
:root{color-scheme:dark;--bg:#0d1118;--panel:#161e29;--line:#2b394a;--text:#e8edf4;--muted:#9aabc0;--gold:#e5b95c;--cyan:#65c9d7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Segoe UI,Arial,sans-serif}
header{padding:18px 22px;border-bottom:1px solid var(--line);background:#111925}h1{font-size:20px;margin:0 0 4px}header p{margin:0;color:var(--muted)}
main{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:14px;padding:14px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:12px;border-bottom:1px solid var(--line)}
label{color:var(--muted)}select,input,button{background:#0d1520;color:var(--text);border:1px solid #3a4b60;border-radius:6px;padding:7px 9px}button{cursor:pointer}button:hover{border-color:var(--gold)}input[type=checkbox]{accent-color:var(--gold)}
#mapWrap{overflow:auto;max-height:calc(100vh - 190px);min-height:360px;background:#080d14;padding:12px}canvas{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#101820;box-shadow:0 2px 16px #0008}
.side{padding:14px}.side h2{font-size:15px;margin:0 0 8px;color:var(--gold)}.statgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px}.stat{background:#0e1621;border:1px solid var(--line);border-radius:7px;padding:8px}.stat b{display:block;font-size:17px}.stat small{color:var(--muted)}
#objects{max-height:48vh;overflow:auto}.obj{padding:8px 0;border-bottom:1px solid #263342}.obj strong{color:var(--cyan);font-weight:600}.obj small{display:block;color:var(--muted);word-break:break-word}.tag{display:inline-block;color:#081116;background:var(--gold);border-radius:4px;padding:1px 5px;font-size:11px;margin-right:5px}
#hoverInfo{color:var(--muted);padding:8px 12px;border-top:1px solid var(--line);min-height:38px}.note{margin:12px 14px;padding:10px 12px;color:var(--muted);background:#151e29;border:1px solid var(--line);border-radius:8px}
@media(max-width:1000px){main{grid-template-columns:1fr}.side{order:2}#mapWrap{max-height:60vh}}
</style></head><body>
<header><h1>Tây Du Chiến Ký — Map Inspector</h1><p>Công cụ xem bản đồ ngoại tuyến được dựng từ dữ liệu .map và tileset gốc trong JAR. Không kết nối Internet.</p></header>
<main><section class="panel"><div class="toolbar">
<label for="mapSelect">Bản đồ</label><select id="mapSelect"></select>
<label for="zoom">Phóng to</label><select id="zoom"><option value="1">100%</option><option value="1.5" selected>150%</option><option value="2">200%</option><option value="3">300%</option></select>
<label><input id="showObjects" type="checkbox" checked> Đối tượng</label>
<label><input id="showGrid" type="checkbox"> Lưới ô</label>
<button id="fit">Vừa khung</button>
</div><div id="mapWrap"><canvas id="mapCanvas"></canvas></div><div id="hoverInfo">Di chuột lên bản đồ để xem tọa độ và đối tượng gần nhất.</div></section>
<aside class="panel side"><h2>Thông tin bản đồ</h2><div class="statgrid" id="stats"></div><h2>Đối tượng được khai báo</h2><div id="objects"></div></aside></main>
<div class="note">Lưu ý: các điểm màu trên bản đồ là tọa độ đối tượng được khai báo trong file .map, chưa phải sprite đã render. Nội dung descriptor được giữ nguyên để tiếp tục ánh xạ sang hệ thống nhân vật/NPC/quái của game.</div>
<script>
const MAPS=__MAPS__;
const ATLAS=__IMAGES__;
const $=id=>document.getElementById(id);
const canvas=$('mapCanvas'),ctx=canvas.getContext('2d');
const loaded={};let current=null,zoom=1.5,hitPoints=[];
function imageFor(name){if(!loaded[name]){loaded[name]=new Image();loaded[name].src=ATLAS[name];loaded[name].onload=()=>{if(current)draw()}}return loaded[name]}
function mapById(id){return MAPS.find(m=>m.id===id)}
function applyTransform(c,x,y,code){
  c.translate(x+16,y+16);
  // Java ME Sprite.TRANS_*; code 2 is horizontal mirror (also verified in the Nokia branch).
  switch(code){case 1:c.scale(1,-1);break;case 2:c.scale(-1,1);break;case 3:c.rotate(Math.PI);break;case 4:c.rotate(Math.PI/2);c.scale(1,-1);break;case 5:c.rotate(Math.PI/2);break;case 6:c.rotate(-Math.PI/2);break;case 7:c.rotate(-Math.PI/2);c.scale(1,-1);break;}
}
function drawTile(img,idx,dx,dy,trans){const cols=Math.floor(img.width/32);const sx=(idx%cols)*32,sy=Math.floor(idx/cols)*32;ctx.save();applyTransform(ctx,dx,dy,trans);ctx.drawImage(img,sx,sy,32,32,-16,-16,32,32);ctx.restore()}
function draw(){if(!current)return;const m=current,img=imageFor(m.tileset);if(!img.complete||!img.naturalWidth)return;
 zoom=Number($('zoom').value);canvas.width=Math.round(m.worldWidth*zoom);canvas.height=Math.round(m.worldHeight*zoom);canvas.style.width=canvas.width+'px';canvas.style.height=canvas.height+'px';
 ctx.setTransform(zoom,0,0,zoom,0,0);ctx.clearRect(0,0,m.worldWidth,m.worldHeight);ctx.fillStyle='#17202a';ctx.fillRect(0,0,m.worldWidth,m.worldHeight);
 for(let r=0;r<m.rows;r++)for(let c=0;c<m.columns;c++){const raw=m.layer1[r][c];if(!raw)continue;drawTile(img,Math.abs(raw)-1,c*32,r*32,m.layer2[r][c]||0)}
 if($('showGrid').checked){ctx.save();ctx.strokeStyle='rgba(255,255,255,.17)';ctx.lineWidth=.6;for(let x=0;x<=m.worldWidth;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,m.worldHeight);ctx.stroke()}for(let y=0;y<=m.worldHeight;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(m.worldWidth,y);ctx.stroke()}ctx.restore()}
 hitPoints=[];if($('showObjects').checked){m.objects.forEach((o,i)=>{const x=o.x,y=o.y;hitPoints.push({x,y,o,i});ctx.save();ctx.fillStyle=o.descriptor.startsWith('名称+')?'#e7b857':'#61d0dc';ctx.strokeStyle='#101820';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,4.5,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.restore()})}
}
function selectMap(id){current=mapById(id);if(!current)return;const m=current;imageFor(m.tileset);$('stats').innerHTML=`<div class="stat"><b>${m.worldWidth} × ${m.worldHeight}</b><small>Kích thước pixel</small></div><div class="stat"><b>${m.rows} × ${m.columns}</b><small>Lưới bản đồ</small></div><div class="stat"><b>${m.tileset}</b><small>Ảnh tileset</small></div><div class="stat"><b>${m.objects.length}</b><small>Đối tượng</small></div>`;
 $('objects').innerHTML='';m.objects.forEach((o,i)=>{const el=document.createElement('div');el.className='obj';const d=document.createElement('div');d.innerHTML=`<span class="tag">${i+1}</span><strong>(${o.x}, ${o.y})</strong>`;const s=document.createElement('small');s.textContent=o.descriptor;el.append(d,s);el.addEventListener('click',()=>{ $('mapWrap').scrollTo({left:Math.max(0,o.x*zoom-180),top:Math.max(0,o.y*zoom-150),behavior:'smooth'});$('hoverInfo').textContent=`Đối tượng ${i+1}: ${o.descriptor} — tọa độ (${o.x}, ${o.y})`});$('objects').appendChild(el)});draw();}
MAPS.sort((a,b)=>Number(a.id)-Number(b.id));MAPS.forEach(m=>{const o=document.createElement('option');o.value=m.id;o.textContent=`Map ${m.id} — ${m.tileset} — ${m.worldWidth}×${m.worldHeight}`;$('mapSelect').appendChild(o)});
$('mapSelect').addEventListener('change',e=>selectMap(e.target.value));$('zoom').addEventListener('change',draw);$('showObjects').addEventListener('change',draw);$('showGrid').addEventListener('change',draw);
$('fit').addEventListener('click',()=>{if(!current)return;const wrap=$('mapWrap');let z=Math.min(3,(wrap.clientWidth-28)/current.worldWidth);z=Math.max(.5,Math.floor(z*4)/4);$('zoom').innerHTML='';[.5,.75,1,1.25,1.5,2,2.5,3].forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=Math.round(v*100)+'%';$('zoom').appendChild(o)});$('zoom').value=String(z);draw();wrap.scrollTo({left:0,top:0})});
canvas.addEventListener('mousemove',e=>{if(!current)return;const r=canvas.getBoundingClientRect(),x=Math.floor((e.clientX-r.left)/zoom),y=Math.floor((e.clientY-r.top)/zoom),near=hitPoints.map(p=>({...p,d:Math.hypot(p.x-x,p.y-y)})).filter(p=>p.d<14).sort((a,b)=>a.d-b.d)[0];$('hoverInfo').textContent=near?`Tọa độ (${x}, ${y}) · gần đối tượng ${near.i+1}: ${near.o.descriptor}`:`Tọa độ (${x}, ${y}) · ô (${Math.floor(x/32)}, ${Math.floor(y/32)})`});
$('mapSelect').value='1';selectMap('1');
</script></body></html>'''
html = html.replace('__MAPS__', json.dumps(maps, ensure_ascii=False, separators=(',', ':')))
html = html.replace('__IMAGES__', json.dumps(images, ensure_ascii=False, separators=(',', ':')))
OUT.write_text(html, encoding='utf-8')
print(f'Wrote {OUT} ({OUT.stat().st_size:,} bytes), embedded {len(maps)} maps and {len(images)} tilesets.')
