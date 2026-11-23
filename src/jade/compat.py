"""What this toolkit works with (STACK.md is generated from this). Major mismatch: refuse. Older minor: warn."""

from __future__ import annotations

import re

TOOLKIT = "0.1.0"
# repo → (minimum version, repository, interface)
REQUIRES = {
    "base": ("0.6.0", "lucky-edgelord/jade-agent-base", "REST /api/agent/tools, MCP /api/agent/mcp, /api/agent/credentials"),
    "vault": ("2.18.3", "lucky-edgelord/jade-vault", "HTTP API /v1 (api 1), header-only auth"),
    "kit": ("3.1.0", "lucky-edgelord/Jade-agent-kit", "JS embed (ES module from a CDN)"),
    "ui": ("1.3.0", "lucky-edgelord/Jade-agent-ui-ux", "web components in Jade's Vault look (ES module from a CDN)"),
    "vn": ("0.1.0", "lucky-edgelord/jade-vn-engine", "ES modules from a CDN + vnc.py compiler (Ren'Py-style scripts on MicroPython)"),
    "edu": ("0.1.0", "lucky-edgelord/jade-edu", "ES module from a CDN (<jade-course>, course JSON)"),
}
# exact commits the toolkit fetches (CLI builds) and pages load, until these repositories publish tags
REFS = {
    "ui": "929fe39282c56e65a1ab9c7f5bf609179613ae53",
    "vn": "1268c01e51aab7d65bc1648428105a279f84682b",
    "edu": "82e877ff5c825eff5af4707ace892e48a39bf740",
}
# what generated pages load
CDN = {
    "kit": "https://cdn.jsdelivr.net/gh/lucky-edgelord/Jade-agent-kit@v3.1.0/dist/jade-agent-kit.js",
    "ui": f"https://cdn.jsdelivr.net/gh/lucky-edgelord/Jade-agent-ui-ux@{REFS['ui'][:7]}/dist/jade-ui.js",
    "vn": f"https://cdn.jsdelivr.net/gh/lucky-edgelord/jade-vn-engine@{REFS['vn'][:7]}/engine/vn.js",
    "edu": f"https://cdn.jsdelivr.net/gh/lucky-edgelord/jade-edu@{REFS['edu'][:7]}/src/edu.js",
}


def parse(v: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(v or ""))
    if not m:
        return (0, 0, 0)
    return tuple(int(x or 0) for x in m.groups())  # type: ignore[return-value]


def check(repo: str, version: str) -> tuple[str, str]:
    """→ ("ok" | "warn" | "refuse", message)"""
    need = REQUIRES[repo][0]
    have, want = parse(version), parse(need)
    if have == (0, 0, 0):
        return "warn", f"{repo}: version unknown; this toolkit expects {need} or later in {want[0]}.x"
    if have[0] != want[0]:
        return "refuse", f"{repo} {version} is outside {want[0]}.x (this toolkit needs {need} or later in {want[0]}.x)"
    if have < want:
        return "warn", f"{repo} {version} is older than {need}; some features are missing"
    return "ok", f"{repo} {version}"
