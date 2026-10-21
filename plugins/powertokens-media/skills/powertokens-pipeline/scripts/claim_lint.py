#!/usr/bin/env python3
"""Offline claim / fake-proof lint for captions, VO, and finish end-cards.

Refuse award / certification / fake-review style language unless the shot list sets
`claims_approved: true` (user explicitly signed off on those claims).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

# Case-insensitive. Keep patterns specific — avoid flagging normal product copy.
CLAIM_PATTERNS = [
    (r"\baward[-\s]?winning\b", "award-winning"),
    (r"\b(winner|won)\b.{0,40}\b(award|prize|oscar|emmy|grammy)\b", "award claim"),
    (r"\b#?\s*1\b.{0,30}\b(best|rated|seller|selling)\b", "#1 / best-seller claim"),
    (r"\bbest[-\s]?seller\b", "best-seller claim"),
    (r"\b(certified|certification)\b", "certification claim"),
    (r"\bFDA\s*[- ]?approved\b", "FDA-approved claim"),
    (r"\bclinically\s+(proven|tested|shown)\b", "clinically proven claim"),
    (r"\b(doctor|dermatologist|dentist)s?\s+recommend", "professional endorsement claim"),
    (r"\b\d{2,}\s*\+?\s*(five[-\s]?star\s+)?(reviews?|ratings?)\b", "review-count claim"),
    (r"\b(5|five)[-\s]?star\b.{0,20}\b(review|rated|rating)\b", "five-star review claim"),
    (r"\bas\s+seen\s+on\b", "as-seen-on claim"),
    (r"\bfeatured\s+in\b", "featured-in claim"),
    (r"\bguaranteed\b.{0,30}\b(result|results|works?|money)\b", "results guarantee"),
    (r"\bmoney[-\s]?back\s+guarantee\b", "money-back guarantee"),
    (r"\b\d{2,3}\s*%\s*(of\s+)?(users?|customers?|people)\b", "percentage-of-users claim"),
]

_COMPILED = [(re.compile(p, re.I | re.S), label) for p, label in CLAIM_PATTERNS]


def find_claims(text):
    """Return list of {snippet, label} for matches in text."""
    if not text or not str(text).strip():
        return []
    s = str(text)
    hits = []
    for cre, label in _COMPILED:
        m = cre.search(s)
        if m:
            hits.append({"label": label, "snippet": m.group(0)[:80]})
    return hits


def lint_texts(items, claims_approved=False):
    """items: iterable of (where, text). Returns list of error strings."""
    if claims_approved:
        return []
    errs = []
    for where, text in items:
        for hit in find_claims(text):
            errs.append("%s: refused claim (%s): %r — set claims_approved:true if the user signed off"
                        % (where, hit["label"], hit["snippet"]))
    return errs


def collect_shotlist_texts(spec):
    """Gather caption / VO / finish end-card strings from a shot list."""
    items = []
    for shot in spec.get("shots") or []:
        sid = shot.get("id") or "?"
        if shot.get("caption"):
            items.append(("%s.caption" % sid, shot["caption"]))
        if shot.get("prompt") and shot.get("lint_prompt_claims"):
            items.append(("%s.prompt" % sid, shot["prompt"]))
    vo = spec.get("voiceover") or {}
    for i, line in enumerate(vo.get("lines") or []):
        key = line.get("id") or "vo%02d" % (i + 1)
        if line.get("text"):
            items.append(("voiceover.%s" % key, line["text"]))
        if line.get("caption"):
            items.append(("voiceover.%s.caption" % key, line["caption"]))
    finish = spec.get("finish") or {}
    card = finish.get("end_card") or {}
    for field in ("headline", "price", "cta", "wordmark", "sub"):
        if card.get(field):
            items.append(("finish.end_card.%s" % field, card[field]))
    hook = finish.get("hook") or {}
    for field in ("text", "sub"):
        if hook.get(field):
            items.append(("finish.hook.%s" % field, hook[field]))
    return items


def lint_shotlist(spec):
    approved = bool(spec.get("claims_approved"))
    return lint_texts(collect_shotlist_texts(spec), claims_approved=approved)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("shotlist")
    p = sub.add_parser("scan-text")
    p.add_argument("text")
    a = ap.parse_args()
    if a.cmd == "scan-text":
        hits = find_claims(a.text)
        pt.emit({"ok": not hits, "hits": hits})
        return 0 if not hits else 2
    spec = json.loads(Path(a.shotlist).read_text(encoding="utf-8"))
    errs = lint_shotlist(spec)
    pt.emit({"ok": not errs, "errors": errs, "claims_approved": bool(spec.get("claims_approved"))})
    return 0 if not errs else 2


if __name__ == "__main__":
    pt.run(main)
