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
SNEAKER = ROOT / "tools" / "examples" / "product-bible.sneaker.json"
BAG = ROOT / "tools" / "examples" / "product-bible.bag.json"


class ProductQcTests(unittest.TestCase):
    def test_thermos_bible_schema(self):
        b = product_qc.load_bible(BIBLE)
        self.assertEqual(b["product_name"].split()[0], "North")
        self.assertEqual(b["category"], "drinkware")
        self.assertIn("dual-lid", b["subtype"])
        self.assertGreaterEqual(len(b["immutable"]["parts"]), 2)
        roles = {p["role"] for p in b["immutable"]["parts"]}
        self.assertIn("closure", roles)
        self.assertTrue(any("screw" in f.lower() or "thread" in f.lower()
                            for f in b["immutable"]["forbid"]))

    def test_sneaker_bible_schema(self):
        b = product_qc.load_bible(SNEAKER)
        self.assertEqual(b["category"], "footwear")
        ids = [p["id"] for p in b["immutable"]["parts"]]
        self.assertIn("outsole", ids)
        self.assertIn("lacing", ids)
        text = product_qc.constraints_block(b)
        self.assertIn("Structure modes", text)
        self.assertIn("outsole", text.lower())
        self.assertNotIn("lid modes", text.lower())

    def test_bag_bible_schema(self):
        b = product_qc.load_bible(BAG)
        self.assertEqual(b["category"], "bag")
        self.assertTrue(any(p["id"] == "top_zipper" for p in b["immutable"]["parts"]))

    def test_validate_bible_rejects_empty_parts(self):
        bad = {
            "product_name": "x",
            "category": "drinkware",
            "subtype": "bottle",
            "immutable": {
                "parts": [],
                "forbid": ["a"],
                "colors": "c",
                "logos": "none",
                "proportions": "p",
            },
            "refs": [{"path": "a.jpg"}],
        }
        errs = product_qc.validate_bible(bad)
        self.assertTrue(any("parts" in e for e in errs))

    def test_validate_bible_requires_category_subtype(self):
        bad = {
            "product_name": "x",
            "immutable": {
                "parts": [{"id": "body", "role": "body", "how": "cylinder"}],
                "forbid": ["a"],
                "colors": "c",
                "logos": "none",
                "proportions": "p",
            },
            "refs": [{"path": "a.jpg"}],
        }
        errs = product_qc.validate_bible(bad)
        self.assertTrue(any("category" in e for e in errs))
        self.assertTrue(any("subtype" in e for e in errs))

    def test_legacy_lid_modes_loads(self):
        legacy = {
            "product_name": "Legacy Bottle",
            "category": "drinkware",
            "subtype": "screw bottle",
            "immutable": {
                "lid_modes": [
                    {"id": "screw_lid", "how": "Full screw lid on threads."},
                ],
                "forbid": ["do not invent a flip spout on threads"],
                "colors": "black",
                "logos": "none",
                "proportions": "tall",
            },
            "refs": [{"path": "a.jpg", "shows": "hero"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.json"
            path.write_text(json.dumps(legacy), encoding="utf-8")
            b = product_qc.load_bible(path)
            self.assertEqual(b["immutable"]["parts"][0]["id"], "screw_lid")
            self.assertEqual(b["immutable"]["parts"][0]["role"], "closure")
            self.assertEqual(b["immutable"]["structure"][0]["id"], "screw_lid")

    def test_legacy_structure_alias_loads(self):
        data = {
            "product_name": "Device X",
            "category": "consumer_electronics",
            "subtype": "phone",
            "immutable": {
                "structure": [
                    {"id": "ports", "how": "USB-C only on bottom edge as in refs."},
                ],
                "forbid": ["do not invent a headphone jack"],
                "colors": "graphite",
                "logos": "none",
                "proportions": "slab phone",
            },
            "refs": [{"path": "phone.jpg"}],
        }
        errs = product_qc.validate_bible(data)
        self.assertEqual(errs, [])
        norm = product_qc.normalize_bible(data)
        self.assertEqual(norm["immutable"]["parts"][0]["role"], "structure")

    def test_constraints_forbid_hybrid_generic(self):
        text = product_qc.constraints_block(product_qc.load_bible(BIBLE))
        self.assertIn("PRODUCT LOCK", text)
        self.assertIn("Structure modes", text)
        self.assertIn("screw", text.lower())
        self.assertIn("Forbidden", text)
        self.assertIn("do not invent, omit, or hybridize parts", text)
        self.assertNotIn("do not redesign the mouth, lid, or threads", text)

    def test_vision_prompt_structure(self):
        body = product_qc.vision_messages(product_qc.load_bible(BIBLE), "kf.png", ["product.jpg"])
        self.assertEqual(body["model"], "MiniMax-M3")
        self.assertEqual(body["messages"][1]["role"], "user")
        types = [c["type"] for c in body["messages"][1]["content"]]
        self.assertIn("image_url", types)
        payload = json.loads(body["messages"][1]["content"][0]["text"])
        self.assertIn("structure_mode_seen", payload["response_schema"])
        self.assertIn("structure_matches_refs", [r["id"] for r in payload["rubric"]])
        self.assertTrue(any("hybrid" in i.lower() for i in payload["instructions"]))

    def test_parse_verdict_pass_and_fail(self):
        ok = product_qc.parse_verdict(
            '{"pass": true, "failures": [], "structure_mode_seen": "closed"}')
        self.assertTrue(ok["pass"])
        self.assertEqual(ok["structure_mode_seen"], "closed")
        bad = product_qc.parse_verdict(
            '```json\n{"pass": true, "failures": ["hybrid part"], "structure_mode_seen": "unknown"}\n```')
        self.assertFalse(bad["pass"])
        self.assertIn("hybrid", bad["failures"][0])

    def test_parse_verdict_accepts_legacy_lid_mode_seen(self):
        v = product_qc.parse_verdict(
            '{"pass": true, "failures": [], "lid_mode_seen": "screw_lid"}')
        self.assertEqual(v["structure_mode_seen"], "screw_lid")

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
