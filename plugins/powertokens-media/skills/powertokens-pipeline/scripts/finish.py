#!/usr/bin/env python3
"""Finishing / polish layer for PowerTokens videos (Python stdlib + ffmpeg, no credits).

  python3 finish.py finish shots.json [--preset clean-premium|ugc-punchy|cinematic] [-o out.mp4]
  python3 finish.py music out.wav --seconds 15 --bpm 100 [--mood warm|punchy|dark]
  python3 finish.py stills final.mp4 [--every 0.5]          # contact sheet for self-review
  python3 finish.py presets

Reads finished clips + voiceover from <workdir>/state.json (written by pipeline.py) and the optional
"finish" block of the shot list. Applies: beat-snapped cuts, punch-in, color grade, xfade transitions,
light-leak flashes, grain + vignette, hook title, kinetic word-pop captions in the safe zone,
end card (product, headline, price, CTA, logo slot), music bed ducked under the voiceover and
loudness normalisation (-14 LUFS). Music is synthesised locally (no third-party audio).
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
FONT_DIRS = [HERE.parent / "assets" / "fonts", HERE.parent.parent / "assets" / "fonts"]

PRESETS = {
    "clean-premium": dict(
        bpm=96, mood="warm", transitions=["fade", "smoothup", "zoomin", "fade"], tdur_beats=0.5,
        punch=0.07, grade="eq=contrast=1.06:saturation=1.10:gamma=0.98,"
                          "curves=all='0/0.02 0.5/0.5 1/0.97',colortemperature=temperature=6200:mix=0.25",
        grain=5, vignette="PI/5", leaks=True, accent="&H0040C8FF", text="&H00FFFFFF",
        font="Poppins ExtraBold", font2="Poppins SemiBold", caption_size=78, music_db=-17, upper=False),
    "ugc-punchy": dict(
        bpm=120, mood="punchy", transitions=["zoomin", "slideleft", "zoomin", "slideright"], tdur_beats=0.3,
        punch=0.12, grade="eq=contrast=1.04:saturation=1.18", grain=0, vignette=None, leaks=False,
        accent="&H0000E5FF", text="&H00FFFFFF", font="Poppins ExtraBold", font2="Poppins SemiBold",
        caption_size=88, music_db=-16, upper=True),
    "cinematic": dict(
        bpm=80, mood="dark", transitions=["fadeblack", "dissolve", "fade", "fadeblack"], tdur_beats=0.75,
        punch=0.05, grade="eq=contrast=1.12:saturation=0.95:gamma=0.97,"
                          "colorbalance=rs=-0.04:bs=0.06:rh=0.06:bh=-0.05",
        grain=9, vignette="PI/4", leaks=True, accent="&H0070B8FF", text="&H00F2F2F2",
        font="Poppins SemiBold", font2="Poppins Medium", caption_size=70, music_db=-16, upper=False),
}
# Safe zone for 9:16 feeds: keep text out of the top ~12% and bottom ~25% (platform UI) and the
# right ~12% (action buttons). Captions sit at 60% height, centered on the left 88%.
CAPTION_Y = int(H * 0.60)
CAPTION_X = int(W * 0.47)


def run(cmd, what):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise pt.PTError("%s failed: %s" % (what, r.stderr[-1200:]), "FFMPEG")
    return r


def probe(path, entry="format=duration"):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entry, "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip().split("\n")[0].split(",")[0])
    except ValueError:
        return 0.0


def font_dir():
    for d in FONT_DIRS:
        if d.is_dir():
            return d
    return None


# ------------------------------------------------------------------ music (self-generated)
def make_music(out, seconds, bpm=96, mood="warm"):
    """Synthesised bed: chord pad + soft kick on each beat + hats on off-beats. Royalty-free by
    construction (generated here, MIT like the rest of this repo)."""
    beat = 60.0 / bpm
    roots = {"warm": [220.0, 174.61, 261.63, 196.0], "punchy": [196.0, 155.56, 233.08, 174.61],
             "dark": [146.83, 116.54, 130.81, 110.0]}[mood]
    bar = beat * 4
    # chord per bar (root, maj3/min3, fifth) chosen by bar index
    root = "(if(lt(mod(t,%f),%f),%f,if(lt(mod(t,%f),%f),%f,if(lt(mod(t,%f),%f),%f,%f))))" % (
        bar * 4, bar, roots[0], bar * 4, bar * 2, roots[1], bar * 4, bar * 3, roots[2], roots[3])
    third = "1.2599" if mood != "dark" else "1.1892"
    pad = ("0.10*sin(2*PI*{r}*t)+0.07*sin(2*PI*{r}*{th}*t)+0.07*sin(2*PI*{r}*1.4983*t)"
           "+0.04*sin(2*PI*{r}*2*t+sin(2*PI*0.5*t))").format(r=root, th=third)
    tb = "mod(t,%f)" % beat
    kick = "0.55*sin(2*PI*(45+90*exp(-%s*30))*%s)*exp(-%s*9)" % (tb, tb, tb)
    hat = "0.05*(random(0)*2-1)*exp(-mod(t+%f,%f)*60)" % (beat / 2, beat)
    fade = "min(1,t/1.5)*min(1,(%f-t)/1.5)" % seconds
    expr = "(%s+%s+%s)*%s" % (pad, kick, hat, fade)
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc='%s':s=48000:d=%f" % (expr, seconds),
         "-af", "lowpass=f=9000,highpass=f=35,acompressor=threshold=-18dB:ratio=3,"
                "aecho=0.8:0.5:60:0.15,volume=0.9", "-ac", "2", str(out)], "music")
    return str(out)


# ------------------------------------------------------------------ ASS (titles, captions, end card)
def ass_time(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def esc(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def ass_header(p):
    return """[Script Info]
ScriptType: v4.00+
PlayResX: %d
PlayResY: %d
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,%s,%d,%s,%s,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,5,3,5,60,160,0,1
Style: Hook,%s,118,%s,%s,&H00101010,&H90000000,0,0,0,0,100,100,-1,0,1,0,6,5,60,60,0,1
Style: Sub,%s,46,%s,%s,&H00101010,&H90000000,0,0,0,0,100,100,2,0,1,0,4,5,60,60,0,1
Style: Card,%s,92,%s,%s,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,0,4,5,60,60,0,1
Style: Price,%s,84,%s,%s,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,0,3,5,60,60,0,1
Style: Btn,%s,50,&H00101010,&H00101010,&H00101010,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,60,60,0,1
Style: Box,%s,10,%s,%s,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" % (W, H, p["font"], p["caption_size"], p["text"], p["accent"],
       p["font"], p["text"], p["accent"], p["font2"], p["text"], p["accent"],
       p["font"], p["text"], p["accent"], p["font"], p["accent"], p["accent"],
       p["font"], p["font"], p["accent"], p["accent"])


def word_pop_events(text, start, end, p, max_chars=16):
    """Kinetic captions: words pop in one by one; the active word is accent-colored and bigger.
    Lines wrap at ~max_chars; each line group shows only while spoken."""
    words = text.split()
    if not words:
        return []
    if p.get("upper"):
        words = [w.upper() for w in words]
    groups, cur = [], []
    for w in words:
        if cur and len(" ".join(cur + [w])) > max_chars:
            groups.append(cur)
            cur = []
        cur.append(w)
    groups.append(cur)
    total_chars = sum(len(w) + 1 for w in words)
    dur = max(0.4, end - start)
    events, t = [], start
    for g in groups:
        g_chars = sum(len(w) + 1 for w in g)
        g_dur = dur * g_chars / total_chars
        g_start, g_end = t, t + g_dur
        wt = g_start
        for i, w in enumerate(g):
            w_dur = g_dur * (len(w) + 1) / g_chars
            w_end = g_end + 0.25 if i == len(g) - 1 else wt + w_dur
            parts = []
            for j, x in enumerate(g):
                if j < i:
                    parts.append("{\\c%s\\fscx100\\fscy100}%s" % (p["text"], esc(x)))
                elif j == i:
                    parts.append("{\\c%s\\fscx118\\fscy118\\t(0,110,\\fscx106\\fscy106)}%s" % (p["accent"], esc(x)))
                else:
                    parts.append("{\\alpha&HFF&}%s" % esc(x))
            pos = "{\\an5\\pos(%d,%d)}" % (CAPTION_X, CAPTION_Y)
            fade = "{\\fad(60,0)}" if i == 0 else ""
            events.append("Dialogue: 2,%s,%s,Cap,,0,0,0,,%s%s%s" % (
                ass_time(wt), ass_time(w_end), pos, fade, "{\\r} ".join(parts)))
            wt += w_dur
        t = g_end
    return events


def hook_events(hook, p):
    t0, t1 = hook.get("start", 0.15), hook.get("end", 1.9)
    text = esc(hook["text"].upper() if p.get("upper") else hook["text"])
    ev = ["Dialogue: 3,%s,%s,Hook,,0,0,0,,{\\an5\\move(%d,%d,%d,%d,0,260)\\fad(120,200)"
          "\\t(0,260,\\fscx100\\fscy100)\\fscx86\\fscy86}%s" % (
              ass_time(t0), ass_time(t1), W // 2, int(H * 0.22) + 40, W // 2, int(H * 0.22), text)]
    if hook.get("sub"):
        ev.append("Dialogue: 3,%s,%s,Sub,,0,0,0,,{\\an5\\pos(%d,%d)\\fad(250,200)}%s" % (
            ass_time(t0 + 0.25), ass_time(t1), W // 2, int(H * 0.22) + 95, esc(hook["sub"])))
    return ev


def rounded_rect(w, h, r):
    k = 0.55 * r
    return ("m %d 0 l %d 0 b %d 0 %d %d %d %d l %d %d b %d %d %d %d %d %d l %d %d b %d %d 0 %d 0 %d "
            "l 0 %d b 0 %d %d 0 %d 0" % (
                r, w - r, w - r + k, w, r - k, w, r, w, h - r, w, h - r + k, w - r + k, h, w - r, h,
                r, h, r - k, h, h - r + k, h - r, r, r - k, r - k, r))


def end_card_events(card, t0, t1, p):
    ev = []
    y = int(H * 0.66)
    if card.get("headline"):
        ev.append("Dialogue: 4,%s,%s,Card,,0,0,0,,{\\an5\\pos(%d,%d)\\fad(200,0)\\blur0.6}%s" % (
            ass_time(t0 + 0.1), ass_time(t1), W // 2, y, esc(card["headline"])))
    if card.get("price"):
        ev.append("Dialogue: 4,%s,%s,Price,,0,0,0,,{\\an5\\pos(%d,%d)\\fad(200,0)\\t(0,200,\\fscx100\\fscy100)"
                  "\\fscx70\\fscy70}%s" % (ass_time(t0 + 0.35), ass_time(t1), W // 2, y + 110, esc(card["price"])))
    if card.get("cta"):
        bw, bh = 520, 112
        bx, by = (W - bw) // 2, y + 190
        ev.append("Dialogue: 4,%s,%s,Box,,0,0,0,,{\\an7\\pos(%d,%d)\\1c%s\\fad(200,0)\\p1}%s{\\p0}" % (
            ass_time(t0 + 0.55), ass_time(t1), bx, by, p["accent"], rounded_rect(bw, bh, 56)))
        ev.append("Dialogue: 5,%s,%s,Btn,,0,0,0,,{\\an5\\pos(%d,%d)\\fad(200,0)}%s" % (
            ass_time(t0 + 0.55), ass_time(t1), W // 2, by + bh // 2, esc(card["cta"])))
    if card.get("wordmark") and not card.get("logo"):
        ev.append("Dialogue: 4,%s,%s,Sub,,0,0,0,,{\\an5\\pos(%d,%d)\\fad(250,0)\\fsp12}%s" % (
            ass_time(t0 + 0.2), ass_time(t1), W // 2, int(H * 0.12), esc(card["wordmark"])))
    return ev


# ------------------------------------------------------------------ video stages
def beat_snap(d, beat, min_beats=3):
    n = max(min_beats, int(math.floor(d / beat + 1e-6)))
    return round(min(d, n * beat), 3)


def prep_clip(src, out, dur, p, idx):
    z = p["punch"]
    # punch-in: scale grows linearly over the cut, then center-crop to 1080x1920
    zoom = "(1+%f*t/%f)" % (z, max(dur, 0.1)) if idx % 2 == 0 else "(1+%f-%f*t/%f)" % (z, z * 0.6, max(dur, 0.1))
    vf = ("scale=%d:%d:force_original_aspect_ratio=increase,"
          "scale=w='trunc(%d*%s/2)*2':h='trunc(%d*%s/2)*2':eval=frame,crop=%d:%d,"
          "fps=%d,%s,format=yuv420p,setsar=1" % (W, H, W, zoom, H, zoom, W, H, FPS, p["grade"]))
    run(["ffmpeg", "-y", "-i", str(src), "-t", "%.3f" % dur, "-vf", vf, "-an", "-c:v", "libx264",
         "-preset", "medium", "-crf", "16", str(out)], "prep %s" % src)


def end_card_bg(still, out, dur, p):
    """Background for the end card: blurred, darkened still + sharp product image with soft shadow."""
    vf = ("[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,gblur=sigma=28,"
          "eq=brightness=-0.16:saturation=0.9[bg];"
          "[1:v]scale=%d:-2,format=rgba[fg];"
          "[fg]split[fgs][fgm];[fgs]colorchannelmixer=rr=0:gg=0:bb=0:aa=0.55,gblur=sigma=18[sh];"
          "[bg][sh]overlay=(W-w)/2+10:%d+24[b2];[b2][fgm]overlay=(W-w)/2:%d,"
          "zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=%d,"
          "%s,format=yuv420p,setsar=1" % (W, H, W, H, int(W * 0.56), int(H * 0.17), int(H * 0.17),
                                         W, H, FPS, p["grade"]))
    run(["ffmpeg", "-y", "-loop", "1", "-t", "%.3f" % dur, "-i", str(still), "-loop", "1", "-t", "%.3f" % dur,
         "-i", str(still), "-filter_complex", vf, "-t", "%.3f" % dur, "-c:v", "libx264", "-preset", "medium",
         "-crf", "16", str(out)], "end card")


def assemble_video(parts, cuts, trans, tdur, out):
    inputs = []
    for prt in parts:
        inputs += ["-i", str(prt)]
    if len(parts) == 1:
        shutil.copy(parts[0], out)
        return [0.0]
    chain, last, offset, starts = [], "[0:v]", 0.0, [0.0]
    for i in range(1, len(parts)):
        offset += cuts[i - 1] - tdur
        starts.append(offset)
        label = "[v%d]" % i
        chain.append("%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f%s" % (
            last, i, trans[(i - 1) % len(trans)], tdur, offset, label))
        last = label
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(chain), "-map", last, "-c:v", "libx264",
                                     "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], "xfade")
    return starts


def overlay_fx(src, ass_path, out, p, leak_times, logo=None, logo_t0=None):
    inputs = ["-i", str(src)]
    fc = []
    cur = "[0:v]"
    n = 1
    if p["leaks"]:
        for k, t in enumerate(leak_times):
            inputs += ["-f", "lavfi", "-t", "0.9", "-i",
                       "gradients=s=%dx%d:c0=0xFF8A3D:c1=0xFFD27F:c2=0x000000:x0=0:y0=0:x1=%d:y1=%d:"
                       "speed=0.03:r=%d" % (W, H, W, int(H * 0.8), FPS)]
            fc.append("[%d:v]format=rgba,colorchannelmixer=aa=0.38,fade=t=in:st=0:d=0.3:alpha=1,"
                      "fade=t=out:st=0.5:d=0.4:alpha=1,setpts=PTS-STARTPTS+%f/TB[lk%d]" % (n, max(0, t - 0.45), k))
            fc.append("%s[lk%d]overlay=eof_action=pass:format=auto[o%d]" % (cur, k, k))
            cur = "[o%d]" % k
            n += 1
    if logo:
        inputs += ["-loop", "1", "-i", str(logo)]
        fc.append("[%d:v]scale=360:-1,format=rgba[lg]" % n)
        fc.append("%s[lg]overlay=(W-w)/2:%d:enable='gte(t,%f)'[ol]" % (cur, int(H * 0.08), logo_t0))
        cur = "[ol]"
        n += 1
    post = []
    if p["vignette"]:
        post.append("vignette=angle=%s" % p["vignette"])
    if p["grain"]:
        post.append("noise=alls=%d:allf=t" % p["grain"])
    fd = font_dir()
    sub = "subtitles=filename='%s'%s" % (str(ass_path).replace("'", r"\'").replace(":", r"\:"),
                                          (":fontsdir='%s'" % str(fd).replace(":", r"\:")) if fd else "")
    post.append(sub)
    fc.append("%s%s,format=yuv420p[vout]" % (cur, ",".join(post)))
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[vout]", "-c:v", "libx264",
                                     "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags",
                                     "+faststart", str(out)], "overlay fx")


def mix_audio(video, vo_items, music, total, out, p):
    """vo_items: [(path, start_s)]. Music ducks under VO (sidechain), then loudnorm to -14 LUFS."""
    inputs = ["-i", str(video), "-i", str(music)]
    fc = ["[1:a]atrim=0:%f,volume=%sdB,afade=t=out:st=%f:d=1.2[mus]" % (total, p["music_db"], max(0, total - 1.2))]
    if vo_items:
        labels = []
        for i, (path, start) in enumerate(vo_items):
            inputs += ["-i", str(path)]
            ms = int(start * 1000)
            fc.append("[%d:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,"
                      "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,adelay=%d|%d[vo%d]" % (i + 2, ms, ms, i))
            labels.append("[vo%d]" % i)
        fc.append("%samix=inputs=%d:normalize=0:duration=longest,apad=whole_dur=%f[vo]" % ("".join(labels), len(labels), total))
        fc.append("[vo]asplit[vo1][vo2]")
        fc.append("[mus][vo2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck]")
        fc.append("[duck][vo1]amix=inputs=2:normalize=0:duration=first,"
                  "loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
    else:
        fc.append("[mus]loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[aout]",
                                     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                                     "-t", "%.3f" % total, "-movflags", "+faststart", str(out)], "audio mix")


# ------------------------------------------------------------------ finish command
def finish(shotlist, preset=None, out=None, keep=False):
    import pipeline
    if not shutil.which("ffmpeg"):
        raise pt.PTError("ffmpeg not found; install it to use finishing.", "MISSING_FFMPEG", 2)
    spec = pipeline.load(shotlist)
    verrs = pipeline.validate(spec)
    if verrs:
        raise pt.PTError("Shot list invalid (claims/bible/schema): " + "; ".join(verrs), "BAD_REQUEST", 3)
    cfg = spec.get("finish", {})
    p = dict(PRESETS[preset or cfg.get("preset", "clean-premium")])
    p.update({k: v for k, v in cfg.get("overrides", {}).items()})
    state = pipeline.load_state(spec)
    wd = Path(spec["_workdir"])
    fx = wd / "finish"
    fx.mkdir(parents=True, exist_ok=True)
    beat = 60.0 / cfg.get("bpm", p["bpm"])
    tdur = round(beat * p["tdur_beats"], 3)

    clips, cuts = [], []
    for shot in spec["shots"]:
        st = state["shots"].get(shot["id"], {})
        src = st.get("output")
        if not src or not Path(src).is_file():
            raise pt.PTError("Clip for %s missing; run the pipeline first." % shot["id"], "BAD_REQUEST", 3)
        d = probe(src)
        cut = shot.get("cut") or beat_snap(d - 0.05, beat)
        clips.append(src)
        cuts.append(min(cut, d))
    parts = []
    for i, (src, cut) in enumerate(zip(clips, cuts)):
        o = fx / ("p%02d.mp4" % i)
        prep_clip(src, o, cut, p, i)
        parts.append(o)

    card = cfg.get("end_card")
    card_dur = 0.0
    if card:
        card_dur = card.get("duration", round(beat * 4, 3))
        still = card.get("product_image")
        if still:
            still = pipeline.resolve_path(spec, still)
        else:
            last = spec["shots"][-1]["id"]
            still = state["shots"].get(last, {}).get("keyframe")
            if not still:
                still = str(fx / "last.png")
                run(["ffmpeg", "-y", "-sseof", "-0.2", "-i", clips[-1], "-frames:v", "1", still], "last frame")
        o = fx / "endcard.mp4"
        end_card_bg(still, o, card_dur + tdur, p)
        parts.append(o)
        cuts.append(card_dur + tdur)
    trans = list(p["transitions"])
    joined = fx / "joined.mp4"
    starts = assemble_video(parts, cuts, trans, tdur, joined)
    total = probe(joined)

    # voiceover timing: line i starts shortly after shot i starts (lines beyond shots follow on)
    vo_state = state.get("voiceover", {})
    vo_lines = (spec.get("voiceover") or {}).get("lines", [])
    vo_items, ass_events, vo_missing = [], [], []
    t_next = 0.0
    for i, line in enumerate(vo_lines):
        key = line.get("id") or "vo%02d" % (i + 1)
        vst = vo_state.get(key, {})
        path = vst.get("output")
        if not path or not Path(path).is_file() or vst.get("status") == "content_policy":
            if line.get("text"):
                vo_missing.append({"id": key, "text": line.get("text"),
                                   "error_type": vst.get("error_type") or (
                                       "CONTENT_POLICY" if vst.get("status") == "content_policy" else None),
                                   "rejected_text": vst.get("rejected_text")})
            continue
        start = max(t_next, (starts[i] if i < len(spec["shots"]) else t_next) + line.get("offset", 0.2))
        d = probe(path)
        vo_items.append((path, start))
        ass_events += word_pop_events(line.get("caption", line["text"]), start, start + d, p)
        t_next = start + d + 0.1
    if not vo_items:  # no VO: use shot captions as kinetic text
        for i, shot in enumerate(spec["shots"]):
            if shot.get("caption"):
                ass_events += word_pop_events(shot["caption"], starts[i] + 0.15, starts[i] + cuts[i] - tdur, p)
    if cfg.get("hook"):
        ass_events = hook_events(cfg["hook"], p) + ass_events
    card_t0 = starts[-1] if card else total
    if card:
        ass_events = [e for e in ass_events if not _starts_after(e, card_t0 + 0.05)] + \
                     end_card_events(card, card_t0, total, p)
    ass_path = fx / "titles.ass"
    ass_path.write_text(ass_header(p) + "\n".join(ass_events) + "\n", encoding="utf-8")

    leak_times = starts[1:] if p["leaks"] else []
    graded = fx / "graded.mp4"
    logo = pipeline.resolve_path(spec, card["logo"]) if card and card.get("logo") else None
    overlay_fx(joined, ass_path, graded, p, leak_times, logo, card_t0)

    music_cfg = cfg.get("music", {})
    music = pipeline.resolve_path(spec, music_cfg["path"]) if music_cfg.get("path") else \
        make_music(fx / "music.wav", total + 0.5, cfg.get("bpm", p["bpm"]), music_cfg.get("mood", p["mood"]))
    out = out or str(wd / ("%s-finished.mp4" % spec["project"]))
    mix_audio(graded, vo_items, music, total, out, p)
    if not keep:
        for f in parts + [joined]:
            Path(f).unlink(missing_ok=True)
    result = {"ok": True, "output": str(Path(out).resolve()), "duration_s": round(probe(out), 2),
              "preset": preset or cfg.get("preset", "clean-premium"), "cuts_s": cuts, "transition_s": tdur,
              "bpm": cfg.get("bpm", p["bpm"]), "subtitles": str(ass_path),
              "music": "self-generated (finish.py make_music, MIT)" if not music_cfg.get("path") else music}
    if vo_missing:
        result["voiceover_missing"] = vo_missing
        result["partial_voiceover"] = True
    return result


def _starts_after(event, t):
    try:
        start = event.split(",")[1]
        h, m, s = start.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s) >= t
    except (IndexError, ValueError):
        return False


def stills(video, every, out_dir=None):
    out_dir = Path(out_dir or Path(video).with_suffix("")).with_name(Path(video).stem + "-stills")
    out_dir.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(video), "-vf", "fps=1/%f,scale=270:-2" % every, str(out_dir / "f%03d.jpg")], "stills")
    sheet = out_dir / "contact.jpg"
    n = len(list(out_dir.glob("f*.jpg")))
    cols = 6
    run(["ffmpeg", "-y", "-i", str(out_dir / "f%03d.jpg"), "-vf",
         "tile=%dx%d:padding=6:color=white" % (cols, max(1, math.ceil(n / cols))), "-frames:v", "1", str(sheet)],
        "contact sheet")
    return {"ok": True, "frames": n, "dir": str(out_dir), "contact_sheet": str(sheet)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("finish")
    f.add_argument("shotlist")
    f.add_argument("--preset", choices=list(PRESETS))
    f.add_argument("-o", "--output")
    f.add_argument("--keep-intermediate", action="store_true")
    m = sub.add_parser("music")
    m.add_argument("output")
    m.add_argument("--seconds", type=float, default=15)
    m.add_argument("--bpm", type=float, default=96)
    m.add_argument("--mood", choices=["warm", "punchy", "dark"], default="warm")
    s = sub.add_parser("stills")
    s.add_argument("video")
    s.add_argument("--every", type=float, default=0.5)
    sub.add_parser("presets")
    a = ap.parse_args()
    if a.cmd == "presets":
        pt.emit({k: {kk: v[kk] for kk in ("bpm", "transitions", "punch", "grain", "leaks")} for k, v in PRESETS.items()})
    elif a.cmd == "music":
        pt.emit({"ok": True, "output": make_music(a.output, a.seconds, a.bpm, a.mood)})
    elif a.cmd == "stills":
        pt.emit(stills(a.video, a.every))
    else:
        pt.emit(finish(a.shotlist, a.preset, a.output, a.keep_intermediate))
    return 0


if __name__ == "__main__":
    pt.run(main)
