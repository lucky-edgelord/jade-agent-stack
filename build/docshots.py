"""Regenerate docs/img: real command output (rendered as terminal screenshots) and the pages those commands build.
usage: JADE_VN_ENGINE=../vn-engine JADE_EDU=../jade-edu python3 build/docshots.py    (needs Playwright with Chrome)"""
import functools, html, http.server, os, pathlib, shutil, socketserver, subprocess, sys, tempfile, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "img"; OUT.mkdir(parents=True, exist_ok=True)
VN = pathlib.Path(os.environ.get("JADE_VN_ENGINE", ROOT.parent / "vn-engine")).resolve()
EDU = pathlib.Path(os.environ.get("JADE_EDU", ROOT.parent / "jade-edu")).resolve()
env = dict(os.environ, JADE_VN_ENGINE=str(VN), JADE_EDU=str(EDU), NO_COLOR="1")
work = pathlib.Path(tempfile.mkdtemp(prefix="jadedocs-"))

def run(cmd):
    r = subprocess.run(cmd, shell=True, cwd=work, env=env, capture_output=True, text=True)
    out = f"$ {cmd}\n{r.stdout}{r.stderr}".rstrip() + "\n"
    return out.replace(str(work) + "/", "").replace(str(pathlib.Path.home()), "~")   # keep the machine's paths out of the pictures

TERM = """<!doctype html><meta charset=utf-8><style>
body{margin:0;background:#040807;padding:18px;font:14px/1.45 'JetBrains Mono',ui-monospace,monospace;color:#c2d6ce}
.w{border:1px solid #14382d;border-left:3px solid #1fe5a5;padding:14px 18px;white-space:pre-wrap;word-break:break-all;width:820px}
.c{color:#1fe5a5}.t{color:#6f8f84;font-size:11px;letter-spacing:.2em;margin-bottom:8px}</style>
<div class=w><div class=t>JADE//TERMINAL</div>%s</div>"""
def term(pg, name, *cmds):
    text = "".join(run(c) + "\n" for c in cmds).rstrip() + "\n"
    body = "".join(f'<span class=c>{html.escape(l)}</span>\n' if l.startswith("$ ") else html.escape(l) + "\n" for l in text.splitlines())
    pg.set_viewport_size({"width": 880, "height": 400}); pg.set_content(TERM % body)
    h = pg.evaluate("document.body.scrollHeight"); pg.set_viewport_size({"width": 880, "height": h})
    pg.screenshot(path=str(OUT / f"{name}.png")); print("png", name)

def serve(mounts):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def translate_path(self, path):
            path = path.split("?")[0]
            for pre, d in mounts.items():
                if path.startswith(pre): return str(pathlib.Path(d) / path[len(pre):])
            return super().translate_path(path)
        extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm"})
    s = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_address[1]}"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page()
    term(pg, "term-vn", "jade vn new mygame --libs rpg,minigames", "jade vn check mygame", "jade vn build mygame")
    term(pg, "term-edu", "jade edu new course.json --title 'Intro to Jade'", "jade edu validate course.json", "jade edu page course.json page.html")
    # the game those commands built, running
    srv, base = serve({"/": work})
    g = b.new_page(viewport={"width": 1280, "height": 720}); errs = []
    g.on("pageerror", lambda e: errs.append(str(e)))
    g.goto(base + "/mygame/build/index.html"); g.wait_for_function("window.VN && (VN.state || VN.error)", timeout=60000)
    g.wait_for_timeout(700); g.screenshot(path=str(OUT / "game-start.png"))
    g.mouse.click(640, 362); g.wait_for_timeout(1200); g.screenshot(path=str(OUT / "game-say.png"))
    g.keyboard.press("Enter"); g.wait_for_timeout(1200); g.screenshot(path=str(OUT / "game-menu.png"))
    print("game errors", errs[:3]); g.close()
    # the course page, with the module taken from the local jade-edu instead of the CDN
    page = (work / "page.html").read_text()
    import re
    (work / "page.html").write_text(re.sub(r'https://cdn\.jsdelivr\.net/gh/lucky-edgelord/jade-edu@[^/]+/src/edu\.js', "/edu/src/edu.js", page))
    srv2, base2 = serve({"/edu/": EDU, "/": work})
    c = b.new_page(viewport={"width": 1280, "height": 760})
    c.goto(base2 + "/page.html"); c.wait_for_function("document.querySelector('jade-course')?.shadowRoot?.querySelector('header')", timeout=30000)
    c.wait_for_timeout(1200); c.screenshot(path=str(OUT / "course-page.png"))
    b.close()
for f in OUT.glob("*.png"):
    subprocess.run(["convert", str(f), "-resize", "1100x", "-quality", "84", str(f.with_suffix(".webp"))], check=True); f.unlink()
shutil.rmtree(work, ignore_errors=True)
