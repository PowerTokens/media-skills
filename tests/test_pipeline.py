"""Offline pipeline + repo structure tests (no network, no credits). ffmpeg tests skip if absent."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("POWERTOKENS_CONFIG_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "tools" / "shared"))
import pt_common as pt  # noqa: E402
import pipeline  # noqa: E402

SKILLS = ROOT / "plugins" / "powertokens-media" / "skills"
BANNED = ["deepseek-v4-1-flash-260910", "deepseek-v4-pro-0813", "deepseek-v4-flash-0731", "deepseek-flash",
          "kling-video-o1"]


def project(tmp, example="product-ad.json"):
    d = Path(tmp)
    (d / "refs").mkdir(exist_ok=True)
    for f in ("product.png", "refs/ning.png", "refs/ava.png", "refs/mia.png"):
        (d / f).write_bytes(b"\x89PNG fake")
    shutil.copy(ROOT / "tools" / "examples" / example, d / example)
    return str(d / example)


class PipelineTests(unittest.TestCase):
    def test_examples_validate(self):
        for ex in ("product-ad.json", "short-drama.json", "ugc-ad.json", "bilingual-vo.json"):
            with tempfile.TemporaryDirectory() as tmp:
                spec = pipeline.load(project(tmp, ex))
                self.assertEqual(pipeline.validate(spec), [], ex)

    def test_validate_catches_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text(json.dumps({"shots": [
                {"id": "a", "prompt": "x", "model": "seedance-fast", "resolution": "1080p"},
                {"id": "b", "prompt": "x", "model": "kling", "ref_images": ["https://e.com/a.png"]},
                {"id": "c", "prompt": "x", "characters": ["ghost"]}]}))
            errs = " | ".join(pipeline.validate(pipeline.load(str(p))))
            self.assertIn("480p, 720p", errs)
            self.assertIn("Kling", errs)
            self.assertIn("unknown character ghost", errs)

    def test_plan_estimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(project(tmp))
            pipeline.validate(spec)
            p = pipeline.plan(spec)
            # 2 x Wan 720p 4 s (0.10/s) + Kling 1080p 3 s (0.168/s) = 0.80 + 0.504
            self.assertAlmostEqual(p["video_est_usd"], 1.30, places=2)
            self.assertTrue(any("voiceover" in u for u in p["not_estimated"]))

    def test_run_refuses_without_matching_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(project(tmp))
            pipeline.validate(spec)
            for bad in (None, 0.5):
                with self.assertRaises(pt.PTError) as ctx:
                    pipeline.cmd_run(spec, bad, 1)
                self.assertEqual(ctx.exception.kind, "NEEDS_APPROVAL")

    def test_run_saves_task_id_then_resumes_without_resubmit(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(project(tmp, "short-drama.json"))
            pipeline.validate(spec)
            spec["shots"] = spec["shots"][:1]
            approve = pipeline.plan(spec)["video_est_usd"]
            posts = []

            def fake_request(method, path, payload=None, cred=None, **k):
                if method == "POST":
                    posts.append(payload)
                    return 200, {"id": "task_abc"}, {}
                raise AssertionError("unexpected")

            with mock.patch.dict(os.environ, {"POWERTOKENS_API_KEY": "sk-test"}), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=pt.PTError("slow", "TIMEOUT", 5)), \
                 mock.patch("sys.stdout"):
                pipeline.cmd_run(spec, approve, 1)
            st = pipeline.load_state(spec)["shots"]["s01"]
            self.assertEqual(st["task_id"], "task_abc")
            self.assertEqual(len(posts), 1)
            body = posts[0]
            self.assertTrue(any(m["type"] == "reference_image" for m in body["media"]))
            self.assertIn("Ning, a woman", body["media"][0]["text"])
            # plan now treats the submitted shot as already paid
            self.assertEqual(pipeline.plan(spec)["video_est_usd"], 0.0)
            # second run: resumes the saved task, no new POST
            out = str(Path(spec["_workdir"]) / "clips" / "s01.mp4")
            with mock.patch.dict(os.environ, {"POWERTOKENS_API_KEY": "sk-test"}), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download", return_value=out) as w, \
                 mock.patch("sys.stdout"):
                rc = pipeline.cmd_run(spec, 0.0, 1)
            self.assertEqual(rc, 0)
            self.assertEqual(len(posts), 1)
            self.assertEqual(w.call_args[0][2], "task_abc")

    def test_srt(self):
        spec = {"shots": [{"caption": "Hi"}, {}, {"caption": "Bye"}]}
        srt = pipeline.build_srt(spec, [2.0, 1.5, 3.0])
        self.assertIn("00:00:00,000 --> 00:00:02,000\nHi", srt)
        self.assertIn("00:00:03,500 --> 00:00:06,500\nBye", srt)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
class AssembleTests(unittest.TestCase):
    def test_assemble_real_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(project(tmp))
            pipeline.validate(spec)
            wd = Path(spec["_workdir"])
            (wd / "clips").mkdir(parents=True)
            (wd / "voiceover").mkdir()
            state = {"shots": {}, "voiceover": {}}
            for i, shot in enumerate(spec["shots"]):
                c = wd / "clips" / ("%s.mp4" % shot["id"])
                size = "1280x720" if i == 2 else "720x1280"   # one off-ratio clip to test padding
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=%s:rate=24:duration=2" % size,
                                "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest",
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(c)],
                               check=True, capture_output=True)
                state["shots"][shot["id"]] = {"status": "done", "output": str(c)}
            vo = wd / "voiceover" / "vo01.mp3"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=3", str(vo)],
                           check=True, capture_output=True)
            state["voiceover"]["vo01"] = {"status": "done", "output": str(vo)}
            pipeline.save_state(spec, state)
            with mock.patch("sys.stdout"):
                pipeline.cmd_assemble(spec, None, True, False)
            final = wd / "thermos-ad-final.mp4"
            self.assertTrue(final.is_file())
            self.assertAlmostEqual(pipeline.probe_duration(str(final)), 6.0, delta=0.3)
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                "stream=width,height", "-of", "csv=p=0", str(final)], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "1080,1920")
            with mock.patch("sys.stdout"):
                pipeline.cmd_reformat(str(final), "1:1", "pad", None)
            sq = wd / "thermos-ad-final-1x1.mp4"
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                "stream=width,height", "-of", "csv=p=0", str(sq)], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "1080,1080")


class RepoStructureTests(unittest.TestCase):
    def test_skills_frontmatter_evals_and_banned_models(self):
        names = []
        for skill in sorted(SKILLS.iterdir()):
            md = (skill / "SKILL.md").read_text(encoding="utf-8")
            m = re.match(r"^---\nname: (\S+)\ndescription: (.+?)\n", md)
            self.assertTrue(m, skill.name)
            self.assertEqual(m.group(1), skill.name)
            self.assertLess(len(m.group(2)), 1024, skill.name)
            self.assertLess(len(md.splitlines()), 500, skill.name)
            for ref in re.findall(r"`(references/[\w.-]+|examples/[\w.-]+|scripts/[\w.-]+)`", md):
                self.assertTrue((skill / ref).is_file(), "%s -> %s" % (skill.name, ref))
            self.assertTrue((ROOT / "evals" / ("%s.trigger_eval.json" % skill.name)).is_file(), skill.name)
            names.append(skill.name)
        for f in list(SKILLS.rglob("*")) + list((ROOT / "tools").rglob("*")):
            if f.is_file() and f.suffix in (".md", ".py", ".json"):
                text = f.read_text(encoding="utf-8")
                for b in BANNED:
                    if b == "kling-video-o1":
                        text = text.replace("Avoid `kling-video-o1*`", "")
                    self.assertNotIn(b, text, str(f))
        self.assertGreaterEqual(len(names), 11)

    def test_synced(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_scripts.py"), "--check"])
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
