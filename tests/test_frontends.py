"""jade vn / jade edu: games with jade-vn-engine and courses with jade-edu. They need checkouts of both repositories:
JADE_VN_ENGINE and JADE_EDU, or ../jade-vn-engine (../vn-engine) and ../jade-edu next to this one. jade edu also needs Node."""
import io
import json
import os
import shutil
import tarfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from helpers import ROOT, isolate

from jade import commands, compat
from jade.errors import JadeError
from jade.resources import source


def _find(env, *names):
    for p in [os.environ.get(env)] + [str(ROOT.parent / n) for n in names]:
        if p and Path(p).is_dir():
            return str(Path(p).resolve())
    return None


VN = _find("JADE_VN_ENGINE", "jade-vn-engine", "vn-engine")
EDU = _find("JADE_EDU", "jade-edu")


def run(cmd, **args):
    return commands.REGISTRY[cmd].run(commands.Context(interactive=False), **{p.name: args.get(p.name, p.default) for p in commands.REGISTRY[cmd].params})


class Pins(unittest.TestCase):
    def test_pins_are_full_commits_and_cdn_matches(self):
        for part in ("vn", "edu"):
            self.assertRegex(compat.REFS[part], r"^[0-9a-f]{40}$")
            self.assertIn("@" + compat.REFS[part][:7] + "/", compat.CDN[part])
            self.assertIn(part, compat.REQUIRES)
        stack = (ROOT / "STACK.md").read_text()
        self.assertIn(compat.REFS["vn"], stack)
        self.assertIn(compat.CDN["edu"], stack)

    def test_commands_on_every_surface(self):
        for n in ("vn.new", "vn.check", "vn.build", "edu.new", "edu.validate", "edu.page"):
            self.assertIn(n, commands.REGISTRY)
            self.assertIn("mcp", commands.REGISTRY[n].surfaces)

    def test_download_is_cached_and_safe(self):
        d = isolate(self)
        os.environ["JADE_CACHE"] = str(d / "cache")
        self.addCleanup(os.environ.pop, "JADE_CACHE", None)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            for name, body in (("x/src/core/course.js", b"export default {}"), ("x/src/edu.js", b"//"), ("x/../evil.txt", b"no"), ("x/README.md", b"skip")):
                ti = tarfile.TarInfo(name); ti.size = len(body); t.addfile(ti, io.BytesIO(body))
        calls = []

        class R(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake(req, timeout=0):
            calls.append(req.full_url); return R(buf.getvalue())
        with mock.patch.dict(os.environ, {"JADE_EDU": ""}), mock.patch("urllib.request.urlopen", fake):
            p = source.checkout("edu")
            source.checkout("edu")
        self.assertEqual(len(calls), 1)
        self.assertIn(compat.REFS["edu"], calls[0])
        self.assertTrue((p / "src/core/course.js").exists())
        self.assertFalse((p / "README.md").exists())
        self.assertFalse(list(d.rglob("evil.txt")))

    def test_bad_local_checkout(self):
        isolate(self)
        with self.assertRaises(JadeError) as e:
            source.checkout("vn", "/nonexistent")
        self.assertEqual(e.exception.code, "JADE409")


@unittest.skipUnless(VN, "no jade-vn-engine checkout")
class Games(unittest.TestCase):
    def setUp(self):
        self.d = isolate(self)

    def test_new_check_build(self):
        r = run("vn.new", name="mygame", libs=["minigames"])
        self.assertTrue((self.d / "mygame/game.toml").exists())
        self.assertIn("minigames", (self.d / "mygame/game.toml").read_text())
        c = run("vn.check", dir="mygame", engine=VN)
        self.assertIn("start", c["labels"])
        b = run("vn.build", dir="mygame", engine=VN)
        names = zipfile.ZipFile(b["xdc"]).namelist()
        for f in ("index.html", "game.json", "vn.js", "vendor/micropython.wasm", "manifest.toml"):
            self.assertIn(f, names)
        small = run("vn.build", dir="mygame", cdn=True, out=str(self.d / "cdn"), engine=VN)
        self.assertNotIn("vn.js", zipfile.ZipFile(small["xdc"]).namelist())
        self.assertIn(compat.CDN["vn"].rsplit("/", 1)[0], (Path(small["out"]) / "index.html").read_text())
        self.assertLess(small["bytes"], b["bytes"] // 10)

    def test_script_error_names_the_line(self):
        run("vn.new", name="bad")
        (self.d / "bad/script.rpy").write_text('label start:\n    "hi"\n    jump nowhere_at_all\n    menu\n')
        with self.assertRaises(JadeError) as e:
            run("vn.check", dir="bad", engine=VN)
        self.assertEqual(e.exception.code, "JADE407")

    def test_new_refuses_to_overwrite(self):
        run("vn.new", name="g")
        with self.assertRaises(JadeError):
            run("vn.new", name="g")


@unittest.skipUnless(EDU and shutil.which("node"), "no jade-edu checkout or no node")
class Courses(unittest.TestCase):
    def setUp(self):
        self.d = isolate(self)

    def test_new_validate_page(self):
        r = run("edu.new", out="c.json", title="Intro to Jade", edu=EDU)
        self.assertEqual(json.loads(Path("c.json").read_text())["format"], "jade-course")
        v = run("edu.validate", file="c.json", edu=EDU)
        self.assertTrue(v["ok"])
        self.assertEqual(v["id"], "intro-to-jade")
        self.assertGreaterEqual(v["labs"], 5)
        ex = run("edu.validate", file=str(Path(EDU) / "examples/stack-101.course.json"), edu=EDU)
        self.assertEqual((ex["chapters"], ex["warnings"]), (3, []))
        p = run("edu.page", course="c.json", out="index.html")
        html = Path("index.html").read_text()
        self.assertIn(compat.CDN["edu"], html)
        self.assertIn('<jade-course src="c.json" teacher="jade">', html)
        run("edu.page", course="c.json", out="l2d.html", model="m/x.model3.json", core="core.js")
        self.assertIn('model="m/x.model3.json"', Path("l2d.html").read_text())

    def test_broken_course(self):
        Path("bad.json").write_text('{"title": "x", "chapters": []}')
        with self.assertRaises(JadeError) as e:
            run("edu.validate", file="bad.json", edu=EDU)
        self.assertEqual(e.exception.code, "JADE408")
        self.assertIn("chapters", e.exception.message)


if __name__ == "__main__":
    unittest.main()
