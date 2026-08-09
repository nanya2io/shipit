import json

with open("dashboard_data.json", encoding="utf-8") as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA).replace("</script", "<\\/script").replace("<!--", "<\\!--")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SHIPIT.EXE</title>
<link href="https://fonts.googleapis.com/css2?family=Bungee&family=VT323&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{
  --hotpink:#FF2E9A;
  --cyan:#00E5FF;
  --lime:#C6FF00;
  --purple:#7B2FF7;
  --deep:#2B0059;
  --paper:#FFF7E4;
  --ink:#241938;
  --chrome-lt:#F1F0F6;
  --chrome-dk:#B9B7C9;
}
*{box-sizing:border-box;}
body{
  margin:0; min-height:100vh;
  background:
    radial-gradient(circle at 20% 20%, rgba(123,47,247,0.35), transparent 45%),
    radial-gradient(circle at 85% 75%, rgba(255,46,154,0.30), transparent 45%),
    #0A0014;
  font-family:'Space Mono', monospace;
  color: var(--ink);
  padding: 28px 14px 60px;
  position:relative;
  overflow-x:hidden;
}
/* starfield */
body::before{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    radial-gradient(2px 2px at 10% 15%, #fff, transparent),
    radial-gradient(2px 2px at 80% 10%, #fff, transparent),
    radial-gradient(1.5px 1.5px at 40% 60%, #fff, transparent),
    radial-gradient(2px 2px at 60% 85%, #fff, transparent),
    radial-gradient(1.5px 1.5px at 92% 40%, #fff, transparent),
    radial-gradient(1.5px 1.5px at 25% 90%, #fff, transparent),
    radial-gradient(2px 2px at 55% 25%, #fff, transparent);
  opacity:0.5;
}
/* scanlines */
body::after{
  content:''; position:fixed; inset:0; pointer-events:none; z-index:200;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,0.08) 0px, rgba(0,0,0,0.08) 1px, transparent 1px, transparent 3px);
  mix-blend-mode: multiply;
}
.window{
  max-width: 900px; margin: 0 auto;
  background: var(--chrome-lt);
  border: 3px solid #000;
  border-radius: 10px 10px 4px 4px;
  box-shadow: 8px 8px 0 rgba(0,0,0,0.55), 0 0 60px rgba(255,46,154,0.25);
  position:relative; z-index:1;
}
.titlebar{
  background: linear-gradient(90deg, var(--hotpink), var(--purple) 70%);
  border-radius: 7px 7px 0 0;
  padding: 8px 10px;
  display:flex; align-items:center; justify-content:space-between;
  border-bottom: 3px solid #000;
}
.titlebar .name{
  font-family:'VT323', monospace; color:#fff; font-size:1.25rem; letter-spacing:1px;
  display:flex; align-items:center; gap:8px;
  text-shadow: 1px 1px 0 rgba(0,0,0,0.4);
}
.titlebar .name .icon{
  width:18px; height:18px; background: var(--lime); border:2px solid #000; display:inline-block;
}
.win-btns{ display:flex; gap:6px; }
.win-btns span{
  width:20px; height:20px; background:var(--chrome-lt); border:2px solid #000;
  display:flex; align-items:center; justify-content:center; font-family:'VT323',monospace;
  font-size:0.9rem; font-weight:bold; box-shadow: 1px 1px 0 #000;
}
.menubar{
  background: var(--chrome-lt); border-bottom:2px solid #000;
  padding:5px 12px; display:flex; gap:18px;
  font-family:'VT323', monospace; font-size:1.05rem; color:#333;
}
.marquee-strip{
  background:#000; color: var(--lime); overflow:hidden; white-space:nowrap;
  border-bottom:2px solid #000; padding:4px 0;
  font-family:'VT323',monospace; font-size:1.1rem; letter-spacing:1px;
}
.marquee-strip span{ display:inline-block; padding-left:100%; animation: marquee 18s linear infinite; }
@keyframes marquee{ to{ transform: translateX(-100%); } }

.content{ padding: 22px 24px 10px; background:
  repeating-linear-gradient(180deg, var(--paper) 0px, var(--paper) 27px, #F3E9CE 28px);
}
.hero{ text-align:center; padding: 10px 0 22px; }
.hero h1{
  font-family:'Bungee', cursive; font-size: clamp(1.7rem, 6vw, 2.6rem);
  color: var(--hotpink); margin:0 0 6px;
  -webkit-text-stroke: 1.5px #000;
  text-shadow: 3px 3px 0 var(--cyan), 6px 6px 0 #000;
  letter-spacing:1px;
}
.hero p{ font-size:0.85rem; color:#4a3f66; max-width:520px; margin:0 auto; line-height:1.5; }
.badge-row{ display:flex; justify-content:center; gap:10px; margin-top:14px; flex-wrap:wrap; }
.pixel-badge{
  font-family:'VT323',monospace; font-size:0.95rem; background:var(--cyan);
  border:2px solid #000; padding:3px 10px; box-shadow:2px 2px 0 #000;
}

.dialog{
  background: var(--chrome-lt); border:2px solid #000; box-shadow: 4px 4px 0 #000;
  padding:16px; margin: 0 0 22px;
}
.dialog h2{
  font-family:'VT323',monospace; font-size:1.3rem; margin:0 0 12px; color:#000;
  background: var(--lime); display:inline-block; padding:2px 10px; border:2px solid #000;
}
.field-row{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px; }
.field{ flex:1; min-width:180px; }
.field label{ font-family:'VT323',monospace; font-size:1rem; display:block; margin-bottom:3px; }
.field input{
  width:100%; font-family:'Space Mono',monospace; font-size:0.95rem;
  padding:8px 10px; border:2px inset #888; background:#fff;
}
.compile-btn{
  font-family:'VT323',monospace; font-size:1.2rem; letter-spacing:1px;
  background: linear-gradient(180deg, #fff, var(--chrome-dk));
  border: 2px outset #ddd; padding:9px 22px; cursor:pointer;
  box-shadow: 3px 3px 0 #000; color:#000;
}
.compile-btn:active{ border-style: inset; transform: translate(2px,2px); box-shadow:1px 1px 0 #000; }
.dialog .hint{ font-size:0.72rem; color:#665; margin-top:8px; }

.chapter-nav{ display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.disk-tab{
  font-family:'VT323',monospace; font-size:1rem; background:var(--chrome-lt);
  border:2px solid #000; padding:6px 12px; cursor:pointer; display:flex; align-items:center; gap:6px;
  box-shadow:2px 2px 0 #000;
}
.disk-tab.locked{ opacity:0.4; cursor:not-allowed; }
.disk-tab.active{ background:var(--hotpink); color:#fff; }
.disk-tab .floppy{ width:12px; height:12px; background:#333; border:1px solid #000; }

.diary-card{
  position:relative; background: #fffdf7; border:2px solid #000;
  box-shadow: 5px 5px 0 rgba(0,0,0,0.3); padding: 26px 22px 20px; margin-bottom:18px;
  background-image: repeating-linear-gradient(180deg, transparent 0, transparent 26px, rgba(120,140,200,0.18) 27px);
}
.diary-card::before{
  content:'📌'; position:absolute; top:-14px; left:20px; font-size:1.4rem;
  transform: rotate(-12deg);
}
.diary-card h3{
  font-family:'Bungee', cursive; color:var(--purple); font-size:1.15rem; margin:0 0 4px;
}
.diary-card .role-tag{
  font-family:'VT323',monospace; font-size:0.85rem; color:#888; margin-bottom:12px; display:block;
}
.diary-card p{ font-size:0.92rem; line-height:1.75; margin:0; white-space:pre-wrap; }
.diary-card.brainrot p{ font-family:'Space Mono',monospace; font-weight:700; color:#1a0033; }

.mode-toggle{
  display:flex; align-items:center; gap:10px; margin: 4px 0 16px; font-family:'VT323',monospace; font-size:1.05rem;
}
.switch{
  width:64px; height:30px; background:#333; border:2px solid #000; border-radius:20px;
  position:relative; cursor:pointer; flex-shrink:0;
}
.switch .knob{
  position:absolute; top:2px; left:2px; width:22px; height:22px; border-radius:50%;
  background: linear-gradient(180deg,#fff,#ccc); border:2px solid #000; transition: left .2s;
}
.switch.on{ background: var(--hotpink); }
.switch.on .knob{ left:36px; background: linear-gradient(180deg,#fff,var(--lime)); }
.glitch{ animation: glitchAnim 0.35s steps(2); }
@keyframes glitchAnim{
  0%{ filter:none; transform:translate(0);}
  30%{ filter: hue-rotate(90deg); transform: translate(-2px,1px);}
  60%{ filter: hue-rotate(-90deg); transform: translate(2px,-1px);}
  100%{ filter:none; transform:translate(0);}
}

.next-btn{
  font-family:'VT323',monospace; font-size:1.2rem; background: var(--lime);
  border:2px solid #000; padding:8px 18px; cursor:pointer; box-shadow:3px 3px 0 #000;
  display:block; margin: 0 auto 24px;
}
.next-btn:active{ transform:translate(2px,2px); box-shadow:1px 1px 0 #000; }

.meter-box{
  background:var(--chrome-lt); border:2px solid #000; padding:12px 14px; margin-bottom:18px;
  box-shadow: 3px 3px 0 #000;
}
.meter-box .label{ font-family:'VT323',monospace; font-size:1.05rem; margin-bottom:6px; }
.heart-track{ display:flex; gap:4px; }
.heart-track span{ font-size:1.3rem; filter: grayscale(1) opacity(0.35); transition:.3s; }
.heart-track span.filled{ filter:none; }

.trope-badges{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }
.trope-sticker{
  font-family:'VT323',monospace; font-size:0.95rem; background:#fff;
  border:2px solid #000; padding:6px 12px; box-shadow:2px 2px 0 #000;
  transform: rotate(var(--r, -2deg)); position:relative; cursor:default;
}
.trope-sticker:nth-child(2n){ --r:2deg; background:var(--cyan); }
.trope-sticker:nth-child(3n){ --r:-1deg; background:var(--lime); }
.trope-sticker .score{ font-size:0.75rem; color:#555; }
.evidence-box{
  font-family:'Space Mono',monospace; font-size:0.75rem; color:#333; background:#fffce0;
  border:1px dashed #999; padding:6px 8px; margin-top:6px; display:none;
}
.trope-sticker:hover .evidence-box{ display:block; }

.structural-panel{
  background:#111; color:var(--lime); border:2px solid #000; padding:14px; margin-bottom:20px;
  font-family:'VT323',monospace; box-shadow:3px 3px 0 #000;
}
.structural-panel h2{ color:var(--cyan); background:none; border:none; padding:0; margin-bottom:10px; }
.structural-row{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:4px 14px; padding:6px 0; border-bottom:1px dotted #444; font-size:1rem;}
.structural-row .role-label{ color:var(--cyan); font-weight:bold; flex-shrink:0; }
.structural-row .trope-list{ text-align:right; flex:1; min-width:180px; }

.attention-panel{
  background:#0a0a0a; color:var(--cyan); border:2px solid #000; padding:14px; margin-bottom:20px;
  font-family:'VT323',monospace; box-shadow:3px 3px 0 #000;
}
.attention-panel h2{ color:var(--lime); margin-bottom:6px; }
.attention-panel .subnote{ color:#888; font-size:0.85rem; margin-bottom:12px; line-height:1.4; }
.attention-sentence{ font-size:1.2rem; line-height:2.4; margin-bottom:6px; }
.attn-token{
  display:inline-block; padding:2px 4px; margin:1px; border-radius:2px;
  font-family:'Space Mono',monospace; font-size:0.95rem; color:#fff;
}
.attn-legend{ display:flex; align-items:center; gap:8px; font-size:0.85rem; color:#888; margin-top:8px; }
.attn-legend .swatch{ width:60px; height:10px; background:linear-gradient(90deg, rgba(0,229,255,0.08), var(--cyan)); border:1px solid #444; }

footer.window-footer{
  border-top:2px solid #000; background:var(--chrome-lt); padding:14px 20px;
  display:flex; flex-wrap:wrap; justify-content:space-between; gap:14px; align-items:center;
  font-family:'VT323',monospace; font-size:0.95rem;
}
.counter{
  background:#000; color:var(--lime); padding:4px 8px; border:2px inset #333; letter-spacing:2px;
}
.webring{ display:flex; gap:10px; align-items:center; }
.webring a{ color:var(--purple); text-decoration:none; border-bottom:1px dashed var(--purple); }

@media(max-width:640px){
  .field-row{ flex-direction:column; }
}

/* boot sequence overlay */
#bootOverlay{
  position:fixed; inset:0; z-index:1000; background:#000;
  font-family:'VT323', monospace; color:#00FF66; font-size:1.3rem;
  padding: 60px 40px; line-height:1.9;
  display:flex; flex-direction:column; justify-content:center;
  transition: opacity 0.6s ease, visibility 0.6s ease;
}
#bootOverlay.hidden{ opacity:0; visibility:hidden; pointer-events:none; }
#bootOverlay .boot-line{ opacity:0; white-space:pre; }
#bootOverlay .boot-line.show{ opacity:1; }
#bootOverlay .cursor-blink{ display:inline-block; width:10px; height:1.1em; background:#00FF66; margin-left:4px; animation: blink 0.8s steps(1) infinite; vertical-align:middle; }
@keyframes blink{ 50%{ opacity:0; } }

/* cursor sparkle trail */
.sparkle-trail{
  position:fixed; pointer-events:none; z-index:999;
  font-size: 14px; user-select:none;
  animation: sparkleFade 0.7s ease-out forwards;
}
@keyframes sparkleFade{
  0%{ opacity:1; transform: translateY(0) scale(1) rotate(0deg); }
  100%{ opacity:0; transform: translateY(-22px) scale(0.4) rotate(90deg); }
}
</style>
</head>
<body>

<div id="bootOverlay">
  <div class="boot-line" id="bl1">C:\&gt; LOADING SHIPIT.EXE...</div>
  <div class="boot-line" id="bl2">C:\&gt; INITIALIZING CROSSOVER DYNAMIC ENGINE...</div>
  <div class="boot-line" id="bl3">C:\&gt; LOADING TROPE TAXONOMY.JSON... OK (16 tropes)</div>
  <div class="boot-line" id="bl4">C:\&gt; CONNECTING TO VIBES.DLL... OK</div>
  <div class="boot-line" id="bl5">C:\&gt; READY.<span class="cursor-blink"></span></div>
</div>

<div class="window">
  <div class="titlebar">
    <div class="name"><span class="icon"></span> C:\SHIPIT.EXE</div>
    <div class="win-btns"><span>_</span><span>□</span><span>X</span></div>
  </div>
  <div class="menubar"><span>File</span><span>Edit</span><span>Ship</span><span>Chaos</span><span>Help</span></div>
  <div class="marquee-strip"><span>★ NOW LOADING: CROSSOVER DYNAMIC ENGINE ★ 100% REAL AI CHARACTER TEAM-UPS ★ NO CAP ★ BEST VIEWED AT 1024x768 ★ CLICK NEXT TO REVEAL CHAPTER ★</span></div>

  <div class="content">
    <div class="hero">
      <h1>SHIPIT.EXE</h1>
      <p>type in two (fictional!) characters from anywhere -- same universe, different universe, doesn't matter. watch the AI write their whole crossover team-up arc, chapter by chapter, then tell you exactly which character-dynamic tropes it just committed to canon. no romance, all found-family/rivalry/team-up energy.</p>
      <div class="badge-row">
        <span class="pixel-badge">chapter-by-chapter reveal</span>
        <span class="pixel-badge">explainable trope AI</span>
        <span class="pixel-badge">brainrot mode included</span>
      </div>
    </div>

    <div class="dialog">
      <h2>LOAD YOUR DUO</h2>
      <div class="field-row">
        <div class="field"><label>Character A</label><input id="charA" placeholder="e.g. Superman"></div>
        <div class="field"><label>Character B</label><input id="charB" placeholder="e.g. Spider-Man"></div>
      </div>
      <button class="compile-btn" onclick="loadDemo()">COMPILE STORY &gt;&gt;</button>
      <div class="hint" id="demoHint"></div>
    </div>

    <div class="chapter-nav" id="chapterNav"></div>

    <div id="chapterArea"></div>

    <button class="next-btn" id="nextBtn" onclick="revealNext()">NEXT CHAPTER &gt;&gt;</button>

    <div class="meter-box">
      <div class="label">🤝 BOND METER 🤝</div>
      <div class="heart-track" id="heartTrack"></div>
    </div>

    <div class="trope-badges" id="tropeBadges"></div>

    <div class="attention-panel" id="attentionPanel" style="display:none;">
      <h2>&gt; ATTENTION LENS</h2>
      <div class="subnote" id="attentionNote"></div>
      <div class="attention-sentence" id="attentionSentence"></div>
      <div class="attn-legend"><span class="swatch"></span> low → high self-attention weight</div>
    </div>

    <div class="structural-panel">
      <h2>&gt; STRUCTURAL TROPE MAP</h2>
      <div id="structuralRows"></div>
    </div>
  </div>

  <footer class="window-footer">
    <div class="counter" id="hitCounter">VISITORS: 004127</div>
    <div class="webring">
      <a href="#">&lt;&lt; PREV SHIP</a>
      <a href="#">RANDOM</a>
      <a href="#">NEXT SHIP &gt;&gt;</a>
    </div>
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;
let chaptersRevealed = 1;
let brainrotState = {};

function el(tag, cls, html){
  const e = document.createElement(tag);
  if(cls) e.className = cls;
  if(html !== undefined) e.innerHTML = html;
  return e;
}

async function loadDemo(){
  const charAInput = document.getElementById('charA');
  const charBInput = document.getElementById('charB');
  const charA = charAInput.value.trim();
  const charB = charBInput.value.trim();
  const btn = document.querySelector('.compile-btn');
  const hint = document.getElementById('demoHint');

  if(!charA || !charB){
    if(hint) hint.textContent = 'enter both character names first.';
    return;
  }

  const originalBtnText = btn.textContent;
  btn.textContent = 'COMPILING... (calls a real LLM, ~15-30s)';
  btn.disabled = true;
  if(hint) hint.textContent = `generating "${charA} × ${charB}" live via your local server...`;

  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({char_a: charA, char_b: charB})
    });
    const result = await resp.json();
    if(!resp.ok){
      throw new Error(result.error || 'Generation failed.');
    }
    DATA.story = result.story;
    DATA.structural_summary = result.structural_summary;
    DATA.taxonomy = result.taxonomy || DATA.taxonomy;
    DATA.meta = result.meta || DATA.meta;
    chaptersRevealed = 1;
    brainrotState = {};
    renderAll();
    if(hint){
      hint.textContent = `live-generated "${charA} × ${charB}". type a new pair and click again to regenerate.`;
    }
  } catch (err) {
    chaptersRevealed = 1;
    brainrotState = {};
    renderAll();
    if(hint){
      hint.textContent = `couldn't generate live (${err.message}). Make sure you started this with ` +
        `"python server.py" and opened http://localhost:5000 -- not by double-clicking dashboard.html. ` +
        `Showing the existing story instead.`;
    }
  } finally {
    btn.textContent = originalBtnText;
    btn.disabled = false;
  }
}

function renderNav(){
  const nav = document.getElementById('chapterNav');
  nav.innerHTML = '';
  DATA.story.chapters.forEach((ch, i) => {
    const tab = el('div', 'disk-tab' + (i+1 > chaptersRevealed ? ' locked' : '') + (i+1 === chaptersRevealed ? ' active' : ''),
      `<span class="floppy"></span> CH.${ch.chapter_number}`);
    if(i+1 <= chaptersRevealed){
      tab.onclick = () => { chaptersRevealed = i+1; renderAll(); };
    }
    nav.appendChild(tab);
  });
}

function renderChapters(){
  const area = document.getElementById('chapterArea');
  area.innerHTML = '';
  for(let i=0; i<chaptersRevealed; i++){
    const ch = DATA.story.chapters[i];
    const isBrainrot = !!brainrotState[ch.chapter_number];
    const card = el('div', 'diary-card' + (isBrainrot ? ' brainrot' : ''));
    card.innerHTML = `
      <h3>Ch.${ch.chapter_number} — ${ch.title}</h3>
      <span class="role-tag">structural role: ${ch.structural_role}</span>
      <div class="mode-toggle">
        <div class="switch ${isBrainrot ? 'on' : ''}" onclick="toggleBrainrot(${ch.chapter_number}, this)"><div class="knob"></div></div>
        <span>${isBrainrot ? '🌀 BRAINROT MODE' : '📖 LORE MODE'}</span>
      </div>
      <p id="text-${ch.chapter_number}">${isBrainrot ? ch.brainrot_text : ch.text}</p>
    `;
    area.appendChild(card);
  }
  document.getElementById('nextBtn').style.display =
    chaptersRevealed >= DATA.story.chapters.length ? 'none' : 'block';
}

function toggleBrainrot(chapterNum, switchEl){
  brainrotState[chapterNum] = !brainrotState[chapterNum];
  switchEl.classList.toggle('on');
  const card = switchEl.closest('.diary-card');
  card.classList.add('glitch');
  setTimeout(() => {
    renderChapters();
  }, 180);
}

function revealNext(){
  if(chaptersRevealed < DATA.story.chapters.length){
    chaptersRevealed++;
    renderAll();
  }
}

function renderMeter(){
  const track = document.getElementById('heartTrack');
  track.innerHTML = '';
  const totalHearts = 10;
  const filled = Math.round((chaptersRevealed / DATA.story.chapters.length) * totalHearts);
  for(let i=0; i<totalHearts; i++){
    track.appendChild(el('span', i < filled ? 'filled' : '', '⚡'));
  }
}

function renderBadges(){
  const box = document.getElementById('tropeBadges');
  box.innerHTML = '';
  const seen = new Set();
  for(let i=0; i<chaptersRevealed; i++){
    const ch = DATA.story.chapters[i];
    ch.detected_tropes.forEach(t => {
      if(seen.has(t.trope_id)) return;
      seen.add(t.trope_id);
      const sticker = el('div', 'trope-sticker');
      const evidence = t.evidence.map(e => e.sentence).join(' / ');
      sticker.innerHTML = `${t.trope_name} <span class="score">(${t.score})</span>
        <div class="evidence-box">"${evidence}"</div>`;
      box.appendChild(sticker);
    });
  }
  if(seen.size === 0){
    box.appendChild(el('div', 'trope-sticker', 'no strong matches yet — keep reading'));
  }
}

function renderStructural(){
  const rows = document.getElementById('structuralRows');
  rows.innerHTML = '';
  Object.entries(DATA.structural_summary).forEach(([role, tropes]) => {
    rows.appendChild(el('div', 'structural-row',
      `<span class="role-label">${role}</span><span class="trope-list">${tropes.length ? tropes.join(', ') : '—'}</span>`));
  });
}

function attnColor(weight){
  // low weight -> near-black, high weight -> bright cyan
  const intensity = Math.round(weight * 255);
  return `rgba(0, ${Math.round(150 + weight*105)}, ${Math.round(180+weight*75)}, ${0.15 + weight*0.75})`;
}

function renderAttention(){
  const panel = document.getElementById('attentionPanel');
  const currentChapter = DATA.story.chapters[chaptersRevealed - 1];
  const lens = currentChapter && currentChapter.attention_lens;
  if(!lens){ panel.style.display = 'none'; return; }
  panel.style.display = 'block';
  document.getElementById('attentionNote').textContent =
    "self-attention weights from GPT-2's final layer (averaged across heads) -- " +
    "brighter word = more weight the model placed on it when processing this sentence. " +
    (DATA.meta.attention_note || '');
  const sentEl = document.getElementById('attentionSentence');
  sentEl.innerHTML = lens.tokens.map(t =>
    `<span class="attn-token" style="background:${attnColor(t.attention)}">${t.token}</span>`
  ).join(' ');
}

function renderFormDefaults(){
  const charA = document.getElementById('charA');
  const charB = document.getElementById('charB');
  if(charA && !charA.value) charA.value = DATA.story.char_a;
  if(charB && !charB.value) charB.value = DATA.story.char_b;
  const hint = document.getElementById('demoHint');
  if(hint){
    hint.textContent = `demo runs on a pre-generated sample story (${DATA.story.char_a} × ${DATA.story.char_b}) ` +
      `classified with the real trope engine. hook up your own GROQ_API_KEY to generate live for any pair ` +
      `(run the Python pipeline, then rebuild -- typing names here doesn't call the API live).`;
  }
}

function renderAll(){
  renderFormDefaults();
  renderNav();
  renderChapters();
  renderMeter();
  renderBadges();
  renderStructural();
  renderAttention();
}

renderAll();

// boot sequence
const bootLines = ['bl1','bl2','bl3','bl4','bl5'];
bootLines.forEach((id, i) => {
  setTimeout(() => {
    const line = document.getElementById(id);
    if(line) line.classList.add('show');
  }, 220 * i);
});
setTimeout(() => {
  const overlay = document.getElementById('bootOverlay');
  if(overlay) overlay.classList.add('hidden');
}, 220 * bootLines.length + 500);

// cursor sparkle trail
const SPARKLE_CHARS = ['✦','★','✧','🩷','⋆'];
let lastSparkle = 0;
document.addEventListener('mousemove', (e) => {
  const now = Date.now();
  if(now - lastSparkle < 55) return;
  lastSparkle = now;
  const s = document.createElement('div');
  s.className = 'sparkle-trail';
  s.textContent = SPARKLE_CHARS[Math.floor(Math.random()*SPARKLE_CHARS.length)];
  s.style.left = (e.clientX + (Math.random()*10-5)) + 'px';
  s.style.top = (e.clientY + (Math.random()*10-5)) + 'px';
  s.style.color = ['#FF2E9A','#00E5FF','#C6FF00','#7B2FF7'][Math.floor(Math.random()*4)];
  document.body.appendChild(s);
  setTimeout(() => s.remove(), 700);
});
</script>
</body>
</html>
"""

html_out = HTML.replace("__DATA_JSON__", DATA_JSON)
with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_out)

print("Dashboard written:", len(html_out)/1024, "KB")
