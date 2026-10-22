#!/usr/bin/env python3
"""Product-consistency helpers for product ads (stdlib only).

  python3 product_qc.py validate-bible bible.json
  python3 product_qc.py constraints bible.json
  python3 product_qc.py vision-prompt bible.json --keyframe kf.png --ref product.jpg
  python3 product_qc.py parse-verdict '{"pass": false, "failures": ["hybrid part"]}'
  python3 product_qc.py check-shotlist shots.json [--require]

No paid API calls unless you later wire chat yourself; this module builds prompts and
parses verdicts for offline tests and agent use. Vision model ids: see docs/product-consistency-qc.md
(default candidate MiniMax-M3; alts glm-5.2 / glm-5.1 / glm-5-turbo — confirm live + multimodal).

Agent bible workflow (required order):
  1. category（商品大类）
  2. subtype（具体分型）
  3. immutable.parts BOM（组成拆解）
  4. then forbid / colors / logos / proportions / refs
     Always include DEFAULT_THIRD_PARTY_FORBID in forbid[] (third-party brand props).
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

# Top-level required for a full product bible (lock sheet).
BIBLE_REQUIRED = ("product_name", "category", "subtype", "immutable", "refs")
# Canonical immutable composition field is `parts`; structure/lid_modes are legacy aliases.
IMMUTABLE_REQUIRED = ("forbid", "colors", "logos", "proportions")
PART_REQUIRED = ("id", "role", "how")

RUBRIC_QUESTIONS = [
    "structure_matches_refs",
    "no_hybrid_or_invented_parts",
    "colors_finish_ok",
    "logo_policy_ok",
    "proportions_silhouette_ok",
]

# Operational only — no legal-advice wording. Copy this into immutable.forbid when drafting a bible.
DEFAULT_THIRD_PARTY_FORBID = (
    "no third-party logos, wordmarks, or brand-identifiable devices "
    "(MacBook, iPhone, Apple logo, Nike swoosh, Starbucks cup mark, Amazon smile, "
    "Google/Microsoft hardware logos) unless the advertised SKU is that brand "
    "or the user explicitly approved it"
)

# Always appended to Seedream / i2v prompts (pipeline injects constraints_block).
THIRD_PARTY_PROP_LOCK = (
    "Third-party brand props: no third-party logos, wordmarks, packaging, or "
    "brand-identifiable devices (Apple MacBook / iPhone / logo, Nike swoosh, "
    "Starbucks cup mark, Amazon smile, Google/Microsoft hardware logos) unless "
    "the advertised SKU is that brand or the user explicitly approved showing it. "
    "Generic unbranded props only (plain silver laptop with no logo or chin text, "
    "blank phone bezel, plain mug)."
)

LOGO_POLICY_ASK = (
    "logo policy ok? Answer no if logos or wordmarks violate immutable.logos "
    "(invented marks, or a required own mark missing), or if the frame shows a "
    "recognizable third-party trademark, wordmark, packaging, or brand-identifiable "
    "device (Apple MacBook / iPhone / logo, Nike swoosh, Starbucks cup mark, "
    "Amazon smile, Google/Microsoft hardware logos) unless that brand is the "
    "advertised SKU or explicitly allowed. Generic unbranded props are yes "
    "(plain silver laptop with no logo or chin text, blank phone bezel, plain mug)."
)


def _is_third_party_forbid(text):
    low = str(text).lower()
    return "third-party" in low and (
        "logo" in low or "wordmark" in low or "brand-identifiable" in low
    )


def _rubric_ask(qid):
    if qid == "logo_policy_ok":
        return LOGO_POLICY_ASK
    return qid.replace("_", " ") + "?"


def _rubric_is_no(value):
    if isinstance(value, bool):
        return value is False
    if value is None:
        return False
    token = str(value).strip().lower().rstrip(".")
    return token in ("no", "fail", "false")


def _as_part(item, default_role="part"):
    """Normalize a dict (or legacy lid_modes entry) into a parts BOM row."""
    if not isinstance(item, dict):
        return None
    pid = item.get("id")
    how = item.get("how")
    if not pid or not how:
        return None
    role = item.get("role") or default_role
    out = {"id": str(pid), "role": str(role), "how": str(how)}
    if item.get("states"):
        out["states"] = list(item["states"]) if isinstance(item["states"], list) else [str(item["states"])]
    return out


def normalize_immutable(imm):
    """Return a shallow-copied immutable with canonical `parts` filled.

    Preference order for composition source:
      1. immutable.parts (canonical BOM)
      2. immutable.structure (alias: list of {id, how} → parts with role=structure)
      3. immutable.lid_modes (legacy → parts with role=closure)
    Always writes `parts` on the returned dict; keeps structure/lid_modes if present.
    """
    if not isinstance(imm, dict):
        return imm
    out = dict(imm)
    parts = None
    raw_parts = out.get("parts")
    if isinstance(raw_parts, list) and raw_parts:
        parts = []
        for item in raw_parts:
            p = _as_part(item, default_role=item.get("role") if isinstance(item, dict) else "part")
            if p:
                parts.append(p)
    if not parts:
        raw_struct = out.get("structure")
        if isinstance(raw_struct, list) and raw_struct:
            parts = []
            for item in raw_struct:
                p = _as_part(item, default_role="structure")
                if p:
                    parts.append(p)
    if not parts:
        raw_lids = out.get("lid_modes")
        if isinstance(raw_lids, list) and raw_lids:
            parts = []
            for item in raw_lids:
                p = _as_part(item, default_role="closure")
                if p:
                    parts.append(p)
    if parts:
        out["parts"] = parts
        # Keep a derived structure list for emitters that want id/how only.
        out["structure"] = [{"id": p["id"], "how": p["how"]} for p in parts]
    return out


def normalize_bible(data):
    """Shallow-copy bible with immutable normalized to parts-canonical form."""
    if not isinstance(data, dict):
        return data
    out = dict(data)
    if isinstance(out.get("immutable"), dict):
        out["immutable"] = normalize_immutable(out["immutable"])
    return out


def load_bible(path):
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise pt.PTError("Cannot read product bible %s: %s" % (path, exc), "BAD_REQUEST", 3)
    data = normalize_bible(data)
    errs = validate_bible(data)
    if errs:
        raise pt.PTError("Product bible invalid: " + "; ".join(errs), "BAD_REQUEST", 3)
    data["_path"] = str(p.resolve())
    return data


def validate_bible(data):
    """Return list of schema errors (empty = ok). Accepts pre- or post-normalize input."""
    errs = []
    if not isinstance(data, dict):
        return ["bible must be a JSON object"]
    # Normalize a working copy so legacy lid_modes/structure validate as parts.
    work = normalize_bible(data)
    for k in BIBLE_REQUIRED:
        if k not in work or work.get(k) in (None, ""):
            errs.append("missing %s" % k)
    imm = work.get("immutable") or {}
    if not isinstance(imm, dict):
        errs.append("immutable must be an object")
        return errs
    parts = imm.get("parts")
    if not parts or not isinstance(parts, list):
        errs.append(
            "immutable.parts must be a non-empty list of {id, role, how} "
            "(or provide legacy immutable.structure / immutable.lid_modes)"
        )
    else:
        for i, m in enumerate(parts):
            if not isinstance(m, dict):
                errs.append("immutable.parts[%d] must be an object" % i)
                continue
            for key in PART_REQUIRED:
                if not m.get(key):
                    errs.append("immutable.parts[%d] needs %s" % (i, key))
            if "states" in m and m["states"] is not None and not isinstance(m["states"], list):
                errs.append("immutable.parts[%d].states must be a list when present" % i)
    forbid = imm.get("forbid")
    if not isinstance(forbid, list) or not forbid:
        errs.append("immutable.forbid must be a non-empty list of strings")
    elif any(not isinstance(f, str) or not f.strip() for f in forbid):
        errs.append("immutable.forbid entries must be non-empty strings")
    for key in ("colors", "proportions"):
        if not imm.get(key):
            errs.append("immutable.%s is required" % key)
    if "logos" not in imm:
        errs.append("immutable.logos is required (use null/'none' if no logo)")
    refs = work.get("refs") or []
    if not isinstance(refs, list) or not (1 <= len(refs) <= 5):
        errs.append(
            "refs must be a list of 1–5 {path, shows?, kind?, part?} objects"
        )
    else:
        for i, r in enumerate(refs):
            if not isinstance(r, dict) or not r.get("path"):
                errs.append("refs[%d].path is required" % i)
                continue
            kind = r.get("kind")
            if kind is not None and kind not in ("hero", "part_detail"):
                errs.append(
                    "refs[%d].kind must be 'hero' or 'part_detail' when set" % i
                )
            if "part" in r and r.get("part") is not None:
                if not isinstance(r.get("part"), str) or not str(r.get("part")).strip():
                    errs.append("refs[%d].part must be a non-empty string when set" % i)
            if kind == "part_detail" and not (isinstance(r.get("part"), str) and r.get("part").strip()):
                errs.append("refs[%d] kind=part_detail requires part=<parts[].id>" % i)
    mmr = work.get("must_match_refs")
    if mmr is not None and not isinstance(mmr, list):
        errs.append("must_match_refs must be a list of strings when present")
    return errs


def constraints_block(bible):
    """English hard-constraint paragraph to append to Seedream / i2v prompts."""
    bible = normalize_bible(bible)
    imm = bible["immutable"]
    parts = imm.get("parts") or []
    part_lines = "; ".join(
        "%s [%s] — %s%s" % (
            p["id"],
            p.get("role", "part"),
            p["how"],
            (" (states: %s)" % "/".join(p["states"])) if p.get("states") else "",
        )
        for p in parts
    )
    # State the third-party prop lock once (canonical sentence), even when forbid[] already has it.
    forbid_items = [f for f in imm["forbid"] if not _is_third_party_forbid(f)]
    logos = imm.get("logos")
    logo_line = "Logos: %s." % (logos if logos not in (None, "none") else "none — do not invent logos or wordmarks")
    cat = bible.get("category") or "product"
    subtype = bible.get("subtype") or ""
    lines = [
        "PRODUCT LOCK (must obey):",
        "Product: %s." % bible.get("product_name", "product"),
        "Category/subtype: %s%s." % (cat, (" / " + subtype) if subtype else ""),
        "Structure modes (parts BOM): %s." % part_lines,
        "Colors/finish: %s." % imm["colors"],
        "Proportions: %s." % imm["proportions"],
        logo_line,
    ]
    if forbid_items:
        lines.append("Forbidden: %s." % "; ".join(forbid_items))
    lines.append(THIRD_PARTY_PROP_LOCK)
    lines.append(
        "Keep the product identical to the reference photos; do not invent, omit, or hybridize parts listed in structure; do not redesign critical geometry."
    )
    lines.append(
        "Part-detail refs (kind=part_detail or shows a single BOM part): use them ONLY to correct that named part; keep body height, silhouette, proportions, colors/finish, and scene framing identical to the hero product ref — unify the part onto the original product; do not shorten, stubby-fy, or restyle the whole SKU from a part-only crop."
    )
    mmr = bible.get("must_match_refs")
    if mmr:
        lines.append("Must match refs exactly for: %s." % ", ".join(str(x) for x in mmr))
    part_detail_ids = []
    for r in bible.get("refs") or []:
        if not isinstance(r, dict):
            continue
        if r.get("kind") == "part_detail" or r.get("part"):
            pid = r.get("part") or r.get("shows") or r.get("path")
            if pid:
                part_detail_ids.append(str(pid))
    if part_detail_ids:
        lines.append(
            "Part-detail ref parts in use: %s." % ", ".join(part_detail_ids)
        )
    if bible.get("notes"):
        lines.append(str(bible["notes"]).strip())
    return " ".join(lines)


def vision_messages(bible, keyframe, refs=None, model=None):
    """OpenAI-style chat messages for a structured yes/no product QC (multimodal)."""
    bible = normalize_bible(bible)
    refs = refs or [r["path"] for r in bible.get("refs", [])]
    imm = bible["immutable"]
    rubric = [{"id": q, "ask": _rubric_ask(q)} for q in RUBRIC_QUESTIONS]
    system = (
        "You are a strict product-consistency inspector for ads. "
        "Compare the KEYFRAME image to the PRODUCT BIBLE and REFERENCE images. "
        "Reply with JSON only, no markdown."
    )
    part_ids = [p["id"] for p in imm.get("parts") or []]
    user_text = {
        "task": "product_keyframe_qc",
        "product_name": bible.get("product_name"),
        "category": bible.get("category"),
        "subtype": bible.get("subtype"),
        "immutable": imm,
        "must_match_refs": bible.get("must_match_refs"),
        "rubric": rubric,
        "response_schema": {
            "pass": "bool — true only if every rubric item is clearly satisfied",
            "failures": "string[] — short codes or phrases for each failed item",
            "structure_mode_seen": (
                "string — which bible part/structure id(s) are shown "
                "(from %s), or 'closed'/'assembled', or 'unknown'" % (part_ids or ["<part id>"])
            ),
            "rubric_answers": {q: "yes|no|unclear" for q in RUBRIC_QUESTIONS},
            "notes": "string — one short sentence",
        },
        "instructions": [
            "Fail if structure is a hybrid not listed in immutable.parts (structure modes).",
            "Fail if any forbid[] rule is violated.",
            "Fail if critical parts are invented, omitted, or redesigned vs refs.",
            (
                "Fail logo_policy_ok — set rubric_answers.logo_policy_ok to no and pass to false — "
                "if logos or wordmarks violate immutable.logos, or if the frame shows a recognizable "
                "third-party trademark, wordmark, packaging, or brand-identifiable device "
                "(Apple MacBook / iPhone / logo, Nike swoosh, Starbucks cup mark, Amazon smile, "
                "Google or Microsoft hardware logos), unless that brand is the advertised SKU "
                "or the user explicitly approved showing it. Generic unbranded props pass "
                "(plain silver laptop with no logo or chin text, blank phone bezel, plain mug). "
                "Default forbid line: %s."
                % DEFAULT_THIRD_PARTY_FORBID
            ),
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
    answers = data.get("rubric_answers") or {}
    if not isinstance(answers, dict):
        answers = {}
    if _rubric_is_no(answers.get("logo_policy_ok")):
        passed = False
        if not any("logo_policy" in str(f).lower() for f in failures):
            failures.append("logo_policy_ok")
    # Prefer structure_mode_seen; accept legacy lid_mode_seen.
    mode_seen = data.get("structure_mode_seen")
    if mode_seen is None:
        mode_seen = data.get("lid_mode_seen", "unknown")
    return {
        "pass": passed,
        "failures": [str(f) for f in failures],
        "structure_mode_seen": mode_seen if mode_seen is not None else "unknown",
        "rubric_answers": data.get("rubric_answers") or {},
        "notes": data.get("notes") or "",
    }



def materialize_vision_body(body):
    """Copy chat body and replace file:// / local image_url entries with data: URLs."""
    import copy
    out = copy.deepcopy(body)
    for msg in out.get("messages") or []:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "image_url":
                continue
            url = (part.get("image_url") or {}).get("url") or ""
            if url.startswith("file://"):
                url = url[7:]
            if url and not url.startswith(("http://", "https://", "data:")):
                part["image_url"]["url"] = pt.to_media_ref(url)
            elif url.startswith("file://"):
                part["image_url"]["url"] = pt.to_media_ref(url[7:])
    return out


def extract_chat_content(resp):
    """Pull assistant text from a /v1/chat/completions-style response."""
    if not isinstance(resp, dict):
        return str(resp)
    choices = resp.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(p.get("text") or "")
                    elif isinstance(p, str):
                        parts.append(p)
                return "\n".join(parts)
            if content is not None:
                return content if isinstance(content, str) else json.dumps(content)
    for key in ("output_text", "content", "result"):
        if resp.get(key):
            return resp[key] if isinstance(resp[key], str) else json.dumps(resp[key])
    return json.dumps(resp)[:2000]


def call_vision_qc(bible, keyframe, cred, refs=None, model=None):
    """POST chat completion for product QC. Returns parse_verdict dict. Raises PTError."""
    body = materialize_vision_body(vision_messages(bible, keyframe, refs, model))
    code, resp, _ = pt.request("POST", "/v1/chat/completions", body, cred=cred, timeout=180)
    if code != 200:
        pt.raise_for(code, resp, "Vision QC chat")
    raw = extract_chat_content(resp)
    try:
        return parse_verdict(raw)
    except pt.PTError:
        # Some models wrap JSON; re-raise with preview
        raise


def augment_prompt_negatives(prompt, failures):
    """Append strict fix instructions from QC failures for one keyframe retry."""
    fails = [str(f).strip() for f in (failures or []) if str(f).strip()]
    if not fails:
        fails = ["unspecified structure mismatch vs product bible"]
    fix = (
        " STRICT FIX after failed product QC — do NOT repeat: %s. "
        "Obey PRODUCT LOCK / parts BOM exactly; no hybrid or invented parts."
        % "; ".join(fails[:8])
    )
    base = (prompt or "").rstrip()
    if "STRICT FIX after failed product QC" in base:
        return base
    return (base + fix).strip()


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
        pt.emit({
            "ok": True,
            "product_name": b["product_name"],
            "category": b.get("category"),
            "subtype": b.get("subtype"),
            "structure": [p["id"] for p in b["immutable"]["parts"]],
            "parts": [{"id": p["id"], "role": p.get("role")} for p in b["immutable"]["parts"]],
            "refs": len(b["refs"]),
        })
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
                 "category": (bible or {}).get("category"),
                 "subtype": (bible or {}).get("subtype"),
                 "qc_model_default": QC_CHAT_DEFAULT, "qc_model_alts": list(QC_CHAT_ALTS)})
        if not ok:
            return 2
    return 0


if __name__ == "__main__":
    pt.run(main)
