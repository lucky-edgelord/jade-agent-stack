"""jade-vn-engine: visual novels and games written in a Ren'Py-style script, run on MicroPython in the browser.
The toolkit runs the engine's own compiler and packager (tools/vnc.py, tools/build.py) at the pinned commit."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

from .. import compat
from ..errors import JadeError
from .source import checkout

STARTER = '''# {name}: a jade-vn-engine game. Build it with `jade vn build {dir}`.
define j = Character("Jade", who_color="#1fe5a5")

label start:
    scene Solid("#040807")
    j "Welcome to {name}."
    menu:
        "Show me an effect":
            $ renpy.fx("crt")
            j "Scanlines, the way old screens drew them."
        "Skip it":
            pass
    j "Edit script.rpy to make this yours."
    return
'''


def _load(d: Path):
    """import the engine's build.py (which imports vnc.py) from a checkout, under private module names"""
    key = f"_jade_vn_build_{abs(hash(str(d)))}"
    if key in sys.modules:
        return sys.modules[key]
    tools = str(d / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    spec = importlib.util.spec_from_file_location(key, d / "tools" / "build.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.modules[key] = m
    return m


def new(name: str, *, dir: str | None = None, libs: list[str] | None = None, title: str | None = None) -> dict:
    g = Path(dir or name)
    if (g / "game.toml").exists():
        raise JadeError(f"{g} already has a game.toml", "JADE400")
    g.mkdir(parents=True, exist_ok=True)
    toml = f'name = "{(title or name).replace(chr(34), "")}"\n'
    if libs:
        toml += f'libs = "{", ".join(libs)}"\n'
    (g / "game.toml").write_text(toml)
    (g / "script.rpy").write_text(STARTER.format(name=title or name, dir=g))
    (g / "assets").mkdir(exist_ok=True)
    return {"dir": str(g), "files": ["game.toml", "script.rpy", "assets/"], "libs": libs or []}


def check(dir: str = ".", *, engine: str | None = None) -> dict:
    """compile the scripts (with the stdlib and the game's libs) without writing anything"""
    d = checkout("vn", engine)
    b = _load(d)
    g = Path(dir)
    if not (g / "game.toml").exists() and not list(g.glob("*.rpy")):
        raise JadeError(f"{g} has no game.toml or .rpy scripts", "JADE405")
    meta = b.toml(str(g / "game.toml"))
    libs = [x.strip() for x in meta.get("libs", "").split(",") if x.strip()]
    files = [str(d / "engine" / "stdlib.rpy")] + [str(d / "engine" / "lib" / f"{x}.rpy") for x in libs] + sorted(str(p) for p in g.rglob("*.rpy"))
    for f in files:
        if not Path(f).exists():
            raise JadeError(f"unknown lib {Path(f).stem!r} in game.toml", "JADE407")
    try:
        out = b.vnc.compile_files(files)
    except b.vnc.CompileError as e:
        raise JadeError(str(e), "JADE407") from e
    return {"dir": str(g), "name": meta.get("name", g.resolve().name), "ops": len(out["code"]), "labels": sorted(k for k in out["labels"] if not k.startswith("_")),
            "libs": libs, "engine": _ref(d)}


def build(dir: str = ".", *, out: str | None = None, cdn: bool = False, engine: str | None = None) -> dict:
    """→ a playable folder and a .xdc. cdn=True loads the engine from the pinned CDN path instead of copying it in."""
    d = checkout("vn", engine)
    b = _load(d)
    g = Path(dir).resolve()
    name = g.name
    outdir = Path(out).resolve() if out else g / "build"
    xdc = (outdir.parent if out else g) / "dist" / f"{name}.xdc"
    url = compat.CDN["vn"].rsplit("/", 1)[0] + "/" if cdn else None
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):  # the packager prints; keep stdout clean for JSON-lines and MCP
            o, x = b.build(str(g), outdir=str(outdir), xdc=str(xdc), cdn=url)
    except b.vnc.CompileError as e:
        raise JadeError(str(e), "JADE407") from e
    return {"out": o, "xdc": x, "bytes": Path(x).stat().st_size, "engine": url or _ref(d), "log": log.getvalue().strip()}


def _ref(d: Path) -> str:
    return d.name if d.parent.name == "vn" else f"local {d}"
