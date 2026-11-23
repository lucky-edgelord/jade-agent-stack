"""Source checkouts of the front-end repositories the CLI builds with (jade-vn-engine's compiler, jade-edu's validator),
at the commits pinned in compat.REFS. A local checkout wins: JADE_VN_ENGINE / JADE_EDU, or the --engine argument.
Downloads are GitHub archives of the pinned commit, kept in $JADE_CACHE (default ~/.cache/jade)."""

from __future__ import annotations

import io
import os
import tarfile
import urllib.request
from pathlib import Path

from .. import compat
from ..errors import JadeError

ENV = {"vn": "JADE_VN_ENGINE", "edu": "JADE_EDU"}
NEEDS = {"vn": ("tools/vnc.py", "tools/build.py", "engine/vn.js"), "edu": ("src/core/course.js", "src/edu.js")}
KEEP = {"vn": ("engine/", "tools/"), "edu": ("src/", "assets/", "tools/")}


def cache_root() -> Path:
    return Path(os.environ.get("JADE_CACHE") or Path.home() / ".cache" / "jade")


def _ok(part: str, d: Path) -> bool:
    return all((d / f).is_file() for f in NEEDS[part])


def checkout(part: str, local: str | None = None) -> Path:
    """→ a folder holding the part at its pinned commit (or the local checkout given)"""
    local = local or os.environ.get(ENV[part])
    if local:
        d = Path(local).expanduser().resolve()
        if not _ok(part, d):
            raise JadeError(f"{d} is not a {compat.REQUIRES[part][1]} checkout (it needs {', '.join(NEEDS[part])})", "JADE409")
        return d
    ref = compat.REFS[part]
    d = cache_root() / part / ref
    if _ok(part, d):
        return d
    url = f"https://codeload.github.com/{compat.REQUIRES[part][1]}/tar.gz/{ref}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jade-agent-stack"}), timeout=60) as r:
            data = r.read()
    except OSError as e:
        raise JadeError(f"could not download {compat.REQUIRES[part][1]}@{ref[:7]}: {e}. Offline? Set {ENV[part]} to a local checkout.", "JADE200") from e
    tmp = d.with_name(d.name + ".part")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        for m in t.getmembers():
            name = m.name.split("/", 1)[1] if "/" in m.name else ""
            if not name or not name.startswith(KEEP[part]) or not (m.isfile() or m.isdir()):
                continue
            target = (tmp / name).resolve()
            if not str(target).startswith(str(tmp.resolve()) + os.sep):  # no path escapes
                continue
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(t.extractfile(m).read())
    if not _ok(part, tmp):
        raise JadeError(f"the {part} archive at {ref[:7]} is missing {', '.join(NEEDS[part])}", "JADE409")
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists():
        import shutil
        shutil.rmtree(d)
    tmp.rename(d)
    return d
