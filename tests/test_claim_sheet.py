import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "shared"))
import claim_sheet  # noqa: E402

EXAMPLE = ROOT / "tools" / "examples" / "claim-sheet.json"


class ClaimSheetTest(unittest.TestCase):
    def test_example_validates(self):
        data = claim_sheet.load(EXAMPLE)
        self.assertEqual(claim_sheet.validate(data), [])

    def test_table_nonempty(self):
        data = claim_sheet.load(EXAMPLE)
        md = claim_sheet.table(data)
        self.assertIn("c1", md)
        self.assertIn("Keeps coffee hot", md)

    def test_approve(self):
        data = claim_sheet.load(EXAMPLE)
        data = claim_sheet.approve(data, ["c1", "c2"])
        self.assertEqual(data["claims"][0]["status"], "approved")
        self.assertEqual(data["status"], "approved")


if __name__ == "__main__":
    unittest.main()
