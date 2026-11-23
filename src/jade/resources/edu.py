"""jade-edu: courses from one JSON file, played by <jade-course> from a CDN. The validator is jade-edu's own
(src/core/course.js at the pinned commit), run with Node, so the CLI and the player agree on every rule."""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

from .. import compat
from ..errors import JadeError
from .source import checkout

TEACHERS = ("jade", "none")


def _node(script: str, *args: str, edu: str | None = None) -> dict:
    node = shutil.which("node")
    if not node:
        raise JadeError("jade-edu's validator needs Node.js (18 or later) on PATH", "JADE409")
    course_js = (checkout("edu", edu) / "src" / "core" / "course.js").as_uri()
    p = subprocess.run([node, "--input-type=module", "-e", f"import C from {json.dumps(course_js)};\n{script}", "--", *args],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise JadeError(f"node failed: {p.stderr.strip()[-400:]}", "JADE409")
    return json.loads(p.stdout)


def validate(file: str, *, edu: str | None = None) -> dict:
    if not Path(file).is_file():
        raise JadeError(f"no such file: {file}", "JADE405")
    r = _node("""import fs from 'node:fs';
const v = C.validate(fs.readFileSync(process.argv.at(-1), 'utf8')), c = v.course;
console.log(JSON.stringify({ ok: v.ok, errors: v.errors, warnings: v.warnings, id: c?.id, title: c?.title,
  chapters: c ? c.chapters.length : 0, labs: c ? c.chapters.reduce((n, x) => n + x.practice.length, 0) : 0,
  quiz: c ? c.chapters.reduce((n, x) => n + x.quiz.length, 0) : 0, exam: !!c?.exam }));""", str(Path(file).resolve()), edu=edu)
    r["file"] = file
    if not r["ok"]:
        raise JadeError("; ".join(r["errors"]), "JADE408", data=r)
    return r


def new(out: str, *, title: str | None = None, edu: str | None = None) -> dict:
    """write jade-edu's starter course (every block and lab kind, ready to edit)"""
    if Path(out).exists():
        raise JadeError(f"{out} already exists", "JADE400")
    t = _node("console.log(JSON.stringify(C.template()));", edu=edu)
    if title:
        t["title"] = title
        t["id"] = "".join(ch if ch.isalnum() else "-" for ch in title.lower()).strip("-")[:48] or t["id"]
    Path(out).write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n")
    return {"out": out, "title": t["title"], "chapters": len(t["chapters"])}


def page(course: str, out: str, *, teacher: str = "jade", title: str | None = None, model: str | None = None, core: str | None = None) -> dict:
    """a page that plays the course with <jade-course> from the pinned CDN"""
    if teacher not in TEACHERS and not model:
        raise JadeError(f"teacher must be one of {', '.join(TEACHERS)} (or give model= for Live2D)", "JADE400")
    attrs = f'src="{html.escape(course)}"' + (f' model="{html.escape(model)}"' if model else f' teacher="{teacher}"') + (f' core="{html.escape(core)}"' if core else "")
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title or "Course")}</title><style>html,body{{margin:0;height:100%;background:#040807}}jade-course{{height:100vh}}</style>
<script type="module" src="{html.escape(compat.CDN['edu'])}"></script></head>
<body><jade-course {attrs}></jade-course></body></html>
"""
    Path(out).write_text(doc)
    return {"out": out, "course": course, "teacher": "live2d" if model else teacher, "module": compat.CDN["edu"]}
