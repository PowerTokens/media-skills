"""Offline product_qc schema / parse / shotlist gate tests (no network)."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("POWERTOKENS_CONFIG_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "tools" / "shared"))
import pt_common as pt  # noqa: E402
import product_qc  # noqa: E402
import pipeline  # noqa: E402

BIBLE = ROOT / "tools" / "examples" / "product-bible.thermos.json"


class ProductQcTests(unittest.TestCase):
    def test_thermos_bible_schema(self):
        b = product_qc.load_bible(BIBLE)
        self.assertEqual(b["product_name"].split()[0], "North")
        self.assertGreaterEqual(len(b["immutable"]["lid_modes"]), 2)
        self.assertTrue(any("screw" in f.lower() or "thread" in f.lower()
                            for f in b["immutable"]["forbid"]))

    def test_validate_bible_rejects_empty_modes(self):
        bad = {"product_name": "x", "immutable": {"lid_modes": [], "forbid": ["a"],
               "colors": "c", "logos": "none", "proportions": "p"}, "refs": [{"path": "a.jpg"}]}
        errs = product_qc.validate_bible(bad)
        self.assertTrue(any("lid_modes" in e for e in errs))

    def test_constraints_forbid_hybrid(self):
        text = product_qc.constraints_block(product_qc.load_bible(BIBLE))
        self.assertIn("PRODUCT LOCK", text)
        self.assertIn("screw", text.lower())
        self.assertIn("Forbidden", text)

    def test_vision_prompt_structure(self):
        body = product_qc.vision_messages(product_qc.load_bible(BIBLE), "kf.png", ["product.jpg"])
        self.assertEqual(body["model"], "MiniMax-M3")
        self.assertEqual(body["messages"][1]["role"], "user")
        types = [c["type"] for c in body["messages"][1]["content"]]
        self.assertIn("image_url", types)

    def test_parse_verdict_pass_and_fail(self):
        ok = product_qc.parse_verdict('{"pass": true, "failures": [], "lid_mode_seen": "closed"}')
        self.assertTrue(ok["pass"])
        bad = product_qc.parse_verdict(
            '```json\n{"pass": true, "failures": ["hybrid lid on threads"], "lid_mode_seen": "unknown"}\n```')
        self.assertFalse(bad["pass"])
        self.assertIn("hybrid", bad["failures"][0])

    def test_parse_verdict_missing_pass(self):
        with self.assertRaises(pt.PTError):
            product_qc.parse_verdict('{"failures": []}')

    def test_shotlist_gate_requires_bible_for_product_ad(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            shots = {"kind": "product-ad", "shots": [{"id": "s01", "prompt": "x", "model": "wan3.0-video",
                                                     "duration": 4, "resolution": "720p", "ratio": "9:16"}]}
            (d / "shots.json").write_text(json.dumps(shots))
            ok, errs, _ = product_qc.check_shotlist_bible(d / "shots.json")
            self.assertFalse(ok)
            self.assertTrue(any("product_bible" in e for e in errs))

    def test_pipeline_validate_with_bible(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "product.png").write_bytes(b"\x89PNG")
            shutil.copy(ROOT / "tools" / "examples" / "product-ad.json", d / "product-ad.json")
            shutil.copy(BIBLE, d / "product-bible.thermos.json")
            spec = pipeline.load(str(d / "product-ad.json"))
            self.assertEqual(pipeline.validate(spec), [])

    def test_pipeline_validate_refuses_product_ad_without_bible(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "product.png").write_bytes(b"\x89PNG")
            shots = json.loads((ROOT / "tools" / "examples" / "product-ad.json").read_text())
            shots.pop("product_bible", None)
            (d / "no-bible.json").write_text(json.dumps(shots))
            errs = pipeline.validate(pipeline.load(str(d / "no-bible.json")))
            self.assertTrue(any("product_bible" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
