#!/usr/bin/env python3
"""Character-consistency helpers for short-drama / UGC (stdlib only).

  python3 character_qc.py validate-bible bible.json
  python3 character_qc.py check-shotlist shots.json [--require]

Mirrors product_qc lightly: schema + pipeline gate only (no face vision QC yet).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

CHAR_KINDS_REQUIRE = ("short-drama", "short_drama", "drama", "micro-drama")
UGC_KINDS = ("ugc-ad", "ugc", "ugc_ad")


def _as_list(val):
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def normalize_character(cid, raw):
    """Normalize one character entry to {id, description, traits?, forbid?, refs?}."""
    if not isinstance(raw, dict):
        return {"id": str(cid), "description": ""}
    out = {"id": str(raw.get("id") or cid), "description": str(raw.get("description") or "").strip()}
    traits = [str(t).strip() for t in _as_list(raw.get("traits")) if str(t).strip()]
    if traits:
        out["traits"] = traits
    forbid = [str(f).strip() for f in _as_list(raw.get("forbid")) if str(f).strip()]
    if forbid:
        out["forbid"] = forbid
    refs = []
    for r in _as_list(raw.get("refs")):
        if isinstance(r, dict) and r.get("path"):
            refs.append(str(r["path"]))
        elif isinstance(r, str) and r.strip():
            refs.append(r.strip())
    if raw.get("ref_image"):
        ri = str(raw["ref_image"]).strip()
        if ri and ri not in refs:
            refs.insert(0, ri)
    if refs:
        out["refs"] = refs
    return out


def characters_from_bible_data(data):
    """Accept {characters: [...] } or {characters: {id: {...}}}."""
    if not isinstance(data, dict):
        return []
    raw = data.get("characters")
    out = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            cid = item.get("id")
            if not cid:
                continue
            out.append(normalize_character(cid, item))
    elif isinstance(raw, dict):
        for cid, item in raw.items():
            out.append(normalize_character(cid, item if isinstance(item, dict) else {}))
    return out


def validate_character(entry):
    """Return list of schema errors for one normalized character."""
    errs = []
    if not isinstance(entry, dict):
        return ["character must be an object"]
    cid = entry.get("id") or "?"
    if not entry.get("description"):
        errs.append("character %s: description is required" % cid)
    for key in ("traits", "forbid", "refs"):
        if key in entry and entry[key] is not None and not isinstance(entry[key], list):
            errs.append("character %s: %s must be a list when present" % (cid, key))
    return errs


def validate_bible(data):
    errs = []
    if not isinstance(data, dict):
        return ["character bible must be a JSON object"]
    chars = characters_from_bible_data(data)
    if not chars:
        errs.append("characters must be a non-empty list or object")
        return errs
    ids = set()
    for c in chars:
        if c["id"] in ids:
            errs.append("duplicate character id %s" % c["id"])
        ids.add(c["id"])
        errs.extend(validate_character(c))
    return errs


def load_bible(path):
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise pt.PTError("Cannot read character bible %s: %s" % (path, exc), "BAD_REQUEST", 3)
    errs = validate_bible(data)
    if errs:
        raise pt.PTError("Character bible invalid: " + "; ".join(errs), "BAD_REQUEST", 3)
    chars = characters_from_bible_data(data)
    return {"_path": str(p.resolve()), "characters": chars, "raw": data}


def merge_into_spec_characters(spec, bible_chars):
    """Merge bible characters into spec['characters'] dict without wiping richer inline fields."""
    dest = spec.setdefault("characters", {})
    for c in bible_chars:
        cid = c["id"]
        existing = dest.get(cid) if isinstance(dest.get(cid), dict) else {}
        merged = dict(existing)
        merged["description"] = existing.get("description") or c["description"]
        if c.get("traits") and not existing.get("traits"):
            merged["traits"] = c["traits"]
        if c.get("forbid") and not existing.get("forbid"):
            merged["forbid"] = c["forbid"]
        if c.get("refs") and not existing.get("ref_image") and not existing.get("refs"):
            merged["ref_image"] = c["refs"][0]
            if len(c["refs"]) > 1:
                merged["refs"] = c["refs"][1:]
        dest[cid] = merged
    return dest


def check_shotlist_characters(spec_or_path, require=False):
    """Validate character_bible / inline characters. Returns (ok, errors)."""
    if isinstance(spec_or_path, (str, Path)):
        path = Path(spec_or_path)
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return False, ["cannot read shot list: %s" % exc]
        base = path.resolve().parent
    else:
        spec = spec_or_path
        base = Path(spec.get("_base") or ".")

    kind = (spec.get("kind") or "").lower()
    inline = spec.get("characters") or {}
    bible_rel = spec.get("character_bible")
    errs = []

    bible_chars = []
    if bible_rel:
        bpath = Path(bible_rel) if Path(bible_rel).is_absolute() else base / bible_rel
        if not bpath.is_file():
            errs.append("character_bible file not found: %s" % bpath)
            return False, errs
        try:
            loaded = load_bible(bpath)
            bible_chars = loaded["characters"]
            if isinstance(spec_or_path, dict) or hasattr(spec, "get"):
                merge_into_spec_characters(spec, bible_chars)
        except pt.PTError as exc:
            return False, [str(exc)]

    # Normalize inline dict entries for schema checks
    inline_list = []
    if isinstance(inline, dict):
        for cid, raw in inline.items():
            inline_list.append(normalize_character(cid, raw if isinstance(raw, dict) else {}))
    elif isinstance(inline, list):
        inline_list = [normalize_character(c.get("id", "c%d" % i), c)
                       for i, c in enumerate(inline) if isinstance(c, dict)]

    combined = {c["id"]: c for c in bible_chars}
    for c in inline_list:
        combined[c["id"]] = c
    chars = list(combined.values())

    need = require or kind in CHAR_KINDS_REQUIRE
    ugc_uses = kind in UGC_KINDS and bool(chars or bible_rel)

    if need and not chars:
        errs.append(
            "short-drama shot list requires character_bible or inline characters{} "
            "with description; see powertokens-short-drama"
        )
        return False, errs

    if need or ugc_uses or bible_rel:
        if not chars and ugc_uses:
            errs.append("ugc-ad with characters requires valid character entries")
        for c in chars:
            errs.extend(validate_character(c))

    return (len(errs) == 0), errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate-bible")
    p.add_argument("bible")
    p = sub.add_parser("check-shotlist")
    p.add_argument("shots")
    p.add_argument("--require", action="store_true")
    a = ap.parse_args()
    if a.cmd == "validate-bible":
        b = load_bible(a.bible)
        pt.emit({"ok": True, "characters": [{"id": c["id"], "has_refs": bool(c.get("refs"))}
                                            for c in b["characters"]]})
    else:
        ok, errs = check_shotlist_characters(a.shots, require=a.require)
        pt.emit({"ok": ok, "errors": errs})
        if not ok:
            return 2
    return 0


if __name__ == "__main__":
    pt.run(main)
