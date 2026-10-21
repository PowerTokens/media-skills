"""Claim sheet helper: validate + render markdown table (stdlib only).

  python3 claim_sheet.py validate claims.json
  python3 claim_sheet.py table claims.json
  python3 claim_sheet.py approve claims.json --ids c1,c2 -o claims.approved.json

Schema: see product-ad examples/claim-sheet.json.
Statuses: proposed | approved | rejected | needs_confirm
"""
from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

REQUIRED_TOP = ("product", "claims", "status")
REQUIRED_CLAIM = ("id", "claim", "source_type", "status")
OK_STATUS = {"proposed", "approved", "rejected", "needs_confirm", "pending_user_approval"}
OK_CLAIM_STATUS = {"proposed", "approved", "rejected", "needs_confirm"}
OK_SOURCE = {"user_brief", "product_page", "packaging", "packshot", "spec_sheet", "other"}


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("claim sheet must be a JSON object")
    return data


def validate(data):
    errs = []
    for k in REQUIRED_TOP:
        if k not in data:
            errs.append("missing top-level key: %s" % k)
    if data.get("status") and data["status"] not in OK_STATUS:
        errs.append("bad status: %s" % data.get("status"))
    prod = data.get("product") or {}
    if not prod.get("name"):
        errs.append("product.name required")
    claims = data.get("claims") or []
    if not isinstance(claims, list) or not claims:
        errs.append("claims must be a non-empty list")
    ids = set()
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            errs.append("claims[%d] not an object" % i)
            continue
        for k in REQUIRED_CLAIM:
            if not c.get(k):
                errs.append("claims[%d] missing %s" % (i, k))
        if c.get("id") in ids:
            errs.append("duplicate claim id: %s" % c.get("id"))
        ids.add(c.get("id"))
        if c.get("status") and c["status"] not in OK_CLAIM_STATUS:
            errs.append("claims[%d] bad status: %s" % (i, c.get("status")))
        if c.get("source_type") and c["source_type"] not in OK_SOURCE:
            errs.append("claims[%d] bad source_type: %s" % (i, c.get("source_type")))
        if c.get("status") == "approved" and not (c.get("source_quote") or c.get("source_type") == "user_brief"):
            errs.append("claims[%d] approved but missing source_quote" % i)
    return errs


def table(data):
    lines = [
        "| id | claim | source | quote | status | use_in |",
        "|---|---|---|---|---|---|",
    ]
    for c in data.get("claims") or []:
        use = ", ".join(c.get("use_in") or [])
        quote = (c.get("source_quote") or "").replace("|", "/")
        claim = (c.get("claim") or "").replace("|", "/")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            c.get("id", ""), claim, c.get("source_type", ""), quote[:80],
            c.get("status", ""), use))
    skipped = data.get("rejected_or_skipped") or []
    if skipped:
        lines.append("")
        lines.append("Skipped / rejected:")
        for s in skipped:
            lines.append("- %s — %s" % (s.get("text", ""), s.get("reason", "")))
    url = data.get("product_url") or ""
    name = (data.get("product") or {}).get("name", "")
    head = "**%s**" % name
    if url:
        head += " · %s" % url
    head += " · sheet status: `%s`" % data.get("status", "?")
    return head + "\n\n" + "\n".join(lines) + "\n"


def approve(data, ids):
    want = set(ids)
    found = set()
    for c in data.get("claims") or []:
        if c.get("id") in want:
            c["status"] = "approved"
            found.add(c["id"])
    missing = want - found
    if missing:
        raise SystemExit("unknown claim ids: %s" % ", ".join(sorted(missing)))
    data["status"] = "approved" if all(
        c.get("status") in ("approved", "rejected") for c in data["claims"]
    ) else "pending_user_approval"
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate / render product claim sheets")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("path")
    t = sub.add_parser("table")
    t.add_argument("path")
    a = sub.add_parser("approve")
    a.add_argument("path")
    a.add_argument("--ids", required=True, help="comma-separated claim ids to mark approved")
    a.add_argument("-o", "--output", help="write updated JSON here (default: stdout)")
    args = p.parse_args(argv)
    data = load(args.path)
    if args.cmd == "validate":
        errs = validate(data)
        if errs:
            print("INVALID", file=sys.stderr)
            for e in errs:
                print("-", e, file=sys.stderr)
            return 1
        print(json.dumps({"ok": True, "claims": len(data["claims"]), "status": data.get("status")}))
        return 0
    if args.cmd == "table":
        errs = validate(data)
        if errs:
            print("INVALID", file=sys.stderr)
            for e in errs:
                print("-", e, file=sys.stderr)
            return 1
        sys.stdout.write(table(data))
        return 0
    if args.cmd == "approve":
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        data = approve(data, ids)
        errs = validate(data)
        if errs:
            print("INVALID after approve", file=sys.stderr)
            for e in errs:
                print("-", e, file=sys.stderr)
            return 1
        out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(out, encoding="utf-8")
            print(json.dumps({"ok": True, "output": args.output, "status": data["status"]}))
        else:
            sys.stdout.write(out)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
