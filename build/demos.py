"""Build the live demos in docs/examples/ from the pinned parts of the stack, using the toolkit's own commands.

    python3 build/demos.py        (needs git checkouts of jade-vn-engine, jade-edu, Jade-agent-ui-ux and jade-vault next to
                                   this one, or JADE_VN_ENGINE / JADE_EDU / JADE_UI / JADE_VAULT; and Node for jade-edu's validator)

Every demo loads the stack from the CDN at the commits pinned in compat.py, so what you see is what a page built with the
toolkit gets:

    docs/examples/chat/     Jade Agent UI/UX: the agent chat, tools and approvals, page surfaces, dashboards (a demo agent; no model)
    docs/examples/rpg/      jade-vn-engine: tile maps, battles, faux-3D tours, minigames, lighting  (built by `jade vn build --cdn`)
    docs/examples/vault/    jade-vn-engine: Jade's Vault, image maps, light levels, VHS, and Jade herself in Live2D
    docs/examples/course/   jade-edu: a course with a talking Jade, quizzes and labs (Python on MicroPython, a terminal, webxdc)
    docs/examples/jade/     Jade Vault's PNGtuber avatar on its own: moods, speech, blinking, nods

The games come from the engine's git history at the pinned commit (tracked files only). The Live2D model in the Vault demo is
Jade's own, from Jade Vault; Live2D's Cubism Core runtime is not ours to ship, so the game loads it from Live2D's site."""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from jade import compat  # noqa: E402
from jade.resources import edu, vn  # noqa: E402

OUT = ROOT / "docs" / "examples"
SIB = ROOT.parent


def repo(env: str, *names: str) -> Path:
    for p in [os.environ.get(env)] + [str(SIB / n) for n in names] + [str(SIB / "lucky-edgelord" / n) for n in names]:
        if p and Path(p).is_dir():
            return Path(p).resolve()
    raise SystemExit(f"set {env} to a checkout of {names[0]}")


VN = repo("JADE_VN_ENGINE", "jade-vn-engine", "vn-engine")
EDU = repo("JADE_EDU", "jade-edu")
UI = repo("JADE_UI", "jade-agent-ui-ux", "Jade-agent-ui-ux")
VAULT = repo("JADE_VAULT", "jade-vault")
FONT = "https://cdn.jsdelivr.net/npm/@fontsource"

# the frame every demo page shares: Jade's Vault look, a bar back to the docs
ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23040807'/%3E%3Crect x='5' y='5' width='6' height='6' fill='%231fe5a5'/%3E%3C/svg%3E"
BAR = """<link rel="icon" href="__ICON__"><style>
.jbar{position:fixed;left:0;right:0;top:0;z-index:2147483600;display:flex;align-items:center;gap:14px;padding:7px 14px;font:600 12px/1 'Rajdhani',system-ui,sans-serif;
letter-spacing:.2em;text-transform:uppercase;background:rgb(4 8 7/.92);border-bottom:1px solid #1a2d27;color:#83998f;backdrop-filter:blur(6px)}
.jbar b{color:#1fe5a5;display:flex;align-items:center;gap:8px}.jbar b::before{content:"";width:7px;height:7px;background:#1fe5a5;box-shadow:0 0 8px #1fe5a5}
.jbar a{color:#e3f2ed;text-decoration:none}.jbar a:hover{color:#1fe5a5}.jbar .sp{flex:1}.jbar .t{color:#ffb8c6;font-family:'JetBrains Mono',monospace;letter-spacing:.1em;text-transform:none;font-weight:400}
@media (max-width:640px){.jbar .t{display:none}}
</style>
<div class="jbar"><b>Jade Agent Stack</b><span class="t">{tag}</span><span class="sp"></span><a href="../">All demos</a><a href="../../">Docs</a></div>"""


def bar(tag: str) -> str:
    return BAR.replace("{tag}", tag).replace("__ICON__", ICON)


def page(title: str, tag: str, body: str, head: str = "", pad: bool = True) -> str:
    fonts = "".join(f"@font-face{{font-family:'{f}';font-weight:{w};font-display:swap;src:url({FONT}/{p}@5/files/{p}-latin-{w}-normal.woff2) format('woff2')}}"
                    for f, p, ws in (("Rajdhani", "rajdhani", (600, 700)), ("JetBrains Mono", "jetbrains-mono", (400,))) for w in ws)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Jade Agent Stack live demo</title><meta name="description" content="{title}: a live demo of Jade Agent Stack">
<style>{fonts}html,body{{margin:0;background:#040807;color:#e3f2ed}}{'body{padding-top:30px;box-sizing:border-box}' if pad else ''}</style>
{head}</head><body>
{bar(tag)}
{body}
</body></html>
"""


def git_export(src: Path, ref: str, path: str, dest: Path) -> Path:
    """tracked files of `path` at `ref` → dest (nothing git-ignored, such as Live2D's files, comes along)"""
    dest.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(["git", "-C", str(src), "archive", ref, path], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar, check=True)
    return dest / path


def game(name: str, slug: str, tag: str, patch=None) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="jade-demo-"))
    g = git_export(VN, compat.REFS["vn"], f"games/{name}", tmp)
    if patch:
        patch(g)
    r = vn.build(str(g), out=str(tmp / "build"), cdn=True, engine=str(VN))
    dest = OUT / slug
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(tmp / "build", dest)
    # the engine's page, with the bar back to the docs on top
    idx = dest / "index.html"
    html = idx.read_text()
    assert '<canvas id="screen"' in html and "height:100vh" in html, "the engine's page changed"
    html = html.replace('<canvas id="screen"', bar(tag) + '\n<canvas id="screen"', 1)
    html = html.replace("height:100vh", "height:calc(100vh - 30px);margin-top:30px", 1)
    idx.write_text(html)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"demo": slug, "files": sum(1 for _ in dest.rglob("*") if _.is_file()), "engine": r["engine"]}


def chat() -> dict:
    src = (UI / "examples" / "index.html").read_text()
    html = src.replace("'../dist/jade-ui.js'", json.dumps(compat.CDN["ui"]).replace('"', "'")).replace('"../dist/jade-ui.js"', json.dumps(compat.CDN["ui"]))
    html = html.replace("https://cdn.jsdelivr.net/gh/lucky-edgelord/Jade-agent-kit@v3.0.0/dist/jade-agent-kit.js", compat.CDN["kit"])
    assert "../dist/" not in html, "the chat demo still points at a local dist/"
    assert "setTheme({ backdrop: true })" in html
    html = html.replace("setTheme({ backdrop: true })", "setTheme({ backdrop: true, mode: 'dark' })", 1)
    html = html.replace("<body>", "<body>\n" + bar("Jade Agent UI/UX · chat, tools, approvals, surfaces"), 1)
    html = html.replace("</head>", "<style>body{padding-top:30px}</style>\n</head>", 1)
    d = OUT / "chat"; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html)
    return {"demo": "chat", "ui": compat.CDN["ui"]}


def course() -> dict:
    d = OUT / "course"; d.mkdir(parents=True, exist_ok=True)
    c = json.loads((EDU / "examples" / "stack-101.course.json").read_text())
    (d / "course.json").write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n")
    v = edu.validate(str(d / "course.json"), edu=str(EDU))
    if not v.get("ok"):
        raise SystemExit(f"course: {v}")
    body = f"""<script type="module" src="{compat.CDN['edu']}"></script>
<style>jade-course{{display:block;height:calc(100vh - 30px)}}</style>
<jade-course src="course.json"></jade-course>"""
    (d / "index.html").write_text(page("Jade Agent Stack 101, a jade-edu course", "jade-edu · a course with Jade as the teacher", body))
    return {"demo": "course", "chapters": v.get("chapters"), "labs": v.get("labs")}


PNG_PAGE = """<style>
.stage{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:0;height:calc(100vh - 30px)}
.av{position:relative;overflow:hidden;background:radial-gradient(800px 500px at 50% 20%,rgb(31 229 165/.12),transparent 60%),
 linear-gradient(transparent 0 calc(100% - 1px),rgb(31 229 165/.05) 0) 0 0/100% 32px,linear-gradient(90deg,transparent 0 calc(100% - 1px),rgb(31 229 165/.05) 0) 0 0/32px 100%}
.av::after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgb(0 0 0/.18) 0 1px,transparent 1px 3px);mix-blend-mode:multiply;z-index:3}
.hud{position:absolute;left:16px;top:14px;z-index:4;display:flex;gap:8px;font:600 12px 'Rajdhani',sans-serif;letter-spacing:.2em;text-transform:uppercase}
.hud span{border:1px solid #1d6b52;padding:4px 8px;color:#1fe5a5}.hud .m{color:#ffb8c6;border-color:#6b2d3c}
.side{border-left:1px solid #1a2d27;padding:18px;overflow:auto;font:14px/1.5 system-ui,sans-serif;color:#c2d6ce}
.side h1{font:700 26px/1 'Rajdhani',sans-serif;letter-spacing:.06em;text-transform:uppercase;margin:4px 0 6px;color:#e3f2ed;text-shadow:-2px 0 rgb(255 61 79/.45),2px 0 rgb(31 229 165/.45)}
.side h2{font:400 11px 'JetBrains Mono',monospace;letter-spacing:.3em;color:#ffb8c6;text-transform:uppercase;margin:18px 0 8px}
.side p{margin:0 0 10px;color:#83998f}.btns{display:flex;flex-wrap:wrap;gap:6px}
button{font:600 12px 'Rajdhani',sans-serif;letter-spacing:.14em;text-transform:uppercase;padding:8px 11px;background:#09100e;color:#e3f2ed;border:1px solid #1a2d27;cursor:pointer;
 clip-path:polygon(0 0,100% 0,100% calc(100% - 7px),calc(100% - 7px) 100%,0 100%)}button:hover{border-color:#1fe5a5;color:#1fe5a5}button.on{background:#1fe5a5;color:#00140c;border-color:#1fe5a5}
textarea{width:100%;box-sizing:border-box;height:86px;background:#060c0a;color:#e3f2ed;border:1px solid #1a2d27;font:13px 'JetBrains Mono',monospace;padding:8px;resize:vertical}
code{font-family:'JetBrains Mono',monospace;color:#b8ffdf}
@media (max-width:760px){.stage{grid-template-columns:1fr;grid-template-rows:55vh auto;height:auto}.av{height:55vh}.side{border-left:0;border-top:1px solid #1a2d27}}
</style>
__ASSETS__
<div class="stage"><div class="av" id="host"><div class="hud"><span>Jade</span><span class="m" id="lbl">online</span></div></div>
<div class="side">
<h2>// Jade Vault 2.29</h2><h1>Jade, the PNGtuber</h1>
<p>Jade Vault's default avatar: one body picture and five expressions of four frames, drawn on a 2D canvas. No WebGL, about 240 kB. Move your pointer and she leans toward it.</p>
<h2>Mood</h2><div class="btns" id="moods"></div>
<h2>Talk</h2><textarea id="say">Hi, I'm Jade. I live in your vault, I run your tools, and now I'm a PNGtuber.</textarea>
<div class="btns" style="margin-top:6px"><button id="speak">Speak</button><button id="flap">Lip-flap only</button><button id="nod">Nod</button></div>
<h2>Framing</h2><div class="btns"><button data-f="portrait" class="on">Portrait</button><button data-f="full">Full</button><button data-f="strip">Strip</button></div>
<p style="margin-top:16px">In the app: <code>Jade.setMood('happy')</code>, <code>Jade.speak(text)</code>, <code>Jade.nod()</code>. Config → App → Avatar switches to Live2D.
<a href="https://github.com/lucky-edgelord/jade-vault/blob/main/docs/pngtuber.md" style="color:#1fe5a5">How it works</a></p>
</div></div>
<script>
(async () => {
const MOODS = { idle:{gaze:null,label:'online'}, listening:{gaze:[-0.75,-0.35],label:'listening'}, thinking:{gaze:[0.55,0.65],label:'thinking'},
  writing:{gaze:[-0.7,-0.15],label:'writing'}, working:{gaze:[0.05,-0.85],label:'jacked in'}, happy:{gaze:[0,0.1],label:'done'}, error:{gaze:[0,-0.1],label:'error'} };
const state = { mood:'idle', moodUntil:0, moodNext:'idle', blink:{t:-1,next:0}, pointer:{x:0,y:0,t:0}, nodT:-1, frame:'portrait', speaking:false, bump:0 };
const api = {}; const S = { jadeAvatar: 'png' };
__RENDERER__
await initPng({ host: document.getElementById('host') });
const host = document.getElementById('host'), lbl = document.getElementById('lbl');
const setMood = (m) => { state.mood = m; state.moodUntil = 0; lbl.textContent = MOODS[m].label; document.querySelectorAll('#moods button').forEach(b => b.classList.toggle('on', b.dataset.m === m)); };
for (const m of Object.keys(MOODS)) { const b = document.createElement('button'); b.textContent = m; b.dataset.m = m; b.onclick = () => setMood(m); document.getElementById('moods').append(b); }
setMood('idle');
const flap = (ms) => { state.speaking = true; clearTimeout(flap.t); flap.t = setTimeout(() => { state.speaking = false; }, ms); };
document.getElementById('flap').onclick = () => flap(2600);
document.getElementById('nod').onclick = () => { state.nodT = performance.now(); };
document.getElementById('speak').onclick = () => {
  const t = document.getElementById('say').value.trim(); if (!t) return;
  if (!('speechSynthesis' in window)) return flap(t.length * 60);
  speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.pitch = 1.25; u.rate = 1.05;
  const v = speechSynthesis.getVoices().find(v => /en-GB/.test(v.lang) && /female|Libby|Sonia|Serena|Kate/i.test(v.name)) || speechSynthesis.getVoices().find(v => /^en/.test(v.lang)); if (v) u.voice = v;
  u.onstart = () => { state.speaking = true; }; u.onend = u.onerror = () => { state.speaking = false; };
  u.onboundary = () => { state.bump = 1; };
  setMood('happy'); speechSynthesis.speak(u);
  setTimeout(() => { if (!speechSynthesis.speaking) flap(t.length * 55); }, 700);   // no voices here: flap anyway
};
for (const b of document.querySelectorAll('[data-f]')) b.onclick = () => {
  document.querySelectorAll('[data-f]').forEach(x => x.classList.toggle('on', x === b));
  const f = b.dataset.f; state.frame = f === 'strip' ? 'portrait' : f; host.style.height = f === 'strip' ? '120px' : ''; state.app.resize();
};
window.JadeDemo = { state, setMood };
})();
</script>"""


def jade() -> dict:
    a = VAULT / "app" / "avatar" / "pngtuber"
    meta = (a / "faces.json").read_text()
    uri = lambda f: "data:image/webp;base64," + base64.b64encode((a / f).read_bytes()).decode()
    assets = (f'<script type="application/json" id="png-meta">{meta}</script>\n'
              f'<script type="text/plain" id="png-body">{uri("body.webp")}</script>\n<script type="text/plain" id="png-faces">{uri("faces.webp")}</script>')
    renderer = (VAULT / "app" / "modules" / "pngtuber.js").read_text()
    body = PNG_PAGE.replace("__ASSETS__", assets).replace("__RENDERER__", renderer)
    d = OUT / "jade"; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(page("Jade, the PNGtuber", "jade-vault · the PNGtuber avatar", body))
    return {"demo": "jade", "bytes": (d / "index.html").stat().st_size}


if __name__ == "__main__":
    todo = sys.argv[1:] or ["chat", "course", "jade", "rpg", "vault"]
    for t in todo:
        if t == "chat": print(chat())
        elif t == "course": print(course())
        elif t == "jade": print(jade())
        elif t == "rpg": print(game("rpg-demo", "rpg", "jade-vn-engine · tile maps, battles, tours, minigames"))
        elif t == "vault": print(game("jade-vault", "vault", "jade-vn-engine · Jade's Vault, lights, VHS, Jade in Live2D"))
