/* ---------------- language toggle ---------------- */
function setLang(l){
  document.body.classList.toggle('lang-vi', l==='vi');
  document.body.classList.toggle('lang-en', l==='en');
  document.getElementById('btn-en').classList.toggle('active', l==='en');
  document.getElementById('btn-vi').classList.toggle('active', l==='vi');
  document.documentElement.lang = l;
  try{ localStorage.setItem('psh-lang', l); }catch(e){}
}
(function(){ try{ var s=localStorage.getItem('psh-lang'); if(s) setLang(s);}catch(e){} })();

/* honor prefers-reduced-motion across canvas + counters */
var REDUCED = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

/* ---------------- voice level dial (critique page) ---------------- */
var LEVELS = {
  1:{en:["Warm","Polite, encouraging. Artifact only — never you.","--warm"], vi:["Ấm áp","Lịch sự, động viên. Chỉ hiện vật — không nhắm bạn.","--warm"], danger:false},
  2:{en:["Gentle","Soft-spoken notes, kindly framed.","--gentle"], vi:["Nhẹ nhàng","Góp ý nhẹ, đóng khung tử tế.","--gentle"], danger:false},
  3:{en:["Blunt","Direct, no cushioning — still about the work.","--blunt"], vi:["Thẳng","Trực diện, không đệm — vẫn về công việc.","--blunt"], danger:false},
  4:{en:["Savage","Sharp and unsparing on the artifact.","--savage"], vi:["Gắt","Sắc và không nương tay với hiện vật.","--savage"], danger:false},
  5:{en:["No-mercy","The default. Brutal, may jab you, but all about the work.","--no-mercy (default)"], vi:["Không khoan nhượng","Mặc định. Tàn nhẫn, có thể đá xéo bạn, nhưng vẫn về công việc.","--no-mercy (mặc định)"], danger:false},
  6:{en:["Roast","Roasts you as the author. Opt-in — asks to confirm.","--roast"], vi:["Quay","Chửi thẳng bạn với tư cách tác giả. Opt-in — hỏi xác nhận.","--roast"], danger:true},
  7:{en:["Harsher register","Escalates the Vietnamese register (ông/tôi → mày/tao). Opt-in.","level 7"], vi:["Bậc gắt hơn","Leo thang đại từ (ông/tôi → mày/tao). Opt-in.","mức 7"], danger:true},
  8:{en:["Harsher still","Stronger register, still grounded in evidence + a fix.","level 8"], vi:["Gắt hơn nữa","Đại từ mạnh hơn, vẫn dựa bằng chứng + cách sửa.","mức 8"], danger:true},
  9:{en:["Work-profanity","Work-aimed profanity. RE-CONFIRMS on every run; declines down to 8.","level 9"], vi:["Chửi thề (vào việc)","Chửi thề nhắm-công-việc. HỎI LẠI mỗi lần chạy; từ chối thì lùi về 8.","mức 9"], danger:true}
};
function setLevel(v){
  v = +v;
  var L = LEVELS[v];
  var lang = document.body.classList.contains('lang-vi') ? 'vi' : 'en';
  var d = L[lang];
  var knob = document.getElementById('knob');
  knob.style.left = ((v-1)/8*100) + '%';
  knob.style.borderColor = L.danger ? '#dc2626' : '#34d399';
  var tag = L.danger
    ? '<span class="dangertag danger">'+(lang==='vi'?'Nguy hiểm · opt-in':'Danger · opt-in')+'</span>'
    : '<span class="dangertag safe">'+(lang==='vi'?'An toàn · hiện vật':'Safe · artifact-only')+'</span>';
  document.getElementById('readout').innerHTML =
    '<div class="lv" style="color:'+(L.danger?'#fb5e7e':'#38bdf8')+'">'+v+'</div>'+
    '<div class="nm">'+d[0]+'</div>'+
    '<div class="alias">'+d[2]+'</div>'+
    '<div class="ds" style="margin-top:6px">'+d[1]+'</div>'+
    tag;
}
// dial only exists on the critique page — guard so dial-less pages don't throw
if(document.getElementById('vrange')){
  setLevel(5);
  // re-render readout text when language flips
  ['btn-en','btn-vi'].forEach(function(id){
    var b = document.getElementById(id);
    if(b) b.addEventListener('click', function(){ var r=document.getElementById('vrange'); if(r) setLevel(r.value); });
  });
}

/* ---------------- scroll reveal + bar fill + counters ---------------- */
var io = new IntersectionObserver(function(entries){
  entries.forEach(function(e){
    if(!e.isIntersecting) return;
    e.target.classList.add('in');
    // fill bars
    e.target.querySelectorAll('[data-bars] .bf').forEach(function(b){ b.style.width = b.dataset.w + '%'; });
    // count up
    e.target.querySelectorAll('[data-count]').forEach(function(n){
      var t = +n.dataset.count, cur = 0, step = Math.max(1, Math.round(t/28));
      if(REDUCED || t===0){ n.textContent=String(t); return; }
      var iv = setInterval(function(){ cur+=step; if(cur>=t){cur=t;clearInterval(iv);} n.textContent=cur; }, 26);
    });
    io.unobserve(e.target);
  });
},{threshold:.16});
document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });

/* ---------------- hero background: 3D constellation (Three.js) ----------------
   Tries a WebGL particle-network scene on the #net canvas; falls back to the 2D
   canvas constellation when Three.js / WebGL is unavailable. Reduced-motion skips
   both (CSS hides #net). Palette-colored to the four skill hues + gold. */
var HERO_COLORS = ['#38bdf8','#fb5e7e','#34d399','#a78bfa','#fbbf24'];

function init2DNet(){
  var c = document.getElementById('net'); if(!c) return;
  var x = c.getContext('2d'), W,H,pts,raf;
  function size(){ W=c.width=innerWidth; H=c.height=Math.max(innerHeight, 700); init(); }
  function init(){
    var n = Math.min(64, Math.floor(W/26)); pts = [];
    for(var i=0;i<n;i++) pts.push({x:Math.random()*W, y:Math.random()*H, vx:(Math.random()-.5)*.28, vy:(Math.random()-.5)*.28, c:HERO_COLORS[i%HERO_COLORS.length]});
  }
  function draw(){
    x.clearRect(0,0,W,H);
    for(var i=0;i<pts.length;i++){
      var p=pts[i]; p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1; if(p.y<0||p.y>H)p.vy*=-1;
      x.beginPath(); x.arc(p.x,p.y,1.6,0,6.28); x.fillStyle=p.c; x.globalAlpha=.8; x.fill();
      for(var j=i+1;j<pts.length;j++){
        var q=pts[j], dx=p.x-q.x, dy=p.y-q.y, d=Math.sqrt(dx*dx+dy*dy);
        if(d<128){ x.globalAlpha=(1-d/128)*.22; x.strokeStyle=p.c; x.lineWidth=1; x.beginPath(); x.moveTo(p.x,p.y); x.lineTo(q.x,q.y); x.stroke(); }
      }
    }
    x.globalAlpha=1; if(!REDUCED) raf=requestAnimationFrame(draw);
  }
  size(); draw();
  addEventListener('resize', function(){ cancelAnimationFrame(raf); size(); draw(); });
  document.addEventListener('visibilitychange', function(){ if(document.hidden){cancelAnimationFrame(raf);} else if(!REDUCED){draw();} });
}

function _dotTexture(){
  var s=64, cv=document.createElement('canvas'); cv.width=cv.height=s;
  var g=cv.getContext('2d'), grd=g.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  grd.addColorStop(0,'rgba(255,255,255,1)'); grd.addColorStop(.35,'rgba(255,255,255,.55)'); grd.addColorStop(1,'rgba(255,255,255,0)');
  g.fillStyle=grd; g.fillRect(0,0,s,s);
  return new THREE.CanvasTexture(cv);
}
function initHero3D(){
  var c = document.getElementById('net');
  if(!c || !window.THREE) return false;
  var renderer;
  try{ renderer = new THREE.WebGLRenderer({canvas:c, alpha:true, antialias:true}); }
  catch(e){ return false; }
  renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
  var scene = new THREE.Scene();
  var cam = new THREE.PerspectiveCamera(60, innerWidth/Math.max(innerHeight,700), 1, 400);
  cam.position.z = 64;
  var group = new THREE.Group(); scene.add(group);

  var N = Math.min(150, Math.max(70, Math.floor(innerWidth/12)));
  var R = 46, pos = new Float32Array(N*3), col = new Float32Array(N*3), nodes = [];
  var pal = HERO_COLORS.map(function(h){ return new THREE.Color(h); });
  for(var i=0;i<N;i++){
    var v = new THREE.Vector3((Math.random()*2-1)*R, (Math.random()*2-1)*R*0.7, (Math.random()*2-1)*R);
    nodes.push(v); pos[i*3]=v.x; pos[i*3+1]=v.y; pos[i*3+2]=v.z;
    var cc = pal[i%pal.length]; col[i*3]=cc.r; col[i*3+1]=cc.g; col[i*3+2]=cc.b;
  }
  var pgeo = new THREE.BufferGeometry();
  pgeo.setAttribute('position', new THREE.BufferAttribute(pos,3));
  pgeo.setAttribute('color', new THREE.BufferAttribute(col,3));
  var pmat = new THREE.PointsMaterial({size:2.6, map:_dotTexture(), vertexColors:true, transparent:true,
    depthWrite:false, blending:THREE.AdditiveBlending, sizeAttenuation:true, opacity:.95});
  group.add(new THREE.Points(pgeo, pmat));

  // static links between near nodes (fixed inside the rotating group)
  var lp=[], lc=[], TH=15, MAXL=320, cnt=0;
  for(var a=0;a<N && cnt<MAXL;a++) for(var b=a+1;b<N && cnt<MAXL;b++){
    if(nodes[a].distanceTo(nodes[b])<TH){
      lp.push(nodes[a].x,nodes[a].y,nodes[a].z, nodes[b].x,nodes[b].y,nodes[b].z);
      var ca=pal[a%pal.length]; lc.push(ca.r,ca.g,ca.b, ca.r,ca.g,ca.b); cnt++;
    }
  }
  var lgeo = new THREE.BufferGeometry();
  lgeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(lp),3));
  lgeo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(lc),3));
  var lmat = new THREE.LineBasicMaterial({vertexColors:true, transparent:true, opacity:.14, blending:THREE.AdditiveBlending, depthWrite:false});
  group.add(new THREE.LineSegments(lgeo, lmat));

  var mx=0, my=0, tx=0, ty=0, raf;
  addEventListener('mousemove', function(e){ tx=(e.clientX/innerWidth-.5); ty=(e.clientY/innerHeight-.5); });
  function resize(){ var h=Math.max(innerHeight,700); renderer.setSize(innerWidth,h,false); cam.aspect=innerWidth/h; cam.updateProjectionMatrix(); }
  resize(); addEventListener('resize', resize);
  function frame(){
    group.rotation.y += .0009; group.rotation.x += .00035;
    mx += (tx-mx)*.04; my += (ty-my)*.04;
    cam.position.x = mx*16; cam.position.y = -my*12; cam.lookAt(0,0,0);
    renderer.render(scene, cam);
    if(!REDUCED) raf=requestAnimationFrame(frame);
  }
  frame();
  document.addEventListener('visibilitychange', function(){ if(document.hidden){cancelAnimationFrame(raf);} else if(!REDUCED){frame();} });
  return true;
}
(function(){ if(REDUCED) return; if(!initHero3D()) init2DNet(); })();

/* ---------------- single-file hash router ---------------- */
/* Active ONLY in the portable build (where every page is one [data-route] panel).
   In the multipage build there are no [data-route] wrappers, so this no-ops and the
   server-baked .active nav class is left untouched. */
(function(){
  var panels = document.querySelectorAll('[data-route]');
  if(!panels.length) return;                       // multipage → real page links, nothing to route
  var navlinks = document.querySelectorAll('[data-nav]');
  function snap(panel){                             // force-reveal a just-shown panel (IO can't fire while hidden)
    panel.querySelectorAll('.reveal:not(.in)').forEach(function(el){ el.classList.add('in'); });
    panel.querySelectorAll('[data-bars] .bf').forEach(function(b){ b.style.width = b.dataset.w + '%'; });
    panel.querySelectorAll('[data-count]').forEach(function(n){ n.textContent = n.dataset.count; });
  }
  function route(force){
    var h = (location.hash || '').replace(/^#\/?/,'') || 'hub';
    var active = null;
    panels.forEach(function(p){ if(p.dataset.route===h) active=p; });
    if(!active){ h='hub'; panels.forEach(function(p){ if(p.dataset.route==='hub') active=p; }); }
    panels.forEach(function(p){ p.hidden = (p!==active); });
    navlinks.forEach(function(a){ a.classList.toggle('active', a.dataset.nav===h); });
    document.body.classList.toggle('view-home', h==='hub');
    document.body.classList.toggle('view-guide', h!=='hub');
    document.body.classList.remove('side-open');   /* close the drawer on navigation */
    if(force && active) snap(active);                // on navigation, snap; on first load let IO animate the hub
    window.scrollTo(0,0);
  }
  addEventListener('hashchange', function(){ route(true); });
  route(false);
})();

/* ---------------- mobile sidebar drawer (multipage + portable) ---------------- */
(function(){
  var toggle = document.querySelector('[data-side-toggle]');
  if(!toggle) return;
  var scrim = document.querySelector('[data-scrim]');
  function set(open){
    document.body.classList.toggle('side-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  toggle.addEventListener('click', function(){ set(!document.body.classList.contains('side-open')); });
  if(scrim) scrim.addEventListener('click', function(){ set(false); });
  addEventListener('keydown', function(e){ if(e.key==='Escape') set(false); });
  document.querySelectorAll('.docs-side .side-link').forEach(function(a){
    a.addEventListener('click', function(){ set(false); });
  });
})();

/* ---------------- right "On this page" TOC + scroll-spy ---------------- */
/* Builds the TOC from the active content's <h2 id> headings. Works for both the
   multipage guides (active = .docs-main) and the portable router (active = the
   visible [data-route] panel); rebuilt on hashchange. TOC clicks scroll only —
   they never touch the hash, so the portable router's route is left intact. */
(function(){
  var tocEl = document.querySelector('[data-toc]');
  var layout = document.querySelector('.docs-layout');
  if(!tocEl || !layout) return;
  var spy = null;
  function activeRoot(){
    return document.querySelector('[data-route]:not([hidden])') || document.querySelector('.docs-main');
  }
  function build(){
    if(spy){ spy.disconnect(); spy = null; }
    var root = activeRoot();
    var heads = root ? root.querySelectorAll('h2[id]') : [];
    tocEl.innerHTML = '';
    if(!heads.length){ layout.classList.remove('has-toc'); return; }
    var label = document.createElement('div');
    label.className = 'toc-h';
    label.innerHTML = '<span class="en">On this page</span><span class="vi">Trên trang này</span>';
    tocEl.appendChild(label);
    var links = [];
    heads.forEach(function(h){
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.innerHTML = h.innerHTML;            /* keeps the en/vi spans so lang toggle works */
      a.addEventListener('click', function(e){
        e.preventDefault();
        h.scrollIntoView({behavior: REDUCED ? 'auto' : 'smooth', block: 'start'});
        h.setAttribute('tabindex', '-1');     /* let the heading take focus so SR/keyboard users land there */
        h.focus({preventScroll: true});
        document.body.classList.remove('side-open');
      });
      tocEl.appendChild(a);
      links.push({id:h.id, a:a});
    });
    layout.classList.add('has-toc');
    spy = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(!e.isIntersecting) return;
        links.forEach(function(l){
          var on = l.id === e.target.id;
          l.a.classList.toggle('active', on);
          if(on){ l.a.setAttribute('aria-current', 'true'); } else { l.a.removeAttribute('aria-current'); }
        });
      });
    }, {rootMargin:'0px 0px -70% 0px', threshold:0});
    heads.forEach(function(h){ spy.observe(h); });
  }
  build();
  addEventListener('hashchange', function(){ setTimeout(build, 0); });
})();

/* ---------------- critique: one-finding, many-levels stepper ---------------- */
(function(){
  var bar = document.getElementById('fbar'); if(!bar) return;
  var dataEl = document.getElementById('finding-data'); if(!dataEl) return;
  var data; try{ data = JSON.parse(dataEl.textContent); }catch(e){ return; }
  var levels = data.levels || []; if(!levels.length) return;
  var ev=document.getElementById('fev'), sp=document.getElementById('fsp'), lv=document.getElementById('flv'),
      body=document.getElementById('fbody'), ftext=document.getElementById('ftext'), flock=document.getElementById('flock');
  var unlocked=false, cur=0;
  function lang(){ return document.body.classList.contains('lang-vi') ? 'vi':'en'; }
  function L10n(vi,en){ return lang()==='vi'?vi:en; }
  function defIdx(){ for(var i=0;i<levels.length;i++) if(levels[i].n===3) return i; return 0; }
  function md(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                          .replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`([^`]+)`/g,'<code>$1</code>'); }
  levels.forEach(function(Lv,i){
    var b=document.createElement('button'); b.type='button'; b.textContent='L'+Lv.n; b.setAttribute('role','tab');
    if(Lv.danger) b.classList.add('dgr');
    b.addEventListener('click', function(){ cur=i; render(); });
    bar.appendChild(b);
  });
  function render(){
    var Lv=levels[cur], gated=Lv.danger && !unlocked;
    bar.querySelectorAll('button').forEach(function(b,i){
      b.classList.toggle('on', i===cur);
      b.classList.toggle('locked', levels[i].danger && !unlocked);
    });
    ev.textContent=data.evidence; sp.textContent=data.spec;
    lv.textContent='L'+Lv.n+' · '+(lang()==='vi'?Lv.alias_vi:Lv.alias_en);
    ftext.innerHTML=md(Lv.vi);
    body.classList.toggle('blur', gated);
    if(unlocked){
      flock.innerHTML='🔓 <span>'+L10n('Đã mở mức 7–9. ','Levels 7–9 unlocked. ')+'</span><a data-fl="hide">'+L10n('Ẩn lại','Hide again')+'</a>';
    } else {
      flock.innerHTML='🔒 <span>'+L10n('Mức 7–9 (chửi thề nhắm-công-việc) đang ẩn. ','Levels 7–9 (work-targeted profanity) hidden. ')+'</span><a data-fl="show">'+L10n('Hiện','Reveal')+'</a>';
    }
    var a=flock.querySelector('a');
    if(a) a.addEventListener('click', function(){ unlocked=(a.dataset.fl==='show'); if(!unlocked && levels[cur].danger) cur=defIdx(); render(); });
  }
  var rv=document.getElementById('dgate-reveal'); if(rv) rv.addEventListener('click', function(){ unlocked=true; render(); });
  ['btn-en','btn-vi'].forEach(function(id){ var b=document.getElementById(id); if(b) b.addEventListener('click', render); });
  cur=defIdx(); render();
})();

/* ---------------- telemetry: same lens, four formats ---------------- */
(function(){
  var tabs=document.getElementById('teltabs'); if(!tabs) return;
  var cmd=document.getElementById('telcmd');
  tabs.querySelectorAll('button').forEach(function(b){
    b.addEventListener('click', function(){
      var f=b.dataset.fmt;
      tabs.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on', x===b); });
      document.querySelectorAll('.fmt-pane').forEach(function(p){ p.classList.toggle('on', p.dataset.pane===f); });
      if(cmd) cmd.textContent=f;
    });
  });
})();
