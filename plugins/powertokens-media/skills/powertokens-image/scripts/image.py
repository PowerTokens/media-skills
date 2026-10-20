#!/usr/bin/env python3
"""Text-to-image (and reference-image edits) via PowerTokens POST /v1/images/generations.

Examples:
  python3 image.py -p "studio photo of a glass perfume bottle on wet black stone" --size 2K
  python3 image.py -p "same bottle, on a beach at sunset" --image ./bottle.png
  python3 image.py ... --dry-run
"""
import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

# Ids from docs.powertokens.ai (Seedream text-to-image pages). Confirm with pt_models.py --filter seedream.
MODELS = {
    "seedream-4-5-251128": "Seedream 4.5 — default; sizes 2K / 4K or WxH (>= 2560x1440 total pixels)",
    "seedream-5-0-260128": "Seedream 5.0",
    "dola-seedream-5-0-pro-260628": "Seedream 5.0 Pro",
}
DEFAULT_MODEL = "seedream-4-5-251128"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--prompt", required=False, default="")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL)
    ap.add_argument("--size", default="2K", help="2K, 4K, or WIDTHxHEIGHT e.g. 1440x2560 for 9:16")
    ap.add_argument("--image", action="append", help="reference image(s): local file or https URL")
    ap.add_argument("--seed", type=int)
    ap.add_argument("-n", "--max-images", type=int, default=1, help=">1 enables sequential image sets")
    ap.add_argument("-o", "--output", help="default ./outputs/image-<time>.png (suffix -2, -3 for sets)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()
    if a.list_models:
        pt.emit({"default": DEFAULT_MODEL, "models": MODELS})
        return 0
    if not a.prompt.strip():
        raise pt.PTError("--prompt is required", "BAD_REQUEST", 3)
    body = {"model": a.model, "prompt": a.prompt.strip(), "size": a.size, "response_format": "url",
            "watermark": False}
    if a.image:
        refs = [pt.to_media_ref(i) for i in a.image]
        body["image"] = refs[0] if len(refs) == 1 else refs
    if a.seed is not None:
        body["seed"] = a.seed
    if a.max_images > 1:
        body["sequential_image_generation"] = "auto"
        body["sequential_image_generation_options"] = {"max_images": a.max_images}
    if a.dry_run:
        shown = dict(body)
        if "image" in shown:
            shown["image"] = "<%d reference image(s)>" % len(a.image)
        pt.emit({"dry_run": True, "endpoint": pt.API_BASE + "/v1/images/generations", "body": shown})
        return 0
    cred, _ = pt.get_credential()
    code, resp, _ = pt.request("POST", "/v1/images/generations", body, cred=cred, timeout=300)
    if code != 200:
        pt.raise_for(code, resp, "Image generation")
    items = resp.get("data") or []
    if not items:
        pt.raise_for(code, resp, "Image generation (empty result)")
    base = Path(a.output or pt.default_output("image", "png"))
    outputs = []
    for i, item in enumerate(items):
        path = base if i == 0 else base.with_name("%s-%d%s" % (base.stem, i + 1, base.suffix))
        if item.get("url"):
            saved = Path(pt.download(item["url"], path, cred))
            # Seedream returns JPEG; fix the extension so viewers and ffmpeg are not confused.
            if pt.sniff_image_mime(saved.read_bytes()[:16]) == "image/jpeg" and saved.suffix.lower() == ".png":
                fixed = saved.with_suffix(".jpg")
                saved.replace(fixed)
                saved = fixed
            outputs.append(str(saved))
        elif item.get("b64_json"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(item["b64_json"]))
            outputs.append(str(path.resolve()))
    pt.emit({"ok": True, "model": a.model, "outputs": outputs, "usage": resp.get("usage")})
    return 0


if __name__ == "__main__":
    pt.run(main)
