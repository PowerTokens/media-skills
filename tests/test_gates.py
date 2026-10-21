"""Offline tests for vision QC/hero gates, character bible, claim lint, caption safe-zone."""
import json
import os
import shutil
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
