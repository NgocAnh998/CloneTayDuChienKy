(() => {
  "use strict";

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height, TILE = 48;
  const keys = new Set();
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const dist = (a,b) => Math.hypot(a.x-b.x,a.y-b.y);
  const saved = (() => { try { return JSON.parse(localStorage.getItem("tdck-save") || "null"); } catch { return null; } })();

  const player = {
    x: saved?.x ?? 470, y: saved?.y ?? 335, r: 13, speed: 175,
    hp: saved?.hp ?? 100, maxHp: 100, level: saved?.level ?? 1,
    exp: saved?.exp ?? 0, gold: saved?.gold ?? 0,
    facing: "down", attack: 0, skill: 0, dash: 0, invuln: 0
  };
  const enemies = [];
  const npc = {x: 480, y: 205, name:"Trưởng thôn", near:false};
  const quest = {kills:saved?.kills ?? 0, target:3, done:saved?.done ?? false};
  let camera = {x:0,y:0}, last = 0, toastTimer = 0, dialogOpen = false;
  let particles = [];

  const terrain = [];
  for (let y=0;y<18;y++) {
    terrain[y] = [];
    for (let x=0;x<30;x++) {
      const edge = x===0||y===0||x===29||y===17;
      const path = (y>=7&&y<=9) || (x>=13&&x<=16);
      terrain[y][x] = edge ? 2 : path ? 1 : ((x*17+y*13)%11===0 ? 3 : 0);
    }
  }
  const obstacles = [
    {x:140,y:120,w:110,h:75},{x:690,y:125,w:120,h:80},
    {x:130,y:420,w:100,h:80},{x:740,y:420,w:110,h:75},
    {x:385,y:85,w:55,h:45},{x:565,y:430,w:65,h:55}
  ];
  function spawnEnemy(x,y){ enemies.push({x,y,r:13,hp:42,maxHp:42,alive:true,hit:0,attackCd:0,dir:0,phase:Math.random()*6.28}); }
  [[290,250],[350,390],[620,285],[680,365],[250,330],[580,150]].forEach(p=>spawnEnemy(...p));

  function toast(text){const el=document.getElementById("toast");el.textContent=text;el.classList.add("show");toastTimer=2.1;}
  function save(){try{localStorage.setItem("tdck-save",JSON.stringify({x:player.x,y:player.y,hp:player.hp,level:player.level,exp:player.exp,gold:player.gold,kills:quest.kills,done:quest.done}));}catch{}}
  function updateHud(){
    document.getElementById("level").textContent=player.level;
    document.getElementById("hpBar").style.width=(player.hp/player.maxHp*100)+"%";
    document.getElementById("hpText").textContent=Math.ceil(player.hp)+" / "+player.maxHp+" HP";
    document.getElementById("expText").textContent=player.exp+" / "+(player.level*50);
    document.getElementById("goldText").textContent=player.gold;
    document.getElementById("questTitle").textContent=quest.done?"Sơn đạo bình yên":"Dọn dẹp sơn đạo";
    document.getElementById("questDesc").textContent=quest.done?"Bạn đã giúp dân làng an toàn trở lại.":"Đánh bại 3 Sơn Tặc quanh khu vực.";
    document.getElementById("questProgress").style.width=(Math.min(quest.kills,3)/3*100)+"%";
    document.getElementById("questCount").textContent=Math.min(quest.kills,3)+" / 3";
  }
  function levelCheck(){while(player.exp>=player.level*50){player.exp-=player.level*50;player.level++;player.maxHp+=18;player.hp=player.maxHp;toast("Lên cấp "+player.level+"! HP đã hồi đầy.");}}
  function burst(x,y,color,n=8){for(let i=0;i<n;i++){const a=Math.random()*Math.PI*2,s=25+Math.random()*100;particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s,life:.35+Math.random()*.3,color});}}
  function attack(skill=false){
    if(dialogOpen||player.attack>0||player.skill>0)return;
    if(skill){if(player.skill>0)return;player.skill=1.0;player.attack=.3;toast("Hỏa quyền!");}
    else player.attack=.28;
    const reach=skill?105:65, damage=skill?34+player.level*8:19+player.level*5;
    let hitCount=0;
    for(const e of enemies){if(!e.alive)continue;const d=dist(player,e);if(d>reach)continue;
      const dx=e.x-player.x,dy=e.y-player.y;
      const facingOK=skill||((player.facing==="up"&&dy<-4)||(player.facing==="down"&&dy>4)||(player.facing==="left"&&dx<-4)||(player.facing==="right"&&dx>4));
      if(facingOK){e.hp-=damage;e.hit=.18;hitCount++;burst(e.x,e.y,skill?"#ffb34d":"#f4e0a1",skill?13:6);if(e.hp<=0){e.alive=false;player.exp+=18;player.gold+=5+Math.floor(Math.random()*8);quest.kills++;levelCheck();if(!quest.done&&quest.kills>=3){quest.done=true;player.gold+=50;toast("Nhiệm vụ hoàn thành! +50 vàng.");}else toast("Hạ Sơn Tặc! +EXP và vàng.");}}
    }
    if(!hitCount)toast(skill?"Hỏa quyền đánh hụt!":"Không có mục tiêu trong tầm.");
    updateHud();save();
  }
  function interact(){
    if(dist(player,npc)>65){toast("Đến gần Trưởng thôn để tương tác.");return;}
    dialogOpen=true;
    document.getElementById("dialogTitle").textContent=npc.name;
    document.getElementById("dialogText").textContent=quest.done?"Đa tạ hiệp khách đã dẹp yên sơn đạo. Dân làng sẽ nhớ ơn người!":"Gần đây sơn tặc hoành hành. Xin hãy giúp ta đánh bại 3 tên quanh làng. Ta sẽ thưởng 50 vàng!";
    document.getElementById("dialog").classList.remove("hidden");
  }
  document.getElementById("dialogClose").onclick=()=>{dialogOpen=false;document.getElementById("dialog").classList.add("hidden");};
  document.getElementById("helpBtn").onclick=()=>document.getElementById("help").classList.remove("hidden");
  document.getElementById("helpClose").onclick=()=>document.getElementById("help").classList.add("hidden");
  document.getElementById("resetBtn").onclick=()=>{if(confirm("Xóa toàn bộ tiến trình đã lưu?")){localStorage.removeItem("tdck-save");location.reload();}};

  addEventListener("keydown",e=>{
    const k=e.key.toLowerCase();
    if(["arrowup","arrowdown","arrowleft","arrowright"," "].includes(k))e.preventDefault();
    keys.add(k);
    if(e.repeat)return;
    if(k==="j")attack(false);if(k==="k")attack(true);if(k==="e")interact();
    if(k==="shift"&&player.dash<=0&&!dialogOpen){player.dash=.22;player.invuln=.3;}
    if(k==="escape"){dialogOpen=false;document.getElementById("dialog").classList.add("hidden");document.getElementById("help").classList.add("hidden");}
  });
  addEventListener("keyup",e=>keys.delete(e.key.toLowerCase()));
  addEventListener("blur",()=>keys.clear());

  function blocked(x,y){
    if(x<28||y<28||x>W-28||y>H-28)return true;
    return obstacles.some(o=>x>o.x-14&&x<o.x+o.w+14&&y>o.y-14&&y<o.y+o.h+14);
  }
  function move(dt){
    if(dialogOpen)return;
    let dx=0,dy=0;
    if(keys.has("w")||keys.has("arrowup"))dy--;
    if(keys.has("s")||keys.has("arrowdown"))dy++;
    if(keys.has("a")||keys.has("arrowleft"))dx--;
    if(keys.has("d")||keys.has("arrowright"))dx++;
    const len=Math.hypot(dx,dy)||1;dx/=len;dy/=len;
    if(dx||dy){if(Math.abs(dx)>Math.abs(dy))player.facing=dx>0?"right":"left";else player.facing=dy>0?"down":"up";}
    const speed=player.dash>0?player.speed*3.4:player.speed;
    const nx=player.x+dx*speed*dt,ny=player.y+dy*speed*dt;
    if(!blocked(nx,player.y))player.x=nx;
    if(!blocked(player.x,ny))player.y=ny;
  }
  function update(dt){
    player.attack=Math.max(0,player.attack-dt);player.skill=Math.max(0,player.skill-dt);player.dash=Math.max(0,player.dash-dt);player.invuln=Math.max(0,player.invuln-dt);
    move(dt);
    for(const e of enemies){if(!e.alive)continue;e.hit=Math.max(0,e.hit-dt);e.attackCd=Math.max(0,e.attackCd-dt);e.phase+=dt*2;
      const d=dist(player,e);if(d<210&&d>28){const dx=(player.x-e.x)/d,dy=(player.y-e.y)/d;e.x+=dx*42*dt;e.y+=dy*42*dt;}
      if(d<31&&e.attackCd<=0&&player.invuln<=0){player.hp-=8;e.attackCd=1.05;burst(player.x,player.y,"#d85a4b",5);if(player.hp<=0){player.hp=player.maxHp;player.x=470;player.y=335;player.gold=Math.max(0,player.gold-10);toast("Bạn đã gục ngã. Hồi sinh tại làng, mất 10 vàng.");save();}}
    }
    for(const p of particles){p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt;p.vx*=.94;p.vy*=.94;}particles=particles.filter(p=>p.life>0);
    if(toastTimer>0){toastTimer-=dt;if(toastTimer<=0)document.getElementById("toast").classList.remove("show");}
    camera.x=clamp(player.x-W/2,0,0);camera.y=clamp(player.y-H/2,0,0);
    updateHud();
  }
  function drawTree(x,y,s=1){ctx.fillStyle="#523b2b";ctx.fillRect(x-5*s,y,10*s,24*s);ctx.fillStyle="#244936";ctx.beginPath();ctx.arc(x,y-9*s,22*s,0,Math.PI*2);ctx.fill();ctx.fillStyle="#376447";ctx.beginPath();ctx.arc(x-9*s,y-15*s,12*s,0,Math.PI*2);ctx.fill();}
  function draw(){
    ctx.clearRect(0,0,W,H);
    for(let y=0;y<H;y+=TILE)for(let x=0;x<W;x+=TILE){const tx=Math.floor(x/TILE),ty=Math.floor(y/TILE),t=terrain[ty]?.[tx]??0;
      ctx.fillStyle=t===1?"#89704d":t===2?"#253b31":t===3?"#405b3d":"#34533b";ctx.fillRect(x,y,TILE,TILE);
      ctx.strokeStyle="#ffffff08";ctx.strokeRect(x,y,TILE,TILE);
      if(t===1){ctx.fillStyle="#a98b60";ctx.fillRect(x+4,y+8,2,2);ctx.fillRect(x+34,y+33,3,2);}
      else if(t===0&&((tx*7+ty*3)%9===0)){ctx.fillStyle="#668052";ctx.fillRect(x+13,y+20,3,3);}
    }
    // village lanterns and wooden huts
    for(const o of obstacles){ctx.fillStyle="#1b3028";ctx.fillRect(o.x+5,o.y+9,o.w,o.h);ctx.fillStyle="#9b6740";ctx.fillRect(o.x,o.y,o.w,o.h*.45);ctx.fillStyle="#d0a46a";ctx.fillRect(o.x+8,o.y+o.h*.45,o.w-16,o.h*.48);ctx.fillStyle="#4b3029";ctx.fillRect(o.x+o.w*.42,o.y+o.h*.48,o.w*.18,o.h*.45);ctx.fillStyle="#d9ad64";ctx.fillRect(o.x-5,o.y-6,o.w+10,8);}
    // scattered trees
    [[70,90,1.1],[300,80,.8],[870,95,1.2],[80,300,.9],[880,300,1.1],[300,520,1],[670,520,1],[870,520,.9],[530,80,.7]].forEach(t=>drawTree(...t));
    // NPC
    drawCharacter(npc.x,npc.y,"#e2b45d","村");
    ctx.fillStyle="#fff0c9";ctx.font="12px sans-serif";ctx.textAlign="center";ctx.fillText(npc.name,npc.x,npc.y-27);
    // enemies
    for(const e of enemies){if(!e.alive)continue;ctx.save();if(e.hit>0)ctx.globalAlpha=.55+.45*Math.sin(performance.now()*.08);drawCharacter(e.x,e.y,"#9b4b3c","賊");ctx.restore();ctx.fillStyle="#241b1a";ctx.fillRect(e.x-16,e.y-25,32,4);ctx.fillStyle="#d84d43";ctx.fillRect(e.x-16,e.y-25,32*Math.max(0,e.hp/e.maxHp),4);}
    // player shadow, dash trail and body
    if(player.dash>0){ctx.globalAlpha=.22;drawCharacter(player.x-player.facing==="left"?12:0,player.y,"#f3bd65","悟");ctx.globalAlpha=1;}
    drawCharacter(player.x,player.y,"#d94e31","悟",player.invuln>0);
    if(player.attack>0){ctx.strokeStyle=player.skill>0?"#ffb34d":"#ffe0a0";ctx.lineWidth=player.skill>0?8:5;ctx.globalAlpha=.8;ctx.beginPath();const a=player.facing==="up"?-Math.PI/2:player.facing==="down"?Math.PI/2:player.facing==="left"?Math.PI:0;ctx.arc(player.x,player.y,player.skill>0?65:42,a-.8,a+.8);ctx.stroke();ctx.globalAlpha=1;}
    for(const p of particles){ctx.globalAlpha=Math.max(0,p.life*2);ctx.fillStyle=p.color;ctx.fillRect(p.x,p.y,4,4);}ctx.globalAlpha=1;
    // subtle edge vignette
    const g=ctx.createRadialGradient(W/2,H/2,180,W/2,H/2,560);g.addColorStop(0,"#0000");g.addColorStop(1,"#090d0a55");ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    ctx.textAlign="left";ctx.font="11px sans-serif";ctx.fillStyle="#f8e6c8";ctx.fillText("LÀNG HOA QUẢ",18,H-18);
    ctx.textAlign="right";ctx.fillStyle="#f8e6c899";ctx.fillText("WASD Di chuyển  ·  J Đánh  ·  K Kỹ năng  ·  E Tương tác",W-18,H-18);
  }
  function drawCharacter(x,y,color,glyph,flash=false){
    ctx.save();ctx.translate(x,y);ctx.fillStyle="#111a15aa";ctx.beginPath();ctx.ellipse(0,10,15,7,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle=flash?"#ffffff":color;ctx.fillRect(-9,-12,18,20);ctx.fillStyle="#f0c69c";ctx.fillRect(-7,-24,14,13);
    ctx.fillStyle=glyph==="悟"?"#f2c64e":"#33241f";ctx.fillRect(-9,-27,18,5);ctx.fillRect(-12,-23,5,5);ctx.fillRect(7,-23,5,5);
    ctx.fillStyle="#38251f";ctx.fillRect(-5,-19,2,2);ctx.fillRect(3,-19,2,2);
    ctx.fillStyle="#4a3025";ctx.fillRect(-8,7,6,7);ctx.fillRect(2,7,6,7);
    if(glyph==="悟"){ctx.fillStyle="#e9b844";ctx.fillRect(-12,-11,24,3);ctx.fillRect(8,-5,4,14);}
    ctx.restore();
  }
  function frame(now){const dt=Math.min(.033,(now-last)/1000||0);last=now;update(dt);draw();requestAnimationFrame(frame);}
  updateHud();toast("Chào mừng đến Làng Hoa Quả!");requestAnimationFrame(frame);
})();