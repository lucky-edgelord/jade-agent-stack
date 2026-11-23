"""Themes: the design tokens of a site (--jade-* CSS custom properties, the same ones Jade Agent UI/UX reads), in light
and dark, plus a font. A theme is a few base colours; the rest is derived, so adding one is a few lines."""

from __future__ import annotations


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def mix(a: str, b: str, t: float) -> str:
    """a blended toward b by t (0..1)"""
    x, y = _rgb(a), _rgb(b)
    return _hex(tuple(x[i] + (y[i] - x[i]) * t for i in range(3)))


def _lum(h: str) -> float:
    r, g, b = (v / 255 for v in _rgb(h))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def on(color: str) -> str:
    """black or white text, whichever reads better on color"""
    return "#ffffff" if _lum(color) < 0.4 else "#0b0b0b"


def palette(bg: str, fg: str, accent: str, *, ok="#1f8a5b", warn="#a8650f", danger="#c0392b", syntax=None) -> dict:
    """all colour tokens from three base colours"""
    dark = _lum(bg) < 0.2
    p = {
        "bg": bg, "fg": fg, "accent": accent, "accent-fg": on(accent),
        "surface": mix(bg, fg, 0.04 if dark else 0.0) if dark else mix(bg, "#ffffff", 0.7),
        "surface-2": mix(bg, fg, 0.09 if dark else 0.05),
        "muted": mix(fg, bg, 0.42), "border": mix(bg, fg, 0.16 if dark else 0.13),
        "user": mix(bg, accent, 0.18 if dark else 0.12), "user-fg": fg, "code": mix(bg, fg, 0.06 if dark else 0.035),
        "ok": ok, "warn": warn, "danger": danger,
    }
    s = syntax or ((mix(accent, "#ffffff", 0.3), "#f0a47e", "#c8a4f0", mix(fg, bg, 0.45)) if dark else (mix(accent, "#000000", 0.25), "#9a3f1c", "#7a4bb3", mix(fg, bg, 0.45)))
    p.update({"syn-k": s[0], "syn-s": s[1], "syn-n": s[2], "syn-c": s[3]})
    return p


SANS = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
FONTS = {
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "Fraunces": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&display=swap",
    "Space Grotesk": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
    "IBM Plex Sans": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
    "JetBrains Mono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap",
    "DM Sans": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap",
}

# name: (description, light (bg, fg, accent), dark (bg, fg, accent), font, radius)
_T = {
    "classic": ("Calm green on near-white; the old jade palette", ("#f7faf8", "#15201b", "#0b7a5b"), ("#0e1411", "#e4ede8", "#3ddc97"), None, 12),
    "midnight": ("Indigo on deep navy", ("#f6f7fb", "#171a2b", "#4f46e5"), ("#0b0d17", "#e6e8f5", "#8b85ff"), "Inter", 12),
    "paper": ("Warm paper, rust accent, a serif for headings", ("#faf8f4", "#2a2620", "#a14a1f"), ("#1a1714", "#ece6dc", "#e39a6b"), "Fraunces", 8),
    "contrast": ("Maximum contrast for readability", ("#ffffff", "#000000", "#0040c0"), ("#000000", "#ffffff", "#ffd400"), None, 6),
    "sunset": ("Coral and amber, friendly and bright", ("#fff8f3", "#2b1a14", "#e8573b"), ("#1c1210", "#f6e7df", "#ff8a5c"), "DM Sans", 16),
    "ocean": ("Deep teal and sea blue", ("#f3f8fa", "#0f2530", "#0e7490"), ("#081820", "#dcedf2", "#38bdf8"), "Inter", 12),
    "forest": ("Moss and pine, earthy", ("#f5f7f0", "#1d2618", "#4d7c0f"), ("#11160d", "#e3ead9", "#a3e635"), "IBM Plex Sans", 10),
    "rose": ("Soft rose and plum", ("#fdf6f8", "#2a1620", "#be185d"), ("#1b0f15", "#f4e4ec", "#f472b6"), "DM Sans", 18),
    "mono": ("Black and white, one sharp accent", ("#ffffff", "#111111", "#111111"), ("#0a0a0a", "#f2f2f2", "#f2f2f2"), "Space Grotesk", 4),
    "neon": ("Dark-first, electric violet and cyan", ("#f7f5ff", "#1a1530", "#7c3aed"), ("#0a0714", "#ece8ff", "#22d3ee"), "Space Grotesk", 14),
    "slate": ("Corporate blue-grey, quiet and professional", ("#f8fafc", "#0f172a", "#2563eb"), ("#0b1120", "#e2e8f0", "#60a5fa"), "Inter", 8),
    "terminal": ("Green phosphor, monospace everything", ("#f4f8f2", "#102010", "#15803d"), ("#050805", "#b6f5b0", "#39ff14"), "JetBrains Mono", 2),
}


# ---- "jade": Jade's own look from Jade Vault, token for token the same as Jade Agent UI/UX's default preset
_KEYS = ["bg", "surface", "surface-2", "fg", "muted", "border", "accent", "accent-fg", "user", "user-fg", "code",
         "ok", "warn", "danger", "syn-k", "syn-s", "syn-n", "syn-c"]
_JADE_LIGHT = dict(zip(_KEYS, ["#eef5f2", "#f8fcfa", "#e2ede8", "#06140f", "#4f665d", "#b9d3c8", "#0a8f63", "#ffffff", "#d7efe4", "#06140f", "#e6f0ec",
                                "#0a8f63", "#a8650f", "#d22b3c", "#0b6e99", "#b0306a", "#6b49b0", "#5c7369"]))
_JADE_DARK = dict(zip(_KEYS, ["#040807", "#09100e", "#0f1a17", "#e3f2ed", "#83998f", "#1a2d27", "#1fe5a5", "#00140c", "#0f2a20", "#e3f2ed", "#060c0a",
                               "#b8ffdf", "#f2c14e", "#ff3d4f", "#7fd8ff", "#ffb8c6", "#c8a4f0", "#5f7a6e"]))
_JADE_TYPE = {"display": "'Rajdhani','Arial Narrow',system-ui,sans-serif", "font": "'Chakra Petch',system-ui,-apple-system,'Segoe UI',sans-serif",
              "mono": "'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace", "cut": "10px"}
_JADE_LIGHT.update({**_JADE_TYPE, "glow": "0 0 0 1px rgb(10 143 99 / .25)", "accent-2": "#d22b6a"})
_JADE_DARK.update({**_JADE_TYPE, "glow": "0 0 0 1px #1d6b52, 0 0 18px rgb(31 229 165 / .16)", "accent-2": "#ffb8c6",
                   "shadow": "0 0 0 1px #1a2d27, 0 10px 30px rgb(0 0 0 / .45)"})
_FONT_CDN = "https://cdn.jsdelivr.net/npm/@fontsource"
JADE_FONTS = "".join(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;src:url({_FONT_CDN}/{pkg}@5/files/{pkg}-latin-{w}-normal.woff2) format('woff2')}}"
                     for fam, pkg, ws in (("Rajdhani", "rajdhani", (500, 600, 700)), ("Chakra Petch", "chakra-petch", (400, 500, 600)), ("JetBrains Mono", "jetbrains-mono", (400, 600)))
                     for w in ws)
# Vault's grid and scanline backdrop (dark only), the same as setTheme({ backdrop: true }) in Jade Agent UI/UX
JADE_BACKDROP = """body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background:
linear-gradient(transparent 0 calc(100% - 1px),rgb(31 229 165/.035) 0) 0 0/100% 32px,linear-gradient(90deg,transparent 0 calc(100% - 1px),rgb(31 229 165/.035) 0) 0 0/32px 100%,
radial-gradient(1200px 600px at 85% -10%,rgb(31 229 165/.10),transparent 60%),radial-gradient(900px 500px at -10% 110%,rgb(255 184 198/.06),transparent 60%)}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:2147483000;background:repeating-linear-gradient(0deg,rgb(0 0 0/.18) 0 1px,transparent 1px 3px);mix-blend-mode:multiply;opacity:.55}"""


def get(name: str) -> dict:
    """a theme: {name, description, light, dark, font, font_url, radius} (+ mode, css for "jade")"""
    if name == "jade":
        return {"name": "jade", "description": "Jade's own look from Jade Vault: netrunner green on void black, cut corners, Rajdhani, Chakra Petch and JetBrains Mono, grid and scanlines",
                "light": dict(_JADE_LIGHT), "dark": dict(_JADE_DARK), "font": None, "font_url": None, "radius": 2, "mode": "dark",
                "fonts_css": JADE_FONTS, "backdrop": JADE_BACKDROP}
    if name not in _T:
        raise KeyError(f"unknown theme {name!r}; themes: {', '.join(names())}")
    d, l, k, font, radius = _T[name]
    return {"name": name, "description": d, "light": palette(*l), "dark": palette(*k), "font": font, "font_url": FONTS.get(font),
            "radius": radius}


def names() -> list[str]:
    return ["jade", *_T]


def css(theme: dict, *, mode: str = "auto", overrides: dict | None = None) -> str:
    """the theme as CSS: tokens on :root for light, dark under prefers-color-scheme (mode auto) or forced"""
    font = f'"{theme["font"]}", {SANS}' if theme.get("font") else SANS
    mono = f'"{theme["font"]}", ui-monospace, monospace' if theme.get("font") == "JetBrains Mono" else "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    shared = {"radius": f'{theme["radius"]}px', "font": font, "mono": mono, "space": "8px", "font-size": "16px",
              "shadow": "0 1px 2px rgb(0 0 0 / .06), 0 8px 24px rgb(0 0 0 / .06)", "focus": "var(--jade-accent)",
              "display": "var(--jade-font)", "cut": "0px", "glow": "none", "accent-2": "var(--jade-accent)"}
    over = overrides or {}

    def block(colors, scheme):
        vals = {**shared, **colors, **over}
        return ";".join(f"--jade-{k}:{v}" for k, v in vals.items()) + f";color-scheme:{scheme}"

    pre = theme.get("fonts_css", "")
    bd = theme.get("backdrop", "")
    if mode == "light":
        return pre + f":root{{{block(theme['light'], 'light')}}}"
    if mode == "dark":
        return pre + f":root{{{block(theme['dark'], 'dark')}}}" + bd
    if bd:   # the backdrop is drawn only in dark mode
        bd = f"@media (prefers-color-scheme:dark){{:root:not([data-jade-mode=light]) {bd.replace('}' + chr(10) + 'body::after', '} :root:not([data-jade-mode=light]) body::after')}}}" + bd.replace("body::", ":root[data-jade-mode=dark] body::")
    return pre + (f":root{{{block(theme['light'], 'light')}}}"
            f"@media (prefers-color-scheme:dark){{:root:not([data-jade-mode=light]){{{block(theme['dark'], 'dark')}}}}}"
            f":root[data-jade-mode=dark]{{{block(theme['dark'], 'dark')}}}") + bd
