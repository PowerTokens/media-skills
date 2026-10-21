#!/usr/bin/env python3
"""Text-to-speech via PowerTokens POST /v1/audio/speech (MiniMax speech models).

Examples:
  python3 speech.py -t "Meet the bottle that keeps coffee hot for 12 hours." --voice English_Trustworthy_Man
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
    body = {"model": a.model, "input": text, "voice": a.voice, "speed": a.speed,
            "response_format": a.format, "metadata": {"output_format": "url"}}
    if a.dry_run:
        pt.emit({"dry_run": True, "endpoint": pt.API_BASE + "/v1/audio/speech", "body": body})
        return 0
    cred, _ = pt.get_credential()
    code, content, headers = pt.request("POST", "/v1/audio/speech", body, cred=cred, timeout=300, raw=True)
    out = a.output or pt.default_output("speech", a.format)
    url, parsed = pt.speech_audio_url(code, content, headers)
    if url:
        path = pt.download(url, out)  # temporary file URL; no credential forwarded
    elif code == 200 and content and content[:1] not in (b"{", b"["):
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(content)
        path = str(Path(out).resolve())
    else:
        pt.raise_for(code, parsed, "Speech")
    pt.emit({"ok": True, "model": a.model, "voice": a.voice, "characters": len(text), "output": path})
    return 0


if __name__ == "__main__":
    pt.run(main)
