#!/usr/bin/env python3
"""Product-consistency helpers for product ads (stdlib only).

  python3 product_qc.py validate-bible bible.json
  python3 product_qc.py constraints bible.json
  python3 product_qc.py vision-prompt bible.json --keyframe kf.png --ref product.jpg
  python3 product_qc.py parse-verdict '{"pass": false, "failures": ["hybrid lid"]}'
  python3 product_qc.py check-shotlist shots.json [--require]

No paid API calls unless you later wire chat yourself; this module builds prompts and
parses verdicts for offline tests and agent use. Vision model ids: see docs/product-consistency-qc.md
(default candidate MiniMax-M3; alts glm-5.2 / glm-5.1 / glm-5-turbo — confirm live + multimodal).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

# Chat model candidates for post-keyframe vision QC (confirm with pt_models.py; vision support unverified).
QC_CHAT_DEFAULT = "MiniMax-M3"
QC_CHAT_ALTS = ("glm-5.2", "glm-5.1", "glm-5-turbo", "MiniMax-M3")

BIBLE_REQUIRED = ("product_name", "immutable", "refs")
IMMUTABLE_KEYS = ("lid_modes", "forbid", "colors", "logos", "proportions")

RUBRIC_QUESTIONS = [
    "lid_mechanism_matches_refs",
    "no_hybrid_or_invented_opening",
    "colors_finish_ok",
    "logo_policy_ok",
    "proportions_silhouette_ok",
]


def load_bible(path):
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise pt.PTError("Cannot read product bible %s: %s" % (path, exc), "BAD_REQUEST", 3)
    errs = validate_bible(data)
    if errs:
        raise pt.PTError("Product bible invalid: " + "; ".join(errs), "BAD_REQUEST", 3)
    data["_path"] = str(p.resolve())
    return data


def validate_bible(data):
    """Return list of schema errors (empty = ok)."""
    errs = []
    if not isinstance(data, dict):
        return ["bible must be a JSON object"]
    for k in BIBLE_REQUIRED:
        if k not in data:
            errs.append("missing %s" % k)
    imm = data.get("immutable") or {}
    if not isinstance(imm, dict):
        errs.append("immutable must be an object")
    else:
        modes = imm.get("lid_modes")
        if not modes or not isinstance(modes, list):
            errs.append("immutable.lid_modes must be a non-empty list")
        else:
            for i, m in enumerate(modes):
                if not isinstance(m, dict) or not m.get("id") or not m.get("how"):
                    errs.append("immutable.lid_modes[%d] needs id and how" % i)
        forbid = imm.get("forbid")
        if not isinstance(forbid, list) or not forbid:
            errs.append("immutable.forbid must be a non-empty list of strings")
        for key in ("colors", "proportions"):
            if not imm.get(key):
                errs.append("immutable.%s is required" % key)
        if "logos" not in imm:
            errs.append("immutable.logos is required (use null/'none' if no logo)")
    refs = data.get("refs") or []
    if not isinstance(refs, list) or not (1 <= len(refs) <= 3):
        errs.append("refs must be a list of 1–3 paths/URLs")
    else:
        for i, r in enumerate(refs):
            if not isinstance(r, dict) or not r.get("path"):
                errs.append("refs[%d].path is required" % i)
    return errs


def constraints_block(bible):
    """English hard-constraint paragraph to append to Seedream / i2v prompts."""
    imm = bible["immutable"]
    modes = "; ".join("%s — %s" % (m["id"], m["how"]) for m in imm["lid_modes"])
    forbid = "; ".join(imm["forbid"])
    logos = imm.get("logos")
    logo_line = "Logos: %s." % (logos if logos not in (None, "none") else "none — do not invent logos or wordmarks")
    lines = [
        "PRODUCT LOCK (must obey):",
        "Product: %s." % bible.get("product_name", "product"),
        "Real opening modes only: %s." % modes,
        "Colors/finish: %s." % imm["colors"],
        "Proportions: %s." % imm["proportions"],
        logo_line,
        "Forbidden: %s." % forbid,
        "Keep the product identical to the reference photos; do not redesign the mouth, lid, or threads.",
    ]
    if bible.get("notes"):
        lines.append(str(bible["notes"]).strip())
    return " ".join(lines)


def vision_messages(bible, keyframe, refs=None, model=None):
    """OpenAI-style chat messages for a structured yes/no product QC (multimodal)."""
    refs = refs or [r["path"] for r in bible.get("refs", [])]
    imm = bible["immutable"]
    rubric = [{"id": q, "ask": q.replace("_", " ") + "?"} for q in RUBRIC_QUESTIONS]
    system = (
        "You are a strict product-consistency inspector for ads. "
        "Compare the KEYFRAME image to the PRODUCT BIBLE and REFERENCE images. "
        "Reply with JSON only, no markdown."
    )
    user_text = {
        "task": "product_keyframe_qc",
        "product_name": bible.get("product_name"),
        "immutable": imm,
        "rubric": rubric,
        "response_schema": {
            "pass": "bool — true only if every rubric item is clearly satisfied",
            "failures": "string[] — short codes or phrases for each failed item",
            "lid_mode_seen": "string — which bible lid mode id is shown, or 'closed', or 'unknown'",
            "rubric_answers": {q: "yes|no|unclear" for q in RUBRIC_QUESTIONS},
            "notes": "string — one short sentence",
        },
        "instructions": [
            "Fail if the lid/opening is a hybrid not listed in lid_modes.",
            "Fail if any forbid[] rule is violated.",
            "If unsure, set pass=false and put 'unclear' in failures.",
        ],
    }
    content = [{"type": "text", "text": json.dumps(user_text, ensure_ascii=False)}]
    for label, path in [("REFERENCE", p) for p in refs] + [("KEYFRAME", keyframe)]:
        if not path:
            continue
        content.append({"type": "text", "text": "%s image follows." % label})
        # Caller / agent attaches local files as data URLs or uploaded URLs; we pass a placeholder ref.
        content.append({"type": "image_url", "image_url": {"url": _image_ref(path)}})
    return {
        "model": model or bible.get("qc_model") or QC_CHAT_DEFAULT,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }


def _image_ref(path):
    p = str(path)
    if p.startswith(("http://", "https://", "data:")):
        return p
    # Offline-safe: do not base64 large files here; agent/pipeline may replace with data URL.
    return "file://%s" % Path(p).resolve()


def parse_verdict(raw):
    """Parse model output into {pass, failures, ...}. Accepts dict or JSON/text with a JSON object."""
    if isinstance(raw, dict):
        data = raw
    else:
        text = str(raw).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            data = json.loads(text)
        except ValueError:
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                raise pt.PTError("Verdict is not JSON: %s" % text[:200], "BAD_REQUEST", 3)
            data = json.loads(m.group(0))
    if "pass" not in data:
        raise pt.PTError("Verdict missing pass field", "BAD_REQUEST", 3)
    passed = bool(data["pass"])
    failures = data.get("failures") or []
    if not isinstance(failures, list):
        failures = [str(failures)]
    if passed and failures:
        # Prefer explicit failures: treat as fail.
        passed = False
    return {
        "pass": passed,
        "failures": [str(f) for f in failures],
        "lid_mode_seen": data.get("lid_mode_seen", "unknown"),
        "rubric_answers": data.get("rubric_answers") or {},
        "notes": data.get("notes") or "",
    }


def check_shotlist_bible(spec_or_path, require=False):
    """Validate product_bible reference on a shot list. Returns (ok, errors, bible_or_none)."""
    if isinstance(spec_or_path, (str, Path)):
        path = Path(spec_or_path)
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return False, ["cannot read shot list: %s" % exc], None
        base = path.resolve().parent
    else:
        spec = spec_or_path
        base = Path(spec.get("_base") or ".")
    kind = (spec.get("kind") or "").lower()
    need = require or kind in ("product-ad", "product_ad", "product")
    bible_rel = spec.get("product_bible")
    errs = []
    if need and not bible_rel:
        errs.append("product-ad shot list requires product_bible (JSON lock sheet); see docs/product-consistency-qc.md")
        return False, errs, None
    if not bible_rel:
        return True, [], None
    bpath = Path(bible_rel) if Path(bible_rel).is_absolute() else base / bible_rel
    if not bpath.is_file():
        errs.append("product_bible file not found: %s" % bpath)
        return False, errs, None
    try:
        bible = load_bible(bpath)
    except pt.PTError as exc:
        return False, [str(exc)], None
    return True, [], bible


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate-bible", help="schema-check a product bible JSON")
    p.add_argument("bible")

    p = sub.add_parser("constraints", help="print prompt hard-constraint block")
    p.add_argument("bible")

    p = sub.add_parser("vision-prompt", help="print chat body for keyframe QC (no API call)")
    p.add_argument("bible")
    p.add_argument("--keyframe", required=True)
    p.add_argument("--ref", action="append", default=[])
    p.add_argument("--model", default="")

    p = sub.add_parser("parse-verdict", help="parse a model JSON verdict (offline)")
    p.add_argument("raw")

    p = sub.add_parser("check-shotlist", help="require/validate product_bible on a shot list")
    p.add_argument("shots")
    p.add_argument("--require", action="store_true")

    a = ap.parse_args()
    if a.cmd == "validate-bible":
        b = load_bible(a.bible)
        pt.emit({"ok": True, "product_name": b["product_name"], "lid_modes": [m["id"] for m in b["immutable"]["lid_modes"]],
                 "refs": len(b["refs"])})
    elif a.cmd == "constraints":
        b = load_bible(a.bible)
        text = constraints_block(b)
        pt.emit({"ok": True, "constraints": text})
    elif a.cmd == "vision-prompt":
        b = load_bible(a.bible)
        body = vision_messages(b, a.keyframe, a.ref or None, a.model or None)
        pt.emit({"ok": True, "chat_path": "/v1/chat/completions", "body": body,
                 "note": "Vision/multimodal support for this model id is not verified in-repo; confirm before spending."})
    elif a.cmd == "parse-verdict":
        v = parse_verdict(a.raw)
        pt.emit({"ok": True, "verdict": v})
    elif a.cmd == "check-shotlist":
        ok, errs, bible = check_shotlist_bible(a.shots, require=a.require)
        pt.emit({"ok": ok, "errors": errs,
                 "product_name": (bible or {}).get("product_name"),
                 "qc_model_default": QC_CHAT_DEFAULT, "qc_model_alts": list(QC_CHAT_ALTS)})
        if not ok:
            return 2
    return 0


if __name__ == "__main__":
    pt.run(main)
