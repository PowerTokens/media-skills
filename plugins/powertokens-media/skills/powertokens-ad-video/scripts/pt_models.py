#!/usr/bin/env python3
"""List the model ids your PowerTokens credential can use (GET /v1/models). Optional filter."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--filter", default="", help="substring, e.g. seedance, wan, kling, seedream, speech")
    args = ap.parse_args()
    cred, source = pt.get_credential()
    code, body, _ = pt.request("GET", "/v1/models", cred=cred)
    if code != 200:
        pt.raise_for(code, body, "List models")
    ids = sorted(m.get("id") for m in body.get("data", []) if isinstance(m, dict) and m.get("id"))
    if args.filter:
        ids = [i for i in ids if args.filter.lower() in i.lower()]
    pt.emit({"ok": True, "credential_source": source, "count": len(ids), "models": ids})


if __name__ == "__main__":
    pt.run(main)
