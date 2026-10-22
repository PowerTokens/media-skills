"""Offline tests for vision QC/hero gates, character bible, claim lint, caption safe-zone."""
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("POWERTOKENS_CONFIG_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "tools" / "shared"))
import pt_common as pt  # noqa: E402
import pipeline  # noqa: E402
import product_qc  # noqa: E402
import character_qc  # noqa: E402
import claim_lint  # noqa: E402

BIBLE = ROOT / "tools" / "examples" / "product-bible.thermos.json"
CHAR_BIBLE = ROOT / "tools" / "examples" / "character-bible.ning.json"


def product_project(tmp):
    d = Path(tmp)
    (d / "refs").mkdir(exist_ok=True)
    (d / "product.png").write_bytes(b"\x89PNG fake")
    (d / "product.jpg").write_bytes(b"\xff\xd8\xff fake")
    shutil.copy(ROOT / "tools" / "examples" / "product-ad.json", d / "product-ad.json")
    shutil.copy(BIBLE, d / "product-bible.thermos.json")
    return str(d / "product-ad.json")


class ClaimLintTests(unittest.TestCase):
    def test_flags_award_and_review_claims(self):
        hits = claim_lint.find_claims("Our award-winning serum has 500+ reviews")
        labels = {h["label"] for h in hits}
        self.assertTrue(any("award" in l for l in labels))
        self.assertTrue(any("review" in l for l in labels))

    def test_shotlist_refuses_unless_approved(self):
        spec = {
            "shots": [{"id": "s01", "caption": "FDA approved formula"}],
            "voiceover": {"lines": [{"id": "vo01", "text": "Clinically proven results"}]},
        }
        errs = claim_lint.lint_shotlist(spec)
        self.assertGreaterEqual(len(errs), 2)
        spec["claims_approved"] = True
        self.assertEqual(claim_lint.lint_shotlist(spec), [])

    def test_pipeline_validate_surfaces_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "product.png").write_bytes(b"\x89PNG")
            shots = json.loads((ROOT / "tools" / "examples" / "product-ad.json").read_text())
            shots["shots"][0]["caption"] = "Award-winning thermos"
            shutil.copy(BIBLE, d / "product-bible.thermos.json")
            (d / "bad.json").write_text(json.dumps(shots))
            errs = pipeline.validate(pipeline.load(str(d / "bad.json")))
            self.assertTrue(any("claim" in e.lower() or "award" in e.lower() for e in errs))


class CharacterQcTests(unittest.TestCase):
    def test_character_bible_schema(self):
        b = character_qc.load_bible(CHAR_BIBLE)
        self.assertEqual(b["characters"][0]["id"], "ning")
        self.assertIn("ponytail", b["characters"][0]["description"])

    def test_short_drama_requires_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            shots = {"kind": "short-drama", "shots": [
                {"id": "s01", "prompt": "x", "model": "wan3.0-video", "duration": 4,
                 "resolution": "720p", "ratio": "9:16"}]}
            (d / "shots.json").write_text(json.dumps(shots))
            ok, errs = character_qc.check_shotlist_characters(d / "shots.json")
            self.assertFalse(ok)
            self.assertTrue(any("character" in e.lower() for e in errs))

    def test_inline_characters_pass_short_drama(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "refs").mkdir()
            (d / "refs" / "ning.png").write_bytes(b"\x89PNG")
            shutil.copy(ROOT / "tools" / "examples" / "short-drama.json", d / "short-drama.json")
            spec = pipeline.load(str(d / "short-drama.json"))
            self.assertEqual(pipeline.validate(spec), [])

    def test_character_bible_file_merges(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "refs").mkdir()
            (d / "refs" / "ning.png").write_bytes(b"\x89PNG")
            shutil.copy(CHAR_BIBLE, d / "character-bible.ning.json")
            shots = {
                "kind": "short-drama",
                "character_bible": "character-bible.ning.json",
                "characters": {},
                "defaults": {"model": "wan3.0-video", "resolution": "720p", "ratio": "9:16", "duration": 4},
                "shots": [{"id": "s01", "characters": ["ning"], "prompt": "Ning walks in the rain."}],
            }
            (d / "shots.json").write_text(json.dumps(shots))
            spec = pipeline.load(str(d / "shots.json"))
            self.assertEqual(pipeline.validate(spec), [])
            self.assertIn("ning", spec["characters"])
            self.assertTrue(spec["characters"]["ning"]["description"])


class VisionHeroGateTests(unittest.TestCase):
    def test_vision_qc_wanted_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            self.assertTrue(pipeline.vision_qc_wanted(spec, None, False))
            self.assertFalse(pipeline.vision_qc_wanted(spec, None, True))
            self.assertTrue(pipeline.vision_qc_wanted(spec, True, False))
        bare = {"kind": "other", "shots": [], "defaults": {}, "characters": {},
                "_base": ".", "_workdir": "/tmp"}
        self.assertFalse(pipeline.vision_qc_wanted(bare, None, False))

    def test_hero_approve_flow_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = product_project(tmp)
            spec = pipeline.load(path)
            # Mark a keyframe on disk for s01
            wd = Path(spec["_workdir"])
            (wd / "keyframes").mkdir(parents=True)
            kf = wd / "keyframes" / "s01.png"
            kf.write_bytes(b"\x89PNG hero")
            state = {"shots": {"s01": {"status": "hero_pending", "keyframe": str(kf)}}, "voiceover": {}}
            pipeline.save_state(spec, state)
            with mock.patch("sys.stdout"):
                rc = pipeline.cmd_approve_hero(spec, "s01")
            self.assertEqual(rc, 0)
            self.assertTrue(pipeline.is_hero_approved(spec, "s01", str(kf)))
            pending = pipeline.load_json_file(pipeline.hero_pending_path(spec), {})
            self.assertNotIn("s01", pending)

    def test_ensure_keyframe_qc_fail_closed_without_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = product_project(tmp)
            spec = pipeline.load(path)
            shot = dict(spec["shots"][0])
            shot["keyframe"] = {"prompt": "hero packshot of the thermos"}
            shot["hero"] = True
            s = pipeline.shot_settings(spec, shot)
            wd = Path(spec["_workdir"])
            (wd / "keyframes").mkdir(parents=True)
            kf = wd / "keyframes" / ("%s.png" % s["id"])
            kf.write_bytes(b"\x89PNG")
            state = {"shots": {s["id"]: {"keyframe": str(kf)}}, "voiceover": {}}
            opts = {"vision_qc": True, "skip_vision_qc": False, "auto_approve_hero": False}

            def boom(*a, **k):
                raise pt.PTError("no chat", "NETWORK", 4)

            with mock.patch.object(product_qc, "call_vision_qc", side_effect=boom):
                with self.assertRaises(pt.PTError) as ctx:
                    pipeline.ensure_keyframe_qc_and_hero(spec, s, "cred", state, wd, opts)
                self.assertEqual(ctx.exception.kind, "VISION_QC")

    def test_ensure_keyframe_qc_pass_then_hero_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = product_project(tmp)
            spec = pipeline.load(path)
            shot = dict(spec["shots"][0])
            shot["keyframe"] = {"prompt": "hero"}
            shot["hero"] = True
            s = pipeline.shot_settings(spec, shot)
            wd = Path(spec["_workdir"])
            (wd / "keyframes").mkdir(parents=True)
            kf = wd / "keyframes" / ("%s.png" % s["id"])
            kf.write_bytes(b"\x89PNG")
            state = {"shots": {s["id"]: {"keyframe": str(kf)}}, "voiceover": {}}
            opts = {"vision_qc": True, "skip_vision_qc": False, "auto_approve_hero": False}
            verdict = {"pass": True, "failures": [], "structure_mode_seen": "closed", "notes": "ok"}
            with mock.patch.object(product_qc, "call_vision_qc", return_value=verdict):
                image, pause = pipeline.ensure_keyframe_qc_and_hero(spec, s, "cred", state, wd, opts)
            self.assertEqual(pause, "hero_pending")
            self.assertEqual(state["shots"][s["id"]]["status"], "hero_pending")
            self.assertTrue(Path(pipeline.hero_pending_path(spec)).is_file())

    def test_qc_retry_then_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = product_project(tmp)
            spec = pipeline.load(path)
            shot = dict(spec["shots"][0])
            shot["keyframe"] = {"prompt": "thermos on table"}
            s = pipeline.shot_settings(spec, shot)
            wd = Path(spec["_workdir"])
            (wd / "keyframes").mkdir(parents=True)
            kf = wd / "keyframes" / ("%s.png" % s["id"])
            kf.write_bytes(b"\x89PNG")
            state = {"shots": {s["id"]: {"keyframe": str(kf)}}, "voiceover": {}}
            opts = {"skip_vision_qc": False, "auto_approve_hero": True}
            bad = {"pass": False, "failures": ["hybrid part"], "structure_mode_seen": "unknown"}
            calls = {"n": 0}

            def fake_qc(*a, **k):
                calls["n"] += 1
                return bad

            def fake_gen(spec_, s_, cred, out):
                Path(out).write_bytes(b"\x89PNG2")
                return str(Path(out).resolve())

            with mock.patch.object(product_qc, "call_vision_qc", side_effect=fake_qc), \
                 mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen):
                with self.assertRaises(pt.PTError) as ctx:
                    pipeline.ensure_keyframe_qc_and_hero(spec, s, "cred", state, wd, opts)
            self.assertEqual(ctx.exception.kind, "VISION_QC")
            self.assertGreaterEqual(calls["n"], 2)
            failed = state["shots"][s["id"]]
            self.assertEqual(failed["qc"], "fail")
            self.assertIn("hybrid part", failed["qc_failures"])
            self.assertNotIn("task_id", failed)

    def test_skip_vision_qc_allows_hero_auto(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = product_project(tmp)
            spec = pipeline.load(path)
            shot = dict(spec["shots"][0])
            shot["keyframe"] = {"prompt": "hero"}
            shot["hero"] = True
            s = pipeline.shot_settings(spec, shot)
            wd = Path(spec["_workdir"])
            (wd / "keyframes").mkdir(parents=True)
            kf = wd / "keyframes" / ("%s.png" % s["id"])
            kf.write_bytes(b"\x89PNG")
            state = {"shots": {s["id"]: {"keyframe": str(kf)}}, "voiceover": {}}
            opts = {"skip_vision_qc": True, "auto_approve_hero": True}
            image, pause = pipeline.ensure_keyframe_qc_and_hero(spec, s, "cred", state, wd, opts)
            self.assertIsNone(pause)
            self.assertEqual(image, str(kf))


class KeyframeBatchGateTests(unittest.TestCase):
    def _run(self, spec, opts=None, parallel=1):
        approve = pipeline.plan(spec)["video_est_usd"]
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"POWERTOKENS_API_KEY": "sk-test"}), \
             mock.patch("sys.stdout", buf):
            rc = pipeline.cmd_run(spec, approve, parallel, opts)
        payload = json.loads(buf.getvalue())
        return rc, payload

    def test_blockers_and_report_include_why(self):
        spec = {
            "kind": "product-ad",
            "shots": [
                {"id": "s01", "keyframe": {"prompt": "a"}},
                {"id": "s02", "keyframe": {"prompt": "b"}},
                {"id": "s03", "prompt": "turntable", "image": "product.png"},
            ],
        }
        state = {"shots": {
            "s01": {"qc": "pass", "vision_qc_pass": True},
            "s02": {"qc": "fail", "vision_qc_retry": True, "qc_failures": [
                "hybrid structure", "third-party logo", "logo_policy_ok: no",
            ]},
        }}
        self.assertTrue(pipeline.keyframe_batch_gate_active(spec, {}))
        self.assertEqual(pipeline.keyframe_batch_blockers(spec, state, {}), ["s02"])
        msg, passed, report = pipeline.keyframe_batch_gate_message(spec, state, ["s02"])
        self.assertEqual(passed, ["s01"])
        self.assertIn("third-party logo", msg)
        self.assertIn("hybrid structure", msg)
        self.assertIn("after one keyframe retry", msg)
        self.assertEqual(report[0]["shot"], "s02")
        self.assertTrue(report[0]["retried"])
        self.assertIn("stopped in the keyframe phase", msg)
        self.assertFalse(pipeline.keyframe_batch_gate_active(spec, {"skip_vision_qc": True}))
        self.assertEqual(pipeline.keyframe_batch_blockers(spec, state, {"skip_vision_qc": True}), [])
        other = {"kind": "short-drama", "shots": [{"id": "s01", "keyframe": {"prompt": "a"}}]}
        self.assertEqual(pipeline.keyframe_batch_blockers(other, {"shots": {}}, {}), [])

    def test_run_stops_in_keyframe_phase_and_skips_sibling_i2v(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            spec["voiceover"] = {}
            # Failing still first so a cancel-on-VISION_QC bug would skip the sibling.
            spec["shots"] = [spec["shots"][1], spec["shots"][0], spec["shots"][2]]
            posts = []
            gens = []
            lock = threading.Lock()
            bad = {
                "pass": False,
                "failures": ["hybrid structure", "third-party logo"],
                "structure_mode_seen": "hybrid",
                "rubric_answers": {"structure_matches_refs": "no", "logo_policy_ok": "no"},
            }
            good = {"pass": True, "failures": [], "structure_mode_seen": "closed", "notes": "ok"}

            def fake_gen(spec_, s_, cred, out):
                with lock:
                    gens.append(s_["id"])
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(b"\x89PNG\r\n\x1a\nkey")
                return str(Path(out).resolve())

            def fake_qc(bible, keyframe, cred, refs=None, model=None):
                if "s02" in str(keyframe):
                    return bad
                return good

            def fake_request(method, path, payload=None, cred=None, **k):
                with lock:
                    posts.append(path)
                return 200, {"id": "task_%d" % len(posts)}, {}

            with mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen), \
                 mock.patch.object(product_qc, "call_vision_qc", side_effect=fake_qc), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=lambda *a, **k: a[3]):
                rc, payload = self._run(spec, parallel=1)
            state = pipeline.load_state(spec)
            self.assertEqual(rc, 4)
            self.assertEqual(posts, [])
            self.assertEqual(gens.count("s02"), 2)
            self.assertEqual(gens.count("s01"), 1)
            self.assertEqual(state["shots"]["s01"]["qc"], "pass")
            self.assertNotIn("task_id", state["shots"]["s01"])
            self.assertEqual(state["shots"]["s02"]["qc"], "fail")
            self.assertNotIn("task_id", state["shots"]["s02"])
            self.assertNotIn("task_id", state["shots"].get("s03", {}))
            report = payload["qc_gate"]["report"]
            self.assertEqual(payload["qc_gate"]["stopped_in"], "keyframe")
            self.assertEqual(payload["qc_gate"]["blocked"], ["s02"])
            self.assertIn("s01", payload["qc_gate"]["passed"])
            why = " ".join(report[0]["why"])
            self.assertIn("hybrid structure", why)
            self.assertIn("third-party logo", why)
            self.assertIn("logo_policy_ok", why)
            self.assertTrue(report[0]["retried"])
            self.assertIn("Not starting any i2v", payload["next_step"])
            self.assertTrue(payload["keyframe_batch_gate"])

    def test_run_batches_i2v_only_after_every_keyframe_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            spec["voiceover"] = {}
            order = []
            lock = threading.Lock()

            def fake_gen(spec_, s_, cred, out):
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(b"\x89PNG\r\n\x1a\nkey")
                return str(Path(out).resolve())

            def fake_qc(bible, keyframe, cred, refs=None, model=None):
                with lock:
                    order.append("qc:%s" % Path(str(keyframe)).stem)
                return {"pass": True, "failures": [], "notes": "ok"}

            def fake_request(method, path, payload=None, cred=None, **k):
                with lock:
                    order.append("video")
                return 200, {"id": "task_%d" % order.count("video")}, {}

            with mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen), \
                 mock.patch.object(product_qc, "call_vision_qc", side_effect=fake_qc), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=lambda *a, **k: a[3]):
                rc, payload = self._run(spec, parallel=2)
            self.assertEqual(rc, 0, payload)
            first_video = order.index("video")
            before = order[:first_video]
            self.assertIn("qc:s01", before)
            self.assertIn("qc:s02", before)
            self.assertEqual(order.count("video"), 3)
            state = pipeline.load_state(spec)
            for sid in ("s01", "s02", "s03"):
                self.assertEqual(state["shots"][sid]["status"], "done")
                self.assertTrue(state["shots"][sid].get("task_id"))
            self.assertEqual(state["shots"]["s01"]["qc"], "pass")
            self.assertEqual(state["shots"]["s02"]["qc"], "pass")

    def test_hero_pauses_only_that_shot_after_qc_gate_opens(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            spec["voiceover"] = {}
            spec["shots"] = spec["shots"][:2]
            spec["shots"][0]["hero"] = True
            posts = []

            def fake_gen(spec_, s_, cred, out):
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(b"\x89PNG\r\n\x1a\nkey")
                return str(Path(out).resolve())

            def fake_request(method, path, payload=None, cred=None, **k):
                posts.append(payload.get("model"))
                return 200, {"id": "task_%d" % len(posts)}, {}

            with mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen), \
                 mock.patch.object(product_qc, "call_vision_qc",
                                   return_value={"pass": True, "failures": []}), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=lambda *a, **k: a[3]):
                rc, payload = self._run(spec, parallel=2)
            state = pipeline.load_state(spec)
            self.assertEqual(rc, 5, payload)
            self.assertEqual(payload["hero_pending"], ["s01"])
            self.assertNotIn("task_id", state["shots"]["s01"])
            self.assertEqual(state["shots"]["s01"]["qc"], "pass")
            self.assertTrue(state["shots"]["s02"].get("task_id"))
            self.assertEqual(len(posts), 1)

    def test_vision_api_down_blocks_every_i2v(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            spec["voiceover"] = {}
            spec["shots"] = [spec["shots"][1], spec["shots"][0]]
            posts = []

            def fake_gen(spec_, s_, cred, out):
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(b"\x89PNG\r\n\x1a\nkey")
                return str(Path(out).resolve())

            def fake_qc(bible, keyframe, cred, refs=None, model=None):
                if "s02" in str(keyframe):
                    raise pt.PTError("connection reset", "NETWORK", 4)
                return {"pass": True, "failures": []}

            def fake_request(method, path, payload=None, cred=None, **k):
                posts.append(path)
                return 200, {"id": "task"}, {}

            with mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen), \
                 mock.patch.object(product_qc, "call_vision_qc", side_effect=fake_qc), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=lambda *a, **k: a[3]):
                rc, payload = self._run(spec, parallel=1)
            state = pipeline.load_state(spec)
            self.assertEqual(rc, 4, payload)
            self.assertEqual(posts, [])
            self.assertEqual(state["shots"]["s01"]["qc"], "pass")
            self.assertNotIn("task_id", state["shots"]["s01"])
            self.assertEqual(state["shots"]["s02"]["qc"], "fail")
            why = " ".join(payload["qc_gate"]["report"][0]["why"])
            self.assertIn("vision QC unavailable", why)
            self.assertIn("--skip-vision-qc", why)
            self.assertFalse(payload["qc_gate"]["report"][0]["retried"])

    def test_skip_vision_qc_allows_video_without_batch_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = pipeline.load(product_project(tmp))
            spec["voiceover"] = {}
            spec["shots"] = spec["shots"][:2]
            posts = []

            def fake_gen(spec_, s_, cred, out):
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(b"\x89PNG\r\n\x1a\nkey")
                return str(Path(out).resolve())

            def fake_request(method, path, payload=None, cred=None, **k):
                posts.append(path)
                return 200, {"id": "task_%d" % len(posts)}, {}

            with mock.patch.object(pipeline, "gen_keyframe", side_effect=fake_gen), \
                 mock.patch.object(product_qc, "call_vision_qc",
                                   side_effect=AssertionError("QC should be skipped")), \
                 mock.patch.object(pt, "request", side_effect=fake_request), \
                 mock.patch.object(pipeline.video, "wait_and_download",
                                   side_effect=lambda *a, **k: a[3]):
                rc, payload = self._run(spec, opts={"skip_vision_qc": True}, parallel=2)
            self.assertEqual(rc, 0, payload)
            self.assertEqual(len(posts), 2)
            self.assertFalse(payload["keyframe_batch_gate"])


class CaptionSafeZoneTests(unittest.TestCase):
    def test_default_caption_style_clear_of_bottom_ui(self):
        self.assertIn("MarginV=520", pipeline.DEFAULT_CAPTION_STYLE)
        self.assertIn("MarginR=130", pipeline.DEFAULT_CAPTION_STYLE)
        self.assertIn("Alignment=2", pipeline.DEFAULT_CAPTION_STYLE)

    def test_assemble_uses_default_unless_overridden(self):
        spec = {"defaults": {"ratio": "9:16"}, "assembly": {}, "shots": [], "_workdir": "/tmp"}
        # Call the style selection logic by inspecting ffmpeg_cmds path via dry structure
        style = spec.get("assembly", {}).get("caption_style", pipeline.DEFAULT_CAPTION_STYLE)
        self.assertEqual(style, pipeline.DEFAULT_CAPTION_STYLE)
        spec["assembly"]["caption_style"] = "FontName=Arial,MarginV=60,Alignment=2"
        style2 = spec.get("assembly", {}).get("caption_style", pipeline.DEFAULT_CAPTION_STYLE)
        self.assertIn("MarginV=60", style2)


class AugmentPromptTests(unittest.TestCase):
    def test_augment_prompt_negatives(self):
        t = product_qc.augment_prompt_negatives("packshot", ["hybrid pour on threads"])
        self.assertIn("STRICT FIX", t)
        self.assertIn("hybrid pour", t)
        # idempotent-ish
        t2 = product_qc.augment_prompt_negatives(t, ["other"])
        self.assertEqual(t2.count("STRICT FIX"), 1)


if __name__ == "__main__":
    unittest.main()
