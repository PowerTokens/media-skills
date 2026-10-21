#!/usr/bin/env python3
"""Shot-list pipeline: JSON shot list -> keyframes (Seedream) -> clips (Wan/Seedance/Kling)
-> voiceover (MiniMax) -> assembled MP4 with captions. Estimate first, resume always.

  python3 pipeline.py validate shots.json            # schema + model limit checks, no network
  python3 pipeline.py validate shots.json --require-product-bible
  python3 pipeline.py plan shots.json                # cost estimate + writes <workdir>/plan.json
  python3 pipeline.py run shots.json --approve-estimate 4.20   # spends credits; must match plan total
  python3 pipeline.py status shots.json              # what is done / pending / failed
  python3 pipeline.py assemble shots.json            # ffmpeg: normalize, concat, voiceover, captions
  python3 pipeline.py reformat final.mp4 --ratio 1:1 # social variant via crop/pad (no credits)

State lives in <workdir>/state.json. Every task id is saved the moment it exists, so `run` again
resumes (polls/downloads) instead of paying twice. Schema: references/shotlist-schema.md.
"""
import argparse
import concurrent.futures as cf
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402
import video  # noqa: E402
import product_qc  # noqa: E402

RATIO_WH = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080),
            "4:3": (1440, 1080), "3:4": (1080, 1440), "21:9": (2520, 1080)}
_LOCK = threading.Lock()


# ------------------------------------------------------------------ load / validate
def load(path):
    p = Path(path)
    try:
        spec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise pt.PTError("Cannot read shot list %s: %s" % (path, exc), "BAD_REQUEST", 3)
    spec["_base"] = str(p.resolve().parent)
    spec.setdefault("project", p.stem)
    spec.setdefault("defaults", {})
    spec.setdefault("characters", {})
    spec.setdefault("shots", [])
    spec["_workdir"] = str((p.resolve().parent / spec.get("workdir", "outputs/" + spec["project"])).resolve())
    return spec


def resolve_path(spec, value):
    if not value or value.startswith(("https://", "http://", "data:")):
        return value
    p = Path(value)
    return str(p if p.is_absolute() else Path(spec["_base"]) / p)


def get_bible(spec):
    """Load product bible once per shot list (None if absent / not required)."""
    if "_bible" in spec:
        return spec["_bible"]
    _ok, _errs, bible = product_qc.check_shotlist_bible(spec, require=False)
    spec["_bible"] = bible
    return bible


def shot_settings(spec, shot):
    d = dict(spec["defaults"])
    d.update({k: v for k, v in shot.items() if v is not None})
    d["model"] = video.resolve(d.get("model", video.DEFAULT_MODEL))
    d["duration"] = int(d.get("duration", 5))
    d["resolution"] = str(d.get("resolution", "720p")).lower()
    d["ratio"] = d.get("ratio", "9:16")
    d["audio"] = bool(d.get("audio", True))
    return d


def compose_prompt(spec, s):
    parts = []
    if spec.get("style"):
        parts.append(spec["style"].strip())
    for cid in s.get("characters", []):
        c = spec["characters"].get(cid)
        if c and c.get("description"):
            parts.append(c["description"].strip())
    parts.append(s.get("prompt", "").strip())
    bible = get_bible(spec)
    if bible:
        # Always inject PRODUCT LOCK for product-ad (and any shot list with a bible).
        parts.append(product_qc.constraints_block(bible))
    return " ".join(p for p in parts if p)


def ref_images(spec, s):
    refs = []
    for cid in s.get("characters", []):
        c = spec["characters"].get(cid) or {}
        if c.get("ref_image"):
            refs.append(resolve_path(spec, c["ref_image"]))
    refs += [resolve_path(spec, r) for r in s.get("ref_images", [])]
    return refs


def keyframe_ref_images(spec, s):
    """Refs for Seedream keyframes: shot refs + existing bible refs (product lock photos).

    Not used for Wan/Kling i2v — Wan forbids mixing first_frame with reference_image;
    Kling has no ref wiring. Product lock for i2v is the QC-passed keyframe + prompt constraints.
    """
    refs = list(ref_images(spec, s))
    kf = s.get("keyframe") or {}
    refs += [resolve_path(spec, r) for r in kf.get("ref_images", [])]
    bible = get_bible(spec)
    if bible:
        seen = set(refs)
        for r in bible.get("refs") or []:
            path = resolve_path(spec, r.get("path"))
            if not path or path in seen:
                continue
            if path.startswith(("https://", "http://", "data:")) or Path(path).is_file():
                refs.append(path)
                seen.add(path)
    return refs


def validate(spec, require_product_bible=False):
    errors, ids = [], set()
    ok_b, b_errs, _ = product_qc.check_shotlist_bible(spec, require=require_product_bible)
    errors.extend(b_errs)
    if not spec["shots"]:
        errors.append("shots[] is empty")
    for cid, c in spec["characters"].items():
        if not c.get("description"):
            errors.append("character %s: description is required (it is prepended to every shot)" % cid)
    for i, shot in enumerate(spec["shots"]):
        sid = shot.get("id") or "shot%02d" % (i + 1)
        shot["id"] = sid
        if sid in ids:
            errors.append("duplicate shot id %s" % sid)
        ids.add(sid)
        try:
            s = shot_settings(spec, shot)
        except pt.PTError as exc:
            errors.append("%s: %s" % (sid, exc)); continue
        for cid in s.get("characters", []):
            if cid not in spec["characters"]:
                errors.append("%s: unknown character %s" % (sid, cid))
        if not s.get("prompt") and not s.get("keyframe"):
            errors.append("%s: prompt is required" % sid)
        image = "__keyframe__" if s.get("keyframe") else resolve_path(spec, s.get("image"))
        refs = ref_images(spec, s)
        try:
            # build() checks duration / resolution / ratio / media combos against model limits
            video.build(s["model"], compose_prompt(spec, s) or "x", s["duration"], s["resolution"], s["ratio"],
                        image="https://example.invalid/k.png" if image else None, audio=s["audio"],
                        refs=["https://example.invalid/r.png"] * len(refs))
        except pt.PTError as exc:
            errors.append("%s: %s" % (sid, exc))
        for path in ([image] if image and image != "__keyframe__" else []) + refs:
            if path and not path.startswith(("https://", "http://", "data:")) and not Path(path).is_file():
                errors.append("%s: file not found: %s" % (sid, path))
    vo = spec.get("voiceover") or {}
    for line in vo.get("lines", []):
        if not line.get("text"):
            errors.append("voiceover line without text")
    return errors


# ------------------------------------------------------------------ plan / estimate
def plan(spec):
    items, total, unknown = [], 0.0, []
    state = load_state(spec)
    for shot in spec["shots"]:
        s = shot_settings(spec, shot)
        st = state["shots"].get(s["id"], {})
        already = (st.get("status") == "done" and Path(st.get("output", "")).is_file()) or bool(st.get("task_id"))
        cost = 0.0 if already else video.estimate(s["model"], s["duration"], s["resolution"])
        total += cost
        items.append({"id": s["id"], "model": s["model"], "seconds": s["duration"], "resolution": s["resolution"],
                      "ratio": s["ratio"], "est_usd": cost,
                      "keyframe": bool(s.get("keyframe")), "refs": len(ref_images(spec, s)),
                      "already_paid": already})
        if s.get("keyframe") and not already:
            unknown.append("%s keyframe image (Seedream; price not in this repo, see powertokens.ai/models)" % s["id"])
    vo = spec.get("voiceover") or {}
    vstate = state.get("voiceover", {})
    chars = sum(len(l.get("text", "")) for i, l in enumerate(vo.get("lines", []))
                if vstate.get(l.get("id") or "vo%02d" % (i + 1), {}).get("status") != "done")
    if chars:
        unknown.append("voiceover %d characters (MiniMax speech; billed per character, price not in this repo)" % chars)
    secs = sum(i["seconds"] for i in items)
    return {"project": spec["project"], "workdir": spec["_workdir"], "shots": items, "total_seconds": secs,
            "video_est_usd": round(total, 2), "not_estimated": unknown,
            "price_source": "List prices copied from PowerTokens Video Studio models.py (checked 2026-10-05); "
                            "actual billing may differ. Verify at https://powertokens.ai/models?" + pt.UTM}


# ------------------------------------------------------------------ state
def state_path(spec):
    return Path(spec["_workdir"]) / "state.json"


def load_state(spec):
    try:
        return json.loads(state_path(spec).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"shots": {}, "voiceover": {}}


def save_state(spec, state):
    with _LOCK:
        p = state_path(spec)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)


# ------------------------------------------------------------------ run
def gen_keyframe(spec, s, cred, out):
    kf = s["keyframe"]
    w, h = {"9:16": (1440, 2560), "16:9": (2560, 1440), "1:1": (2048, 2048)}.get(s["ratio"], (2048, 2048))
    prompt = kf["prompt"]
    bible = get_bible(spec)
    if bible:
        lock = product_qc.constraints_block(bible)
        if "PRODUCT LOCK" not in prompt:
            prompt = (prompt.rstrip() + " " + lock).strip()
    body = {"model": kf.get("model", "seedream-4-5-251128"), "prompt": prompt,
            "size": kf.get("size", "%dx%d" % (w, h)), "response_format": "url", "watermark": False}
    refs = [pt.to_media_ref(r) for r in keyframe_ref_images(spec, s)]
    if refs:
        body["image"] = refs[0] if len(refs) == 1 else refs
    code, resp, _ = pt.request("POST", "/v1/images/generations", body, cred=cred, timeout=300)
    if code != 200 or not resp.get("data"):
        pt.raise_for(code, resp, "Keyframe %s" % s["id"])
    item = resp["data"][0]
    if item.get("url"):
        return pt.download(item["url"], out, cred)
    import base64
    Path(out).write_bytes(base64.b64decode(item["b64_json"]))
    return str(Path(out).resolve())


def run_shot(spec, shot, cred, state, wd):
    s = shot_settings(spec, shot)
    sid = s["id"]
    st = state["shots"].setdefault(sid, {})
    out = str(wd / "clips" / ("%s.mp4" % sid))
    if st.get("status") == "done" and Path(st.get("output", "")).is_file():
        return sid, "skipped (done)"
    if st.get("task_id"):
        print("[%s] resuming task %s" % (sid, st["task_id"]), file=sys.stderr, flush=True)
    else:
        image = resolve_path(spec, s.get("image"))
        if s.get("keyframe"):
            kf_out = str(wd / "keyframes" / ("%s.png" % sid))
            if not Path(st.get("keyframe", "")).is_file():
                st["keyframe"] = gen_keyframe(spec, s, cred, kf_out)
                save_state(spec, state)
            image = st["keyframe"]
        refs = [] if image and s["model"].startswith("wan") else ref_images(spec, s)
        endpoint, body = video.build(s["model"], compose_prompt(spec, s), s["duration"], s["resolution"],
                                     s["ratio"], image=image, audio=s["audio"], refs=refs)
        code, resp, _ = pt.request("POST", endpoint, body, cred=cred)
        if code not in (200, 201, 202):
            st.update(status="failed", error="submit HTTP %s" % code)
            save_state(spec, state)
            pt.raise_for(code, resp, "Submit %s" % sid)
        data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
        task = resp.get("id") or resp.get("task_id") or data.get("task_id")
        if not task:
            pt.raise_for(code, resp, "Submit %s (no task id)" % sid)
        st.update(task_id=task, model=s["model"], i2v=endpoint.endswith("image2video"), status="submitted",
                  submitted_at=int(time.time()))
        save_state(spec, state)  # saved BEFORE polling -> never pay twice
    try:
        st["output"] = video.wait_and_download(cred, st["model"], st["task_id"], out, st.get("i2v", False))
        st["status"] = "done"
    except pt.PTError as exc:
        st.update(status="timeout" if exc.kind == "TIMEOUT" else "failed", error=str(exc))
        save_state(spec, state)
        raise
    save_state(spec, state)
    return sid, "done"


def run_voiceover(spec, cred, state, wd):
    vo = spec.get("voiceover") or {}
    lines = vo.get("lines", [])
    if not lines:
        return []
    done = []
    for i, line in enumerate(lines):
        key = line.get("id") or "vo%02d" % (i + 1)
        st = state["voiceover"].setdefault(key, {})
        if st.get("status") == "done" and Path(st.get("output", "")).is_file():
            done.append(key); continue
        body = {"model": line.get("model", vo.get("model", "speech-2.8-turbo")), "input": line["text"],
                "voice": line.get("voice", vo.get("voice", "English_Trustworthy_Man")),
                "speed": line.get("speed", vo.get("speed", 1.0)), "response_format": "mp3",
                "metadata": {"output_format": "url"}}
        code, content, headers = pt.request("POST", "/v1/audio/speech", body, cred=cred, timeout=300, raw=True)
        url, parsed = pt.speech_audio_url(code, content, headers)
        out = wd / "voiceover" / ("%s.mp3" % key)
        if not url:
            pt.raise_for(code, parsed, "Voiceover %s" % key)
        st["output"] = pt.download(url, out)
        st["status"] = "done"
        save_state(spec, state)
        done.append(key)
    return done


def cmd_run(spec, approve, parallel):
    p = plan(spec)
    if approve is None or abs(float(approve) - p["video_est_usd"]) > 0.005:
        raise pt.PTError("Refusing to spend: run `plan` first, show the user the estimate "
                         "(video_est_usd=%.2f plus not_estimated items), get a yes, then pass "
                         "--approve-estimate %.2f" % (p["video_est_usd"], p["video_est_usd"]),
                         "NEEDS_APPROVAL", 6)
    cred, _ = pt.get_credential()
    wd = Path(spec["_workdir"])
    wd.mkdir(parents=True, exist_ok=True)
    state = load_state(spec)
    results, failures = {}, {}
    with cf.ThreadPoolExecutor(max_workers=max(1, min(parallel, 4))) as ex:
        futs = {ex.submit(run_shot, spec, shot, cred, state, wd): shot["id"] for shot in spec["shots"]}
        for f in cf.as_completed(futs):
            sid = futs[f]
            try:
                results[sid] = f.result()[1]
            except pt.PTError as exc:
                failures[sid] = {"error_type": exc.kind, "error": str(exc)}
                if exc.kind in ("INSUFFICIENT_CREDITS", "AUTH", "NO_CREDENTIAL"):
                    for other in futs:
                        other.cancel()
    vo = []
    if not failures:
        vo = run_voiceover(spec, cred, state, wd)
    out = {"ok": not failures, "done": results, "failed": failures, "voiceover": vo, "state": str(state_path(spec))}
    if failures:
        out["next_step"] = "Fix the cause, then run the same command again; finished and submitted shots resume."
    pt.emit(out)
    return 0 if not failures else 4


def cmd_status(spec):
    state = load_state(spec)
    rows = []
    for shot in spec["shots"]:
        st = state["shots"].get(shot["id"], {})
        rows.append({"id": shot["id"], "status": st.get("status", "pending"), "task_id": st.get("task_id"),
                     "output": st.get("output"), "error": st.get("error")})
    pt.emit({"project": spec["project"], "shots": rows, "voiceover": state.get("voiceover", {})})


# ------------------------------------------------------------------ assembly (ffmpeg, no credits)
def srt_time(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def build_srt(spec, durations):
    entries, t = [], 0.0
    for shot, d in zip(spec["shots"], durations):
        cap = shot.get("caption")
        if cap:
            entries.append("%d\n%s --> %s\n%s\n" % (len(entries) + 1, srt_time(t), srt_time(t + d), cap))
        t += d
    return "\n".join(entries)


def ffmpeg_cmds(spec, clips, durations, vo_files, out, burn=True, keep_clip_audio=True):
    ratio = spec["defaults"].get("ratio", "9:16")
    w, h = RATIO_WH.get(ratio, (1080, 1920))
    wd = Path(spec["_workdir"])
    norm_dir = wd / "norm"
    norm = [str(norm_dir / Path(c).name) for c in clips]
    cmds = []
    for c, n in zip(clips, norm):
        cmds.append(["ffmpeg", "-y", "-i", c, "-f", "lavfi", "-t", "60", "-i", "anullsrc=r=48000:cl=stereo",
                     "-filter_complex",
                     "[0:v]scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,"
                     "fps=30,format=yuv420p,setsar=1[v];%s" % (
                         w, h, w, h,
                         "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]" if keep_clip_audio and has_audio(c)
                         else "[1:a]anull[a]"),
                     "-map", "[v]", "-map", "[a]", "-t", "%.3f" % probe_duration(c),
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "48000", n])
    concat_list = wd / "concat.txt"
    joined = str(wd / "joined.mp4")
    cmds.append(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", joined])
    current = joined
    if vo_files:
        vo_cat = wd / "vo_concat.txt"
        vo_joined = str(wd / "voiceover.m4a")
        cmds.append(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(vo_cat), "-c:a", "aac", vo_joined])
        mixed = str(wd / "mixed.mp4")
        duck = spec.get("assembly", {}).get("clip_audio_volume", 0.25)
        cmds.append(["ffmpeg", "-y", "-i", current, "-i", vo_joined, "-filter_complex",
                     "[0:a]volume=%s[bg];[bg][1:a]amix=inputs=2:duration=first:normalize=0[a]" % duck,
                     "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", mixed])
        current = mixed
    srt = build_srt(spec, durations)
    if srt and burn:
        srt_path = str(wd / "captions.srt")
        style = spec.get("assembly", {}).get(
            "caption_style", "FontName=DejaVu Sans,FontSize=14,Outline=2,Shadow=0,MarginV=60,Alignment=2")
        cmds.append(["ffmpeg", "-y", "-i", current, "-vf",
                     "subtitles=%s:force_style='%s'" % (srt_path.replace(":", r"\:").replace("'", r"\'"), style),
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy", out])
    else:
        cmds.append(["ffmpeg", "-y", "-i", current, "-c", "copy", out])
    return cmds, norm, srt


def probe_duration(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def has_audio(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                            "-of", "csv=p=0", path], capture_output=True, text=True, timeout=30)
        return bool(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False


def cmd_assemble(spec, out, burn, dry):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise pt.PTError("ffmpeg/ffprobe not found. Install ffmpeg (brew install ffmpeg / apt install ffmpeg / "
                         "winget install ffmpeg) or deliver clips separately.", "MISSING_FFMPEG", 2)
    state = load_state(spec)
    clips, durations = [], []
    for shot in spec["shots"]:
        st = state["shots"].get(shot["id"], {})
        path = st.get("output") or str(Path(spec["_workdir"]) / "clips" / ("%s.mp4" % shot["id"]))
        if not Path(path).is_file():
            raise pt.PTError("Clip for %s missing (%s). Run `run` first." % (shot["id"], path), "BAD_REQUEST", 3)
        clips.append(path)
        durations.append(probe_duration(path) or float(shot_settings(spec, shot)["duration"]))
    vo_files = [v["output"] for v in state.get("voiceover", {}).values() if v.get("output")]
    wd = Path(spec["_workdir"])
    out = out or str(wd / ("%s-final.mp4" % spec["project"]))
    cmds, norm, srt = ffmpeg_cmds(spec, clips, durations, vo_files, out, burn)
    if dry:
        pt.emit({"dry_run": True, "commands": [" ".join(c) for c in cmds]})
        return 0
    (wd / "norm").mkdir(parents=True, exist_ok=True)
    (wd / "concat.txt").write_text("".join("file '%s'\n" % n.replace("'", r"'\''") for n in norm), encoding="utf-8")
    if vo_files:
        (wd / "vo_concat.txt").write_text("".join("file '%s'\n" % v for v in vo_files), encoding="utf-8")
    if srt:
        (wd / "captions.srt").write_text(srt, encoding="utf-8")
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True)
        if r.returncode != 0:
            raise pt.PTError("ffmpeg failed: %s\n%s" % (" ".join(c[:6]), r.stderr[-800:]), "FFMPEG")
    pt.emit({"ok": True, "output": str(Path(out).resolve()), "duration_s": round(probe_duration(out), 2),
             "captions": str(wd / "captions.srt") if srt else None})
    return 0


def cmd_reformat(src, ratio, mode, out):
    if ratio not in RATIO_WH:
        raise pt.PTError("ratio must be one of %s" % ", ".join(RATIO_WH), "BAD_REQUEST", 3)
    if not shutil.which("ffmpeg"):
        raise pt.PTError("ffmpeg not found.", "MISSING_FFMPEG", 2)
    w, h = RATIO_WH[ratio]
    vf = ("scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d" if mode == "crop" else
          "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black") % (w, h, w, h)
    out = out or str(Path(src).with_name("%s-%s.mp4" % (Path(src).stem, ratio.replace(":", "x"))))
    r = subprocess.run(["ffmpeg", "-y", "-i", src, "-vf", vf + ",setsar=1", "-c:v", "libx264", "-preset",
                        "veryfast", "-crf", "20", "-c:a", "copy", out], capture_output=True, text=True)
    if r.returncode != 0:
        raise pt.PTError("ffmpeg failed: %s" % r.stderr[-500:], "FFMPEG")
    pt.emit({"ok": True, "output": str(Path(out).resolve()), "ratio": ratio, "mode": mode})
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "plan", "status"):
        sp = sub.add_parser(name)
        sp.add_argument("shotlist")
        if name in ("validate", "plan"):
            sp.add_argument("--require-product-bible", action="store_true",
                            help="refuse if product_bible missing (also auto when kind=product-ad)")
    r = sub.add_parser("run")
    r.add_argument("shotlist")
    r.add_argument("--approve-estimate", type=float, help="the video_est_usd from `plan`, after the user agreed")
    r.add_argument("--parallel", type=int, default=2, help="concurrent shots (1-4)")
    r.add_argument("--require-product-bible", action="store_true",
                   help="refuse if product_bible missing (also auto when kind=product-ad)")
    a = sub.add_parser("assemble")
    a.add_argument("shotlist")
    a.add_argument("-o", "--output")
    a.add_argument("--no-captions", action="store_true", help="skip burning captions (captions.srt still written)")
    a.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("reformat")
    f.add_argument("video")
    f.add_argument("--ratio", required=True)
    f.add_argument("--mode", choices=["crop", "pad"], default="crop")
    f.add_argument("-o", "--output")
    args = ap.parse_args()
    if args.cmd == "reformat":
        return cmd_reformat(args.video, args.ratio, args.mode, args.output)
    spec = load(args.shotlist)
    require_pb = bool(getattr(args, "require_product_bible", False))
    errors = validate(spec, require_product_bible=require_pb)
    if args.cmd == "validate" or errors:
        pt.emit({"ok": not errors, "errors": errors, "shots": len(spec["shots"])})
        return 0 if not errors else 3
    if args.cmd == "plan":
        p = plan(spec)
        Path(spec["_workdir"]).mkdir(parents=True, exist_ok=True)
        (Path(spec["_workdir"]) / "plan.json").write_text(json.dumps(p, indent=2), encoding="utf-8")
        p["next_step"] = ("Show this estimate to the user. After they agree: pipeline.py run %s "
                          "--approve-estimate %.2f" % (args.shotlist, p["video_est_usd"]))
        pt.emit(p)
        return 0
    if args.cmd == "run":
        return cmd_run(spec, args.approve_estimate, args.parallel)
    if args.cmd == "status":
        return cmd_status(spec)
    return cmd_assemble(spec, args.output, not args.no_captions, args.dry_run)


if __name__ == "__main__":
    pt.run(main)
