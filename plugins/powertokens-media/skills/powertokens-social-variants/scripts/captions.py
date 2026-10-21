#!/usr/bin/env python3
"""TikTok/CapCut-style kinetic captions as ASS subtitles (stdlib) + ffmpeg burn-in.

Styles: tiktok (default: white, yellow active word), pill (active word on a colored box),
caps-punch (ALL CAPS, 1-2 words, bounce, keyword emoji), zh (Noto Sans SC Black, 2-4 characters).
Words are timed proportionally inside each voiceover line (the TTS API returns no word timestamps).

  python3 captions.py preview base.mp4 --style tiktok --text "Six a.m. on the trail." --start 0.3 \
      --end 2.9 [--audio vo.mp3] -o out.mp4
"""
import argparse
import re
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

W, H = 1080, 1920
HERE = Path(__file__).resolve().parent
ASSET_DIRS = [HERE.parent / "assets", HERE.parent.parent / "assets"]


def asset_dir():
    for d in ASSET_DIRS:
        if (d / "fonts").is_dir():
            return d
    return None


# ------------------------------------------------------------------ font metrics (tiny TTF/OTF reader)
class Metrics:
    """Advance widths from hmtx + cmap (format 4/12). Falls back to 0.6em per char."""

    def __init__(self, path):
        self.upem, self.adv, self.cmap, self.line = 1000, [], {}, 1.0
        try:
            self._load(Path(path).read_bytes())
        except (OSError, struct.error, KeyError, IndexError):
            pass

    def _load(self, b):
        n = struct.unpack(">H", b[4:6])[0]
        t = {b[12 + 16 * i:16 + 16 * i].decode("latin1"): struct.unpack(">II", b[20 + 16 * i:28 + 16 * i])
             for i in range(n)}
        self.upem = struct.unpack(">H", b[t["head"][0] + 18:t["head"][0] + 20])[0]
        hh = t["hhea"][0]
        asc, desc = struct.unpack(">hh", b[hh + 4:hh + 8])
        self.line = (asc - desc) / float(self.upem)  # libass maps font size to ascender+descender
        if "OS/2" in t:
            o2 = t["OS/2"][0]
            wa, wd = struct.unpack(">HH", b[o2 + 74:o2 + 78])
            if wa + wd:
                self.line = (wa + wd) / float(self.upem)
        nh = struct.unpack(">H", b[hh + 34:hh + 36])[0]
        o = t["hmtx"][0]
        self.adv = [struct.unpack(">H", b[o + 4 * i:o + 4 * i + 2])[0] for i in range(nh)]
        c = t["cmap"][0]
        best = None
        for i in range(struct.unpack(">H", b[c + 2:c + 4])[0]):
            pid, eid, off = struct.unpack(">HHI", b[c + 4 + 8 * i:c + 12 + 8 * i])
            fmt = struct.unpack(">H", b[c + off:c + off + 2])[0]
            if pid in (0, 3) and fmt in (4, 12) and (best is None or fmt == 12):
                best = (fmt, c + off)
        fmt, s = best
        if fmt == 4:
            seg = struct.unpack(">H", b[s + 6:s + 8])[0] // 2
            ends = struct.unpack(">%dH" % seg, b[s + 14:s + 14 + 2 * seg])
            p = s + 16 + 2 * seg
            starts = struct.unpack(">%dH" % seg, b[p:p + 2 * seg])
            deltas = struct.unpack(">%dh" % seg, b[p + 2 * seg:p + 4 * seg])
            ro_pos = p + 4 * seg
            ros = struct.unpack(">%dH" % seg, b[ro_pos:ro_pos + 2 * seg])
            for k in range(seg):
                for ch in range(starts[k], min(ends[k], 0x9FFF) + 1):
                    if ch == 0xFFFF:
                        continue
                    if ros[k] == 0:
                        g = (ch + deltas[k]) & 0xFFFF
                    else:
                        a = ro_pos + 2 * k + ros[k] + 2 * (ch - starts[k])
                        g = struct.unpack(">H", b[a:a + 2])[0]
                        g = (g + deltas[k]) & 0xFFFF if g else 0
                    self.cmap[ch] = g
        else:
            ng = struct.unpack(">I", b[s + 12:s + 16])[0]
            for k in range(ng):
                a, e, g0 = struct.unpack(">III", b[s + 16 + 12 * k:s + 28 + 12 * k])
                for ch in range(a, min(e, 0x9FFF) + 1):
                    self.cmap[ch] = g0 + ch - a

    def width(self, text, size):
        if not self.adv:
            return len(text) * 0.6 * size
        total = 0
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                total += self.upem if ord(ch) > 0x2E80 else self.upem * 0.6
            else:
                total += self.adv[min(g, len(self.adv) - 1)]
        return total * size / self.upem / self.line


# ------------------------------------------------------------------ styles
# ASS colours are &HAABBGGRR. Yellow #FFE100 -> &H0000E1FF.
STYLES = {
    "tiktok": dict(font="Poppins ExtraBold", file="Poppins-ExtraBold.ttf", size=215, caps=False, max_words=3,
                   max_chars=16, text="&H00FFFFFF", accent="&H0000E1FF", outline=13, shadow=6, box=False,
                   pop=True, emoji=False, cjk=False, tilt=0),
    "pill": dict(font="Poppins ExtraBold", file="Poppins-ExtraBold.ttf", size=195, caps=False, max_words=3,
                 max_chars=16, text="&H00FFFFFF", accent="&H00FF5C2E", outline=10, shadow=5, box=True,
                 pop=True, emoji=False, cjk=False, tilt=0),
    "caps-punch": dict(font="Poppins ExtraBold", file="Poppins-ExtraBold.ttf", size=250, caps=True, max_words=2,
                       max_chars=12, text="&H00FFFFFF", accent="&H0033FF66", outline=15, shadow=7, box=False,
                       pop=True, emoji=True, cjk=False, tilt=4),
    "zh": dict(font="Noto Sans SC Black", file="NotoSansSC-Black.otf", size=190, caps=False, max_words=4,
               max_chars=4, text="&H00FFFFFF", accent="&H0000E1FF", outline=13, shadow=6, box=False,
               pop=True, emoji=False, cjk=True, tilt=0),
}
# 9:16 safe zone: above TikTok/Reels bottom UI (~25%) and left of the right action rail (~12%).
CENTER_Y = int(H * 0.64)
CENTER_X = int(W * 0.47)
EMOJI = {"hot": "1f525", "fire": "1f525", "coffee": "2615", "fast": "26a1", "trail": "1f3d4",
         "mountain": "1f3d4", "热": "1f525", "咖啡": "2615"}


def t_ass(t):
    cs = int(round(max(0.0, t) * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def header(st, extra_styles=""):
    bs = 3 if st["box"] else 1
    return ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\n"
            "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
            "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: W,{f},{s},{c},{c},&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,{o},{sh},5,0,0,0,1\n"
            "Style: A,{f},{s},{a},{a},&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,{o},{sh},5,0,0,0,1\n"
            "Style: P,{f},{s},&H00FFFFFF,&H00FFFFFF,{a},&H96000000,0,0,0,0,100,100,0,0,{bs},22,0,5,0,0,0,1\n"
            "{x}\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            ).format(f=st["font"], s=st["size"], c=st["text"], a=st["accent"], o=st["outline"], sh=st["shadow"],
                     bs=bs, x=extra_styles) % (W, H)


def tokenize(text, st):
    text = text.upper() if st["caps"] else text
    if st["cjk"]:
        # split on punctuation, then into chunks of <= max_chars characters
        parts = [p for p in re.split(r"[，。！？、,.!?\s]+", text) if p]
        toks = []
        for p in parts:
            n = max(1, round(len(p) / st["max_chars"] + 0.49))
            size = -(-len(p) // n)
            toks += [p[i:i + size] for i in range(0, len(p), size)]
        return [list(t) for t in toks]  # per-character karaoke inside each CJK chunk
    words = text.split()
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= st["max_words"] or len(" ".join(cur + [w])) > st["max_chars"]
                    or cur[-1][-1:] in ".,!?"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def events(text, start, end, style="tiktok", emphasis=(), metrics=None):
    """Return (ass_event_lines, emoji_overlays[(code, t0, t1, x, y)])."""
    st = STYLES[style]
    m = metrics or Metrics(Path(asset_dir() or ".") / "fonts" / st["file"])
    chunks = tokenize(text, st)
    weights = [sum(len(w) + 1 for w in c) for c in chunks]
    total = float(sum(weights)) or 1.0
    span = max(0.3, end - start)
    out, emo, t = [], [], start
    emph = {e.lower().strip(".,!?") for e in emphasis}
    space = m.width(" ", st["size"]) if not st["cjk"] else 0
    for ci, chunk in enumerate(chunks):
        c_dur = span * weights[ci] / total
        c0, c1 = t, t + c_dur
        widths = [m.width(w, st["size"]) for w in chunk]
        line_w = sum(widths) + space * (len(chunk) - 1)
        x = CENTER_X - line_w / 2
        centers = []
        for w in widths:
            centers.append(x + w / 2)
            x += w + space
        wt = c0
        wsum = float(sum(len(w) + 1 for w in chunk))
        for wi, word in enumerate(chunk):
            w_dur = c_dur * (len(word) + 1) / wsum
            w0, w1 = wt, (c1 if wi == len(chunk) - 1 else wt + w_dur)
            key = word.lower().strip(".,!?")
            for j, other in enumerate(chunk):
                # every word of the chunk is drawn for this word's time slot; active one styled
                active = j == wi
                is_emph = other.lower().strip(".,!?") in emph
                pos = "\\an5\\pos(%d,%d)" % (centers[j], CENTER_Y)
                tags = pos
                if wi == 0 and st["pop"]:
                    # chunk entrance: quick scale bounce 70% -> 112% -> 100%
                    tags += "\\fscx70\\fscy70\\t(0,90,\\fscx112\\fscy112)\\t(90,170,\\fscx100\\fscy100)"
                    if st["tilt"]:
                        tags += "\\frz%d\\t(0,160,\\frz0)" % st["tilt"]
                if active and st["pop"] and wi > 0:
                    tags += "\\t(0,80,\\fscx112\\fscy112)\\t(80,160,\\fscx104\\fscy104)"
                if active and st["box"]:
                    sty = "P"
                elif active or is_emph:
                    sty = "A"
                else:
                    sty = "W"
                if is_emph and not active:
                    tags += "\\fscx106\\fscy106"
                out.append("Dialogue: %d,%s,%s,%s,,0,0,0,,{%s}%s" % (
                    1 if sty == "P" else 2, t_ass(w0), t_ass(w1), sty, tags, other.replace("{", "(")))
            if st["emoji"] and key in EMOJI:
                emo.append((EMOJI[key], w0, c1, int(centers[wi]), CENTER_Y - int(st["size"] * 1.25)))
            wt += w_dur
        t = c1
    return out, emo


def burn(src, ass_text, emoji, out, audio=None, dur=None):
    ad = asset_dir()
    ass_path = Path(out).with_suffix(".ass")
    ass_path.write_text(ass_text, encoding="utf-8")
    inputs = ["-i", str(src)]
    fc, cur, n = [], "[0:v]", 1
    for k, (code, t0, t1, x, y) in enumerate(emoji):
        png = ad / "emoji" / ("%s.png" % code) if ad else None
        if not png or not png.is_file():
            continue
        inputs += ["-loop", "1", "-t", "%.2f" % (t1 + 0.1), "-i", str(png)]
        fc.append("[%d:v]scale=190:190,format=rgba,fade=t=in:st=%.2f:d=0.12:alpha=1[e%d]" % (n, t0, k))
        fc.append("%s[e%d]overlay=%d:%d:enable='between(t,%.2f,%.2f)':eof_action=pass[ov%d]" % (
            cur, k, x - 95, y - 95, t0, t1, k))
        cur, n = "[ov%d]" % k, n + 1
    fonts = (":fontsdir='%s'" % str(ad / "fonts").replace(":", r"\:")) if ad else ""
    fc.append("%ssubtitles=filename='%s'%s,format=yuv420p[v]" % (
        cur, str(ass_path).replace("'", r"\'").replace(":", r"\:"), fonts))
    amap = []
    if audio:
        inputs += ["-i", str(audio)]
        amap = ["-map", "%d:a" % n]
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[v]"] + amap + \
          (["-t", "%.2f" % dur] if dur else []) + ["-c:v", "libx264", "-crf", "18", "-preset", "medium",
                                                  "-c:a", "aac", "-shortest" if not dur else "-y", str(out)]
    cmd = [c for c in cmd if c]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise pt.PTError("ffmpeg caption burn failed: %s" % r.stderr[-800:], "FFMPEG")
    return str(Path(out).resolve())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preview")
    p.add_argument("video")
    p.add_argument("--style", choices=list(STYLES), default="tiktok")
    p.add_argument("--text", required=True, action="append", help="repeat for several lines")
    p.add_argument("--start", type=float, action="append", required=True)
    p.add_argument("--end", type=float, action="append", required=True)
    p.add_argument("--emphasis", default="", help="comma-separated keywords to color")
    p.add_argument("--audio")
    p.add_argument("--duration", type=float)
    p.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    st = STYLES[a.style]
    evs, emo = [], []
    for text, s, e in zip(a.text, a.start, a.end):
        ev, em = events(text, s, e, a.style, [x for x in a.emphasis.split(",") if x])
        evs += ev
        emo += em
    out = burn(a.video, header(st) + "\n".join(evs) + "\n", emo, a.output, a.audio, a.duration)
    pt.emit({"ok": True, "output": out, "style": a.style, "events": len(evs), "emoji": len(emo)})
    return 0


if __name__ == "__main__":
    pt.run(main)
