#!/usr/bin/env python3
"""Text-to-video and image-to-video via PowerTokens. Submits, polls, downloads the mp4.

Examples:
  python3 video.py generate -p "a red fox running through snow, cinematic" -d 5 -r 720p --ratio 16:9
  python3 video.py generate -p "the bottle slowly rotates" --image ./product.png --ratio 9:16
  python3 video.py generate ... --dry-run          # print the request, spend nothing
  python3 video.py resume TASK_ID --model wan3.0-video   # re-poll / download without paying again
  python3 video.py models                           # model table with limits and list prices
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

# Mirrors PowerTokens Video Studio models.py (checked 2026-10-05). USD per output second.
MODELS = {
    "wan3.0-video": dict(family="wan", name="Wan 3.0", durations=(2, 30), res=("480p", "720p", "1080p"),
                         ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "adaptive"),
                         price={"480p": 0.05, "720p": 0.10, "1080p": 0.20}),
    "wan3.0-video-prime": dict(family="wan", name="Wan 3.0 Prime (faster)", durations=(2, 30),
                               res=("480p", "720p", "1080p"),
                               ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "adaptive"),
                               price={"480p": 0.068, "720p": 0.14, "1080p": 0.28}),
    "dreamina-seedance-2-0-fast-260128": dict(family="seedance", name="Seedance 2.0 Fast", durations=(4, 15),
                                              res=("480p", "720p"),
                                              ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"),
                                              price={"480p": 0.121, "720p": 0.121}),
    "dreamina-seedance-2-5-260628": dict(family="seedance", name="Seedance 2.5", durations=(4, 30),
                                         res=("480p", "720p", "1080p"),
                                         ratios=("16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"),
                                         price={"480p": 0.105, "720p": 0.232, "1080p": 0.569}),
    "kling-v3": dict(family="kling", name="Kling v3", durations=(3, 15), res=("720p", "1080p", "4k"),
                     ratios=("16:9", "9:16", "1:1"), price={"720p": 0.126, "1080p": 0.168, "4k": 0.42}),
}
ALIASES = {"wan": "wan3.0-video", "wan3": "wan3.0-video", "wan-prime": "wan3.0-video-prime",
           "seedance": "dreamina-seedance-2-0-fast-260128", "seedance-fast": "dreamina-seedance-2-0-fast-260128",
           "seedance-2.5": "dreamina-seedance-2-5-260628", "kling": "kling-v3"}
DEFAULT_MODEL = "wan3.0-video"
KLING_MODE = {"720p": "std", "1080p": "pro", "4k": "4k"}


def resolve(model):
    m = ALIASES.get(model.lower(), model)
    if m not in MODELS:
        raise pt.PTError("Unknown model %r. Choose one of: %s" % (model, ", ".join(MODELS)), "BAD_REQUEST", 3)
    return m


def estimate(model, duration, res):
    return round(MODELS[model]["price"].get(res, 0) * duration, 3)


def build(model, prompt, duration, res, ratio, image=None, last=None, audio=True, refs=None):
    spec = MODELS[model]
    lo, hi = spec["durations"]
    if not lo <= duration <= hi:
        raise pt.PTError("%s supports %d-%d seconds." % (spec["name"], lo, hi), "BAD_REQUEST", 3)
    if res not in spec["res"]:
        raise pt.PTError("%s supports %s." % (spec["name"], ", ".join(spec["res"])), "BAD_REQUEST", 3)
    if ratio not in spec["ratios"]:
        raise pt.PTError("%s supports ratios %s." % (spec["name"], ", ".join(spec["ratios"])), "BAD_REQUEST", 3)
    media = []
    if image:
        media.append({"type": "first_frame", "url": pt.to_media_ref(image)})
    if last:
        media.append({"type": "last_frame", "url": pt.to_media_ref(last)})
    fam = spec["family"]
    refs = list(refs or [])
    if refs:
        # Reference-to-video (character / product consistency). Docs: Wan 3.0 says reference_* and
        # first/last frame are mutually exclusive; Kling v3 uses a different element API (not wired).
        if fam == "kling":
            raise pt.PTError("Reference images are not supported for Kling in this skill; use Wan 3.0 "
                             "or Seedance.", "BAD_REQUEST", 3)
        if fam == "wan" and media:
            raise pt.PTError("Wan 3.0: reference images cannot be combined with first/last frame. "
                             "Use one or the other.", "BAD_REQUEST", 3)
        media.extend({"type": "reference_image", "url": pt.to_media_ref(r)} for r in refs)
    if fam == "wan":
        body = dict(model=model, prompt=prompt.strip(), seconds=str(duration), size=res.upper(),
                    ratio=ratio, generate_audio=audio)
        if media:
            body["media"] = media
        return "/v1/videos", body
    if fam == "seedance":
        items = ([{"type": "text", "text": prompt.strip()}] if prompt.strip() else []) + media
        if not items:
            raise pt.PTError("Give a prompt or an image.", "BAD_REQUEST", 3)
        return "/v1/videos", dict(model=model, media=items, seconds=str(duration), size=res.lower(),
                                  ratio=ratio, generate_audio=audio, watermark=False)
    body = dict(model_name=model, prompt=prompt.strip(), duration=str(duration), mode=KLING_MODE[res],
                sound="on" if audio else "off")

    def raw_b64(ref):
        return ref.split(";base64,", 1)[1] if ref.startswith("data:") and ";base64," in ref else ref
    if media:
        for m in media:
            body["image" if m["type"] == "first_frame" else "image_tail"] = raw_b64(m["url"])
        return "/kling/v1/videos/image2video", body
    body["aspect_ratio"] = ratio
    return "/kling/v1/videos/text2video", body


def poll_path(model, task_id, i2v=False):
    if MODELS[model]["family"] == "kling":
        return "/kling/v1/videos/%s/%s" % ("image2video" if i2v else "text2video", task_id)
    return "/v1/videos/" + task_id


def parse_status(model, body):
    if MODELS[model]["family"] == "kling":
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        raw = str(data.get("task_status") or "").lower()
        status = {"submitted": "queued", "processing": "in_progress", "succeed": "succeeded",
                  "success": "succeeded"}.get(raw, raw)
        vids = (data.get("task_result") or {}).get("videos") or []
        url = vids[0].get("url", "") if vids and isinstance(vids[0], dict) else ""
        return status, None, url, data.get("task_status_msg")
    status = str(body.get("status") or "").lower()
    meta = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
    content = body.get("content") if isinstance(body.get("content"), dict) else {}
    url = ""
    for c in (meta.get("url"), body.get("video_url"), content.get("video_url")):
        if isinstance(c, str) and c.startswith("https://"):
            url = c
            break
    err = body.get("error") if body.get("error") else None
    return status, body.get("progress"), url, err


def wait_and_download(cred, model, task_id, output, i2v=False, timeout=1800, interval=10):
    path = poll_path(model, task_id, i2v)
    start, errors = time.time(), 0
    while time.time() - start < timeout:
        code, body, _ = pt.request("GET", path, cred=cred)
        if code != 200:
            errors += 1
            if code in (401, 402, 403) or errors >= 5:
                pt.raise_for(code, body, "Polling task %s" % task_id)
            time.sleep(interval)
            continue
        status, progress, url, err = parse_status(model, body)
        print("[%ds] %s %s" % (time.time() - start, status or "?", "" if progress is None else "%s%%" % progress),
              file=sys.stderr, flush=True)
        if status in ("succeeded", "completed", "success"):
            src = url or (pt.API_BASE + path + "/content" if MODELS[model]["family"] != "kling" else "")
            if not src:
                raise pt.PTError("Task succeeded but returned no video URL.", "SERVER")
            return pt.download(src, output, cred)
        if status in ("failed", "cancelled", "canceled"):
            raise pt.PTError("Task %s %s: %s" % (task_id, status, err or "no reason given"), "FAILED")
        time.sleep(interval)
    raise pt.PTError("Still running after %ds. Resume later with: video.py resume %s --model %s"
                     % (timeout, task_id, model), "TIMEOUT", 5)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("-p", "--prompt", default="")
    g.add_argument("-m", "--model", default=DEFAULT_MODEL)
    g.add_argument("-d", "--duration", type=int, default=5)
    g.add_argument("-r", "--resolution", default="720p")
    g.add_argument("--ratio", default="16:9")
    g.add_argument("-i", "--image", help="first frame: local file or https URL (image-to-video)")
    g.add_argument("--last-frame", help="optional last frame")
    g.add_argument("--ref-image", action="append", default=[],
                   help="reference image for character/product consistency (repeatable; Wan/Seedance). "
                        "Refer to them in the prompt as image 1, image 2, ...")
    g.add_argument("--no-audio", action="store_true")
    g.add_argument("-o", "--output", help="default ./outputs/video-<time>.mp4")
    g.add_argument("--dry-run", action="store_true", help="print request + estimate, do not submit")
    g.add_argument("--timeout", type=int, default=1800)
    r = sub.add_parser("resume")
    r.add_argument("task_id")
    r.add_argument("-m", "--model", default=DEFAULT_MODEL)
    r.add_argument("--image-to-video", action="store_true", help="Kling only: task was image2video")
    r.add_argument("-o", "--output")
    sub.add_parser("models")
    a = ap.parse_args()

    if a.cmd == "models":
        pt.emit({"default": DEFAULT_MODEL, "models": [
            dict(id=k, name=v["name"], seconds="%d-%d" % v["durations"], resolutions=v["res"],
                 ratios=v["ratios"], list_usd_per_second=v["price"]) for k, v in MODELS.items()],
            "note": "List prices from powertokens.ai model pages (checked 2026-10-05); check the site for current pricing."})
        return 0
    model = resolve(a.model)
    if a.cmd == "resume":
        cred, _ = pt.get_credential()
        out = a.output or pt.default_output("video", "mp4")
        path = wait_and_download(cred, model, a.task_id, out, a.image_to_video)
        pt.emit({"ok": True, "task_id": a.task_id, "model": model, "output": path})
        return 0
    res = a.resolution.lower()
    endpoint, body = build(model, a.prompt, a.duration, res, a.ratio, a.image, a.last_frame, not a.no_audio, a.ref_image)
    est = estimate(model, a.duration, res)
    if a.dry_run:
        shown = {k: (v[:60] + "…" if isinstance(v, str) and len(v) > 200 else v) for k, v in body.items()}
        pt.emit({"dry_run": True, "endpoint": pt.API_BASE + endpoint, "body": shown, "est_cost_usd": est})
        return 0
    cred, source = pt.get_credential()
    code, resp, _ = pt.request("POST", endpoint, body, cred=cred)
    if code not in (200, 201, 202):
        pt.raise_for(code, resp, "Submit video")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    task_id = resp.get("id") or resp.get("task_id") or data.get("task_id")
    if not task_id:
        pt.raise_for(code, resp, "Submit video (no task id)")
    print("Submitted task %s (%s, est. $%s). Polling…" % (task_id, model, est), file=sys.stderr, flush=True)
    out = a.output or pt.default_output("video", "mp4")
    path = wait_and_download(cred, model, task_id, out, i2v=endpoint.endswith("image2video"), timeout=a.timeout)
    pt.emit({"ok": True, "task_id": task_id, "model": model, "est_cost_usd": est, "output": path})
    return 0


if __name__ == "__main__":
    pt.run(main)
