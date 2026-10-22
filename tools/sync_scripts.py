#!/usr/bin/env python3
"""Copy tools/shared/*.py (and shared examples) into each skill so every skill folder is
self-contained (Codex $skill-installer / manual copy install one folder at a time).
Run after editing tools/shared or tools/examples. `--check` exits 1 if copies are stale (CI).

Skill-local patches are applied after the shared file is read and are part of `--check`.
Other skills keep the shared Wan 3.0 video default.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "tools" / "shared"
EXAMPLES = ROOT / "tools" / "examples"
SKILLS = ROOT / "plugins" / "powertokens-media" / "skills"
AUTH = ["pt_common.py", "pt_login.py", "pt_models.py"]
PIPE = AUTH + ["video.py", "image.py", "speech.py", "pipeline.py"]
FINISH = ["captions.py", "finish.py"]
QC = ["product_qc.py", "character_qc.py", "claim_lint.py", "claim_sheet.py"]
NEEDS = {
    "powertokens-video": (AUTH + ["video.py"], []),
    "powertokens-image": (AUTH + ["image.py"], []),
    "powertokens-speech": (AUTH + ["speech.py"], []),
    "powertokens-model-routing": (AUTH + ["video.py"], []),
    "powertokens-prompting": ([], []),
    "powertokens-pipeline": (PIPE + FINISH + QC, ["product-ad.json", "northloop-ad.json", "claim-sheet.json", "product-bible.thermos.json", "product-bible.sneaker.json", "product-bible.bag.json", "short-drama.json", "ugc-ad.json", "bilingual-vo.json", "character-bible.ning.json"]),
    "powertokens-product-ad": (PIPE + FINISH + QC, ["product-ad.json", "northloop-ad.json", "claim-sheet.json", "product-bible.thermos.json", "product-bible.sneaker.json", "product-bible.bag.json"]),
    "powertokens-ugc-ad": (PIPE + FINISH + QC, ["ugc-ad.json", "character-bible.ning.json"]),
    "powertokens-short-drama": (PIPE + FINISH + QC, ["short-drama.json", "character-bible.ning.json"]),
    "powertokens-social-variants": (PIPE + FINISH + QC, []),
    "powertokens-bilingual-voiceover": (PIPE + FINISH + QC, ["bilingual-vo.json"]),
    "powertokens-travel-poster": (AUTH + ["image.py"], []),
    "powertokens-product-qc": (AUTH + ["image.py", "video.py", "speech.py", "pipeline.py"] + QC,
                               ["product-ad.json", "product-bible.thermos.json", "product-bible.sneaker.json", "product-bible.bag.json"]),
}
# Product-ad drafts default to Seedance 2.0 Mini when a shot omits `model`.
# The shared video.py stays on Wan so video / pipeline / UGC / drama skills do not change.
PATCHES = {
    "powertokens-product-ad": {
        "scripts/video.py": [
            (
                'DEFAULT_MODEL = "wan3.0-video"',
                'DEFAULT_MODEL = "dreamina-seedance-2-0-mini-260615"',
            ),
        ],
    },
}

def transform(skill, sub, name, data):
    rel = "%s/%s" % (sub, name)
    for old, new in PATCHES.get(skill, {}).get(rel, []):
        raw_old, raw_new = old.encode(), new.encode()
        found = data.count(raw_old)
        if found != 1:
            raise SystemExit("patch anchor for %s %s matched %d times" % (skill, rel, found))
        data = data.replace(raw_old, raw_new, 1)
    return data


check = "--check" in sys.argv
stale = []
for skill, (scripts, examples) in NEEDS.items():
    for src_dir, names, sub in ((SHARED, scripts, "scripts"), (EXAMPLES, examples, "examples")):
        for name in names:
            src, dst = src_dir / name, SKILLS / skill / sub / name
            expected = transform(skill, sub, name, src.read_bytes())
            current = dst.read_bytes() if dst.exists() else b""
            if current != expected:
                stale.append(str(dst.relative_to(ROOT)))
                if not check:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(expected)
print(("stale: " if check else "synced: ") + (", ".join(stale) or "nothing"))
sys.exit(1 if check and stale else 0)
