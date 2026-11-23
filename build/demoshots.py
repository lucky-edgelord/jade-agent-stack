"""Open every live demo in headless Chrome (served from docs/), play a little, check for errors, and write the
thumbnails the examples page shows (docs/img/demo-*.webp).   python3 build/demoshots.py  (Playwright, Chrome, network for the CDN)"""
import functools, http.server, pathlib, socketserver, subprocess, sys, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS, IMG = ROOT / "docs", ROOT / "docs" / "img"
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS)); H.log_message = lambda *a: None
H.log_message = lambda *a: None
H.extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{".js": "text/javascript", ".wasm": "application/wasm"})
srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}/examples/"
fails = []


def shot(pg, name):
    p = IMG / f"demo-{name}.png"; pg.screenshot(path=str(p))
    subprocess.run(["convert", str(p), "-resize", "960x", "-quality", "82", str(p.with_suffix(".webp"))], check=True); p.unlink()


def check(name, cond, msg):
    print(("ok   " if cond else "FAIL ") + f"{name}: {msg}")
    if not cond: fails.append(f"{name}: {msg}")


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required",
                          "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])

    def open_(path, vp=(1280, 760)):
        pg = b.new_page(viewport={"width": vp[0], "height": vp[1]}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        pg.on("response", lambda r: errs.append(f"{r.status} {r.url}") if r.status >= 400 and not r.url.endswith("favicon.ico") else None)
        pg.goto(BASE + path); return pg, errs

    # chat
    pg, errs = open_("chat/")
    pg.wait_for_function("document.getElementById('chat').agent", timeout=30000)
    pg.locator("jade-chat").get_by_role("button", name="Show me what you can do").click()
    pg.wait_for_function("!document.getElementById('chat').busy", timeout=30000); pg.wait_for_timeout(600)
    shot(pg, "chat")
    check("chat", pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--jade-accent').trim()") in ("#1fe5a5", "#0a8f63"), "Vault tokens")
    check("chat", not errs, f"errors {errs[:2]}"); pg.close()

    # course
    pg, errs = open_("course/")
    pg.wait_for_function("document.querySelector('jade-course')?.shadowRoot?.querySelector('header h1')", timeout=30000); pg.wait_for_timeout(1500)
    shot(pg, "course")
    pg.locator("jade-course >> nav.rail button").nth(2).click(); pg.locator("jade-course >> .tabs button:has-text('Practice')").click()
    pg.locator("jade-course >> .lab .btn:has-text('Show solution')").click(); pg.locator("jade-course >> .lab .btn:has-text('Run tests')").click()
    pg.locator("jade-course >> .results .verdict").wait_for(timeout=40000); pg.wait_for_timeout(300)
    check("course", pg.locator("jade-course >> .results .verdict.ok").count() == 1, "Python lab passes on MicroPython from the pinned engine CDN")
    shot(pg, "course-python")
    check("course", not errs, f"errors {errs[:2]}"); pg.close()

    # the PNGtuber
    pg, errs = open_("jade/")
    pg.wait_for_function("window.JadeDemo && JadeDemo.state.ready", timeout=20000)
    pg.click("text=happy"); pg.click("#flap"); pg.wait_for_timeout(500)
    shot(pg, "jade")
    check("jade", pg.evaluate("JadeDemo.state.kind") == "png", "renders"); check("jade", not errs, f"errors {errs[:2]}"); pg.close()

    # the RPG
    pg, errs = open_("rpg/", (1280, 750))
    pg.wait_for_function("window.VN && (VN.state || VN.error)", timeout=60000)
    check("rpg", not pg.evaluate("VN.error"), "engine boots from the CDN")
    pg.wait_for_timeout(500); pg.mouse.click(640, 392); pg.wait_for_timeout(1500)
    for _ in range(40):
        if pg.evaluate("VN.state.VM.wait && VN.state.VM.wait.kind") != "say": break
        pg.keyboard.press("Enter"); pg.wait_for_timeout(60)
    pg.wait_for_timeout(600); shot(pg, "rpg")
    check("rpg", not errs, f"errors {errs[:2]}"); pg.close()

    # Jade's Vault, with Jade in Live2D at the Comms Desk
    pg, errs = open_("vault/", (1280, 750))
    pg.wait_for_function("window.VN && (VN.state || VN.error)", timeout=60000)
    check("vault", not pg.evaluate("VN.error"), "engine boots from the CDN")
    pg.wait_for_timeout(500); pg.mouse.click(640, 392); pg.wait_for_timeout(1500)
    for _ in range(40):
        if pg.evaluate("VN.state.VM.wait && VN.state.VM.wait.kind") != "say": break
        pg.keyboard.press("Enter"); pg.wait_for_timeout(80)
    pg.wait_for_timeout(1500); shot(pg, "vault")
    l = pg.evaluate("VN.state.py('locus(\"comms\")')"); l = l.get("v", l) if isinstance(l, dict) else l
    pg.evaluate(f"VN.state.exec('pos.update({{\"x\": {l['s'][0]//24}, \"y\": {l['s'][1]//24}, \"rev\": pos[\"rev\"] + 1}})')"); pg.evaluate("VN.refresh()"); pg.wait_for_timeout(600)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    for _ in range(6):
        if pg.evaluate("VN.state.layers.master.some(x => x.tag === 'jade')"): break
        pg.keyboard.press("Enter"); pg.wait_for_timeout(400)
    pg.wait_for_timeout(6000); shot(pg, "vault-live2d")
    check("vault", not errs, f"errors {errs[:3]}"); pg.close()

    # the examples page and a site
    for path, name in (("", "examples"), ("demo/", "site")):
        pg, errs = open_(path); pg.wait_for_timeout(2000); shot(pg, name); check(name, not errs, f"errors {errs[:2]}"); pg.close()
    b.close()
sys.exit(1 if fails else 0)
