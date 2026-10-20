#!/usr/bin/env python3
"""Copy tools/shared/*.py into each skill's scripts/ so every skill folder is self-contained
(needed for Codex $skill-installer / manual copy, which install one skill folder at a time).
Run after editing anything in tools/shared. `--check` exits 1 if copies are stale (for CI)."""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "tools" / "shared"
SKILLS = ROOT / "plugins" / "powertokens-media" / "skills"
NEEDS = {
    "powertokens-video": ["pt_common.py", "pt_login.py", "pt_models.py", "video.py"],
    "powertokens-image": ["pt_common.py", "pt_login.py", "pt_models.py", "image.py"],
    "powertokens-speech": ["pt_common.py", "pt_login.py", "pt_models.py", "speech.py"],
    "powertokens-ad-video": ["pt_common.py", "pt_login.py", "pt_models.py", "video.py", "image.py", "speech.py"],
}
check = "--check" in sys.argv
stale = []
for skill, files in NEEDS.items():
    dest = SKILLS / skill / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for name in files:
        src, dst = SHARED / name, dest / name
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            stale.append(str(dst.relative_to(ROOT)))
            if not check:
                shutil.copy2(src, dst)
print(("stale: " if check else "synced: ") + (", ".join(stale) or "nothing"))
sys.exit(1 if check and stale else 0)
