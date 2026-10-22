#!/usr/bin/env python3
"""Text-to-speech via PowerTokens POST /v1/audio/speech (MiniMax speech models).

Examples:
  python3 speech.py -t "Meet the bottle that keeps coffee hot for 12 hours." --voice English_Trustworthy_Man
  python3 speech.py --split-lines --segment en -f lines.txt -o outputs/vo.mp3
  python3 speech.py -f script.txt --voice English_Graceful_Lady --speed 1.1 --format wav
  python3 speech.py --list-voices
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

DEFAULT_MODEL = "speech-2.8-turbo"
MODELS = ["speech-2.8-turbo", "speech-2.8-hd", "speech-2.6-turbo", "speech-2.6-hd", "speech-02-turbo", "speech-02-hd"]
# English subset of the documented voice list (docs.powertokens.ai speech-2.8-turbo). Full list: see docs.
VOICES = {
    "English_Trustworthy_Man": "en, male, warm narrator",
    "English_Graceful_Lady": "en, female, calm/elegant",
    "English_Aussie_Bloke": "en, male, Australian",
    "English_Whispering_girl": "en, female, whisper/ASMR",
    "English_Diligent_Man": "en, male, energetic",
    "English_Gentle-voiced_man": "en, male, soft",
    "Chinese (Mandarin)_News_Anchor": "zh, news anchor",
    "Chinese (Mandarin)_Lyrical_Voice": "zh, lyrical female",
}
DEFAULT_VOICE = "English_Trustworthy_Man"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-t", "--text")
    ap.add_argument("-f", "--file", help="UTF-8 text file (max 10,000 chars)")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL)
    ap.add_argument("-v", "--voice", default=DEFAULT_VOICE)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav"])
    ap.add_argument("-o", "--output")
    ap.add_argument("--segment", help="segment id included in errors and in the default filename")
    ap.add_argument("--split-lines", action="store_true",
                    help="one TTS call per non-empty line (multi-line ads). A content-policy block stays on that line.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()
    if a.list_voices:
        pt.emit({"default_model": DEFAULT_MODEL, "models": MODELS, "default_voice": DEFAULT_VOICE, "voices": VOICES,
                 "full_list": "https://docs.powertokens.ai/en/zmodelAudio/minimax/speech-2.8-turbo?" + pt.UTM})
        return 0
    text = a.text if a.text else (Path(a.file).read_text(encoding="utf-8") if a.file else "")
    if not text.strip():
        raise pt.PTError("Give --text or --file.", "BAD_REQUEST", 3)
    if len(text) > 10000:
        raise pt.PTError("Text is %d chars; the limit is 10,000. Split it." % len(text), "BAD_REQUEST", 3)
    segments = split_segments(text, a.split_lines, a.segment)
    bodies = []
    for sid, line in segments:
        bodies.append((sid, line, speech_body(a.model, line, a.voice, a.speed, a.format)))
    if a.dry_run:
        pt.emit({"dry_run": True, "endpoint": pt.API_BASE + "/v1/audio/speech",
                 "segments": [{"id": sid, "body": body} for sid, _line, body in bodies]})
        return 0
    cred, _ = pt.get_credential()
    if len(bodies) == 1:
        sid, line, body = bodies[0]
        out = a.output or pt.default_output("speech-%s" % sid if a.segment else "speech", a.format)
        path, spoken, rewritten_from = speak_with_policy_retry(cred, body, out, segment_label(sid, line))
        result = {"ok": True, "model": a.model, "voice": a.voice, "segment_id": sid,
                  "characters": len(spoken), "output": path}
        if rewritten_from:
            result["rewritten_from"] = rewritten_from
            result["spoken_text"] = spoken
        pt.emit(result)
        return 0
    done, blocked, rewritten = [], [], []
    stem = Path(a.output).stem if a.output else None
    out_dir = Path(a.output).parent if a.output else Path("outputs")
    for sid, line, body in bodies:
        out = str(out_dir / ("%s-%s.%s" % (stem or "speech", sid, a.format)))
        try:
            path, spoken, rewritten_from = speak_with_policy_retry(
                cred, body, out, segment_label(sid, line))
        except pt.PTError as exc:
            if exc.kind != "CONTENT_POLICY":
                exc.details["segments"] = done
                exc.details["voiceover_blocked"] = blocked
                raise
            blocked.append(blocked_record(sid, line, exc))
            continue
        done.append({"id": sid, "output": path, "characters": len(spoken)})
        if rewritten_from:
            rewritten.append({"id": sid, "rejected_text": rewritten_from, "spoken_text": spoken})
    out = {"ok": not blocked, "model": a.model, "voice": a.voice, "segments": done,
           "voiceover_rewritten": rewritten, "voiceover_blocked": blocked}
    if blocked:
        out["partial"] = True
        out["error_type"] = "CONTENT_POLICY"
        out["next_step"] = POLICY_NEXT_STEP
        pt.emit(out)
        return 7
    pt.emit(out)
    return 0


def speech_body(model, text, voice, speed, fmt):
    return {"model": model, "input": text, "voice": voice, "speed": speed,
            "response_format": fmt, "metadata": {"output_format": "url"}}


def split_segments(text, split_lines, segment_id):
    """One TTS call per non-empty line when --split-lines; otherwise one segment."""
    if split_lines:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            raise pt.PTError("No non-empty lines to speak.", "BAD_REQUEST", 3)
        prefix = segment_id or "line"
        return [("%s-%02d" % (prefix, i + 1), line) for i, line in enumerate(lines)]
    return [(segment_id or "speech", text)]


def segment_label(sid, text):
    snippet = " ".join((text or "").split())
    if len(snippet) > 80:
        snippet = snippet[:77] + "..."
    return '%s ("%s")' % (sid, snippet)


POLICY_NEXT_STEP = (
    "A voiceover segment was blocked by the audio content policy. Other segments are kept. "
    "Show the user the rejected line and the rewrite that was already tried. "
    "Ask them to pick or supply a new line (original product claim only — no lyrics, celebrity names, "
    "verbatim slogans, or long quotes). Do not send the blocked text again. "
    "Assemble only after they accept a partial cut, or a ZH-only cut when bilingual and EN is blocked."
)


def post_speech(cred, body, out_path, label):
    """One /v1/audio/speech call. Raises PTError; CONTENT_POLICY carries rejected_text."""
    code, content, headers = pt.request("POST", "/v1/audio/speech", body, cred=cred, timeout=300, raw=True)
    url, parsed = pt.speech_audio_url(code, content, headers)
    if url:
        return pt.download(url, out_path)  # temporary file URL; no credential forwarded
    if code == 200 and content and content[:1] not in (b"{", b"["):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(content)
        return str(Path(out_path).resolve())
    if not isinstance(parsed, dict):
        parsed = {}
    pt.raise_for(code, parsed, "Speech %s" % label, snippet=body.get("input"))


def speak_with_policy_retry(cred, body, out_path, label):
    """Speak body. On CONTENT_POLICY, rewrite once and retry once.

    Returns (path, spoken_text, rewritten_from or None).
    """
    try:
        path = post_speech(cred, body, out_path, label)
        return path, body.get("input") or "", None
    except pt.PTError as exc:
        if exc.kind != "CONTENT_POLICY":
            raise
        original = body.get("input") or ""
        rewritten = pt.policy_rewrite(original)
        exc.details["rejected_text"] = (exc.details.get("rejected_text") or original)[:500]
        exc.details["segment_id"] = label
        if not rewritten:
            exc.details["rewrite_attempted"] = None
            raise
        retry = dict(body)
        retry["input"] = rewritten
        try:
            path = post_speech(cred, retry, out_path, label + " rewrite")
        except pt.PTError as exc2:
            if exc2.kind == "CONTENT_POLICY":
                exc2.details["rejected_text"] = original[:500]
                exc2.details["rewrite_attempted"] = rewritten
                exc2.details["segment_id"] = label
            raise
        return path, rewritten, original


def blocked_record(sid, line, exc):
    return {
        "id": sid,
        "rejected_text": (exc.details.get("rejected_text") or line)[:500],
        "rewrite_attempted": exc.details.get("rewrite_attempted"),
        "error_type": "CONTENT_POLICY",
        "error": str(exc),
    }


if __name__ == "__main__":
    pt.run(main)
