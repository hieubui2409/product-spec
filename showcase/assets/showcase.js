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

/* ---------------- voice level dial ---------------- */
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

/* ---------------- hero constellation network ---------------- */
(function(){
  var c = document.getElementById('net'); if(!c) return;
  var x = c.getContext('2d'), W,H,pts,raf;
  var COLORS = ['#38bdf8','#fb5e7e','#34d399','#a78bfa'];
  function size(){ W=c.width=innerWidth; H=c.height=Math.max(innerHeight, 700); init(); }
  function init(){
    var n = Math.min(64, Math.floor(W/26));
    pts = [];
    for(var i=0;i<n;i++){
      pts.push({x:Math.random()*W, y:Math.random()*H, vx:(Math.random()-.5)*.28, vy:(Math.random()-.5)*.28, c:COLORS[i%4]});
    }
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
  // pause when tab hidden
  document.addEventListener('visibilitychange', function(){ if(document.hidden){cancelAnimationFrame(raf);} else {draw();} });
})();

/* ---------------- single-file hash router ---------------- */
/* Active ONLY in the portable dist build (where every page is one [data-route] panel).
   In the multipage build there are no [data-route] wrappers, so this no-ops and the
   server-baked .active nav class is left untouched. */
(function(){
  var panels = document.querySelectorAll('[data-route]');
  if(!panels.length) return;                       // multipage → real page links, nothing to route
  var navlinks = document.querySelectorAll('nav [data-nav]');
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
    if(force && active) snap(active);                // on navigation, snap; on first load let IO animate the hub
    window.scrollTo(0,0);
  }
  addEventListener('hashchange', function(){ route(true); });
  route(false);
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
