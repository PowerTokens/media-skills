#!/usr/bin/env python3
"""Copy tools/shared/*.py (and shared examples) into each skill so every skill folder is
self-contained (Codex $skill-installer / manual copy install one folder at a time).
Run after editing tools/shared or tools/examples. `--check` exits 1 if copies are stale (CI)."""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "tools" / "shared"
EXAMPLES = ROOT / "tools" / "examples"
SKILLS = ROOT / "plugins" / "powertokens-media" / "skills"
AUTH = ["pt_common.py", "pt_login.py", "pt_models.py"]
PIPE = AUTH + ["video.py", "image.py", "speech.py", "pipeline.py"]
NEEDS = {
    "powertokens-video": (AUTH + ["video.py"], []),
    "powertokens-image": (AUTH + ["image.py"], []),
    "powertokens-speech": (AUTH + ["speech.py"], []),
    "powertokens-model-routing": (AUTH + ["video.py"], []),
    "powertokens-prompting": ([], []),
    "powertokens-pipeline": (PIPE, ["product-ad.json", "short-drama.json", "ugc-ad.json", "bilingual-vo.json"]),
    "powertokens-product-ad": (PIPE, ["product-ad.json"]),
    "powertokens-ugc-ad": (PIPE, ["ugc-ad.json"]),
    "powertokens-short-drama": (PIPE, ["short-drama.json"]),
    "powertokens-social-variants": (PIPE, []),
    "powertokens-bilingual-voiceover": (PIPE, ["bilingual-vo.json"]),
    "powertokens-travel-poster": (AUTH + ["image.py"], []),
}
check = "--check" in sys.argv
stale = []
for skill, (scripts, examples) in NEEDS.items():
    for src_dir, names, sub in ((SHARED, scripts, "scripts"), (EXAMPLES, examples, "examples")):
        for name in names:
            src, dst = src_dir / name, SKILLS / skill / sub / name
            if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                stale.append(str(dst.relative_to(ROOT)))
                if not check:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
print(("stale: " if check else "synced: ") + (", ".join(stale) or "nothing"))
sys.exit(1 if check and stale else 0)
