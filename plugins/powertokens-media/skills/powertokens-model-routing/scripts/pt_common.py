"""Shared helpers for PowerTokens media skills (Python 3.8+ stdlib only).

Auth order: POWERTOKENS_API_KEY env var  >  token saved by `pt_login.py login`.
"""
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = os.environ.get("POWERTOKENS_API_BASE", "https://api.powertokens.ai").rstrip("/")
if not API_BASE.startswith("https://"):
    sys.exit("POWERTOKENS_API_BASE must be https:// (your credential is sent there).")

UTM = "utm_source=media-skills&utm_medium=skill&utm_campaign=media-skills"
SIGNUP_URL = "https://powertokens.ai/?" + UTM
KEYS_URL = "https://powertokens.ai/api-keys?" + UTM
BILLING_URL = "https://powertokens.ai/?" + UTM  # TODO: replace with the real top-up page URL
USER_AGENT = "powertokens-media-skills/0.1"

CONFIG_DIR = Path(os.environ.get("POWERTOKENS_CONFIG_DIR")
                  or Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "powertokens")
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"


class PTError(Exception):
    def __init__(self, message, kind="UNKNOWN", exit_code=4, details=None):
        super().__init__(message)
        self.kind, self.exit_code = kind, exit_code
        self.details = details or {}


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def run(main):
    """Run a CLI main(); print errors as JSON with stable error_type and exit codes."""
    try:
        sys.exit(main() or 0)
    except PTError as exc:
        out = {"ok": False, "error_type": exc.kind, "error": str(exc)}
        for key, val in exc.details.items():
            if key in out:
                continue
            if val is None and key != "rewrite_attempted":
                continue
            out[key] = val
        if exc.kind in ("NO_CREDENTIAL", "AUTH"):
            out["next_step"] = ("Run `python3 scripts/pt_login.py login` (browser sign-in) or export "
                                "POWERTOKENS_API_KEY. New here? Sign up: " + SIGNUP_URL)
        if exc.kind == "INSUFFICIENT_CREDITS":
            out["next_step"] = "Top up credits, then retry: " + BILLING_URL
        emit(out)
        sys.exit(exc.exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


# ---------------------------------------------------------------- credentials
def load_saved_token():
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    token = data.get("access_token")
    exp = data.get("expires_at")
    if not token:
        return None
    if exp and time.time() > float(exp) - 60:
        return None  # expired; refresh flow lives in pt_login.py (TODO once PT ships refresh tokens)
    return token


def get_credential():
    key = os.environ.get("POWERTOKENS_API_KEY", "").strip()
    if key:
        return key, "env:POWERTOKENS_API_KEY"
    token = load_saved_token()
    if token:
        return token, "login:" + str(CREDENTIALS_PATH)
    raise PTError("No PowerTokens credential found (no POWERTOKENS_API_KEY and no saved login).",
                  "NO_CREDENTIAL", 2)


def mask(secret):
    return (secret[:4] + "…" + secret[-4:]) if len(secret) > 12 else "****"


# ---------------------------------------------------------------- HTTP
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None  # never forward the Authorization header to another host


_OPENER = urllib.request.build_opener(_NoRedirect)


# MiniMax speech blocks (audio copyright / sensitive input) and similar provider wording.
# Checked after credits / rate-limit / auth so those stay stable.
_POLICY_MARKERS = (
    "copyright",
    "content policy",
    "content_policy",
    "content-policy",
    "safety",
    "unsafe",
    "usage policy",
    "policy violation",
    "violates our policy",
    "moderation",
    "new_sensitive",
    "sensitive content",
    "input sensitive",
    "audio policy",
    "版权",
    "内容政策",
    "内容安全",
    "安全策略",
    "违规",
)


def classify(code, body):
    text = json.dumps(body, ensure_ascii=False).lower() if body else ""
    if code == 402 or any(s in text for s in ("insufficient_user_quota", "insufficient", "quota",
                                                "余额不足", "credit")):
        return "INSUFFICIENT_CREDITS"
    if code == 429 or "rate limit" in text or "too many requests" in text:
        return "RATE_LIMIT"
    if code == 401 or "invalid token" in text or "token_invalid" in text or "expired" in text:
        return "AUTH"
    if any(marker in text for marker in _POLICY_MARKERS):
        return "CONTENT_POLICY"
    if code == 403:
        return "NOT_ALLOWED"
    if code and 400 <= code < 500:
        return "BAD_REQUEST"
    return "SERVER"


def error_message(body):
    """Best-effort provider message from a JSON error body."""
    if not isinstance(body, dict):
        return str(body)[:300]
    err = body.get("error")
    if isinstance(err, dict):
        msg = err.get("message") or err.get("msg")
        if msg:
            return str(msg)
    if isinstance(err, str) and err.strip():
        return err.strip()
    base = body.get("base_resp")
    if isinstance(base, dict) and base.get("status_msg"):
        return str(base["status_msg"])
    msg = body.get("message") or body.get("msg")
    if msg:
        return str(msg)
    return json.dumps(body, ensure_ascii=False)[:300]


def rejected_snippet_from_body(body):
    """Return blocked text when the provider echoes it; otherwise None."""
    if not isinstance(body, dict):
        return None
    for key in ("input", "text", "prompt", "content"):
        val = body.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:500]
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("input", "text", "prompt", "content"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()[:500]
    return None


def request(method, path_or_url, payload=None, cred=None, timeout=60, raw=False):
    """Returns (status, body_dict, headers). Raises PTError on network failure."""
    url = path_or_url if path_or_url.startswith("https://") else API_BASE + path_or_url
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if cred:
        headers["Authorization"] = "Bearer " + cred
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = _OPENER.open(req, timeout=timeout)
        code, hdrs, content = resp.status, dict(resp.headers), resp.read(4 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        code, hdrs, content = exc.code, dict(exc.headers or {}), exc.read(4 * 1024 * 1024)
    except (urllib.error.URLError, OSError) as exc:
        raise PTError("Network error talking to %s: %s" % (urllib.parse.urlsplit(url).netloc, exc),
                      "NETWORK")
    if raw:
        return code, content, hdrs
    try:
        body = json.loads(content.decode("utf-8")) if content else {}
    except ValueError:
        body = {"_raw": content[:500].decode("utf-8", "replace")}
    return code, body if isinstance(body, dict) else {"data": body}, hdrs


def raise_for(code, body, what, snippet=None):
    kind = classify(code, body if isinstance(body, dict) else {})
    msg = error_message(body)
    details = {}
    if kind == "CONTENT_POLICY":
        text = (snippet or rejected_snippet_from_body(body) or "").strip()
        if text:
            details["rejected_text"] = text[:500]
            msg = "%s | rejected_text: %s" % (msg, text[:180])
        details["recovery"] = (
            "This segment was blocked by the audio content policy. "
            "Rewrite it once (paraphrase; drop lyrics, celebrity names, trademark slogans, and long quotes; "
            "keep approved claim-sheet facts) and retry once. If it is still blocked, ask the user with the "
            "rejected line and rewrite options, and continue the other segments."
        )
    raise PTError("%s failed (HTTP %s): %s" % (what, code, msg), kind,
                  3 if kind in ("BAD_REQUEST", "CONTENT_POLICY") else 4, details)


_QUOTED = re.compile(
    r"[\"“”«»][^\"“”«»\n]{0,500}[\"“”«»]"
    r"|‘[^’\n]{8,500}’"
    r"|「[^」]{0,500}」"
    r"|『[^』]{0,500}』"
)
_TM = re.compile(r"[®™©]|\((?:r|tm|c)\)", re.I)
_ATTR = re.compile(
    r"(?i)\b(?:as|according to)\s+[A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){0,3}\s+says\b[:,]?\s*"
    r"|\b(?:endorsed by|featuring|starring)\s+[A-Z][\w.'’-]+(?:\s+[A-Z][\w.'’-]+){0,3}\b[:,]?\s*"
)
_DASH_ATTR = re.compile(r"\s*[—–-]\s*[A-Z][A-Za-z.'’-]+(?:\s+[A-Z][A-Za-z.'’-]+){0,3}\s*$")


def policy_rewrite(text):
    """One conservative rewrite for a CONTENT_POLICY retry.

    Strips quoted lyrics/slogans, trademark marks, and celebrity-style attributions.
    Keeps the unquoted remainder (numbers and product facts). Returns None when the
    text would be unchanged or too thin to speak — caller must not spend a retry.
    """
    original = " ".join((text or "").split())
    if not original:
        return None
    cleaned = _TM.sub("", original)
    cleaned = _QUOTED.sub(" ", cleaned)
    cleaned = _ATTR.sub(" ", cleaned)
    cleaned = _DASH_ATTR.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    candidate = _finish_rewrite(cleaned, original) if cleaned else None
    if candidate:
        return candidate
    return _finish_rewrite(_prefer_fact_sentences(original), original)


def _finish_rewrite(candidate, original):
    """Return a speakable rewrite, or None when it is the same line with tidy punctuation."""
    candidate = " ".join((candidate or "").split()).strip(" .,;:-")
    original_norm = " ".join((original or "").split()).strip(" .,;:-")
    if not candidate or len(candidate) < 8 or candidate == original_norm:
        return None
    if candidate[-1] not in ".!?":
        spoken = candidate + "."
    else:
        spoken = candidate
    if spoken.strip(" .,;:-") == original_norm:
        return None
    return spoken


def _prefer_fact_sentences(text):
    """Drop lyric-like or long unspecific sentences when a shorter fact remains."""
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    if len(parts) < 2:
        return " ".join((text or "").split()).strip(" .,;:-")
    kept = []
    for part in parts:
        words = part.split()
        has_digit = bool(re.search(r"\d", part))
        lyric_like = (len(words) >= 8 and part.count(",") >= 2 and not has_digit) or bool(_QUOTED.search(part))
        if lyric_like:
            continue
        if len(words) > 30 and not has_digit:
            continue
        if part.strip():
            kept.append(part.strip())
    if not kept:
        return ""
    return " ".join(kept).strip()


def download(url, out_path, cred=None):
    """Download a result file. Sends the credential only to the PowerTokens API host."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
    if cred and url.startswith(API_BASE + "/"):
        headers["Authorization"] = "Bearer " + cred
    req = urllib.request.Request(url, headers=headers)
    tmp = out.with_suffix(out.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as fh:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                fh.write(chunk)
    except (urllib.error.URLError, OSError) as exc:
        raise PTError("Download failed: %s" % exc, "DOWNLOAD")
    tmp.replace(out)
    return str(out.resolve())


# ---------------------------------------------------------------- misc
def to_media_ref(value):
    """http(s) URL passes through; a local file becomes a data: URL."""
    if value.startswith(("https://", "http://", "data:")):
        return value
    p = Path(value).expanduser()
    if not p.is_file():
        raise PTError("Image not found: %s" % value, "BAD_REQUEST", 3)
    if p.stat().st_size > 10 * 1024 * 1024:
        raise PTError("Image larger than 10 MB; resize it or pass a public URL.", "BAD_REQUEST", 3)
    raw = p.read_bytes()
    mime = sniff_image_mime(raw) or mimetypes.guess_type(p.name)[0] or "image/png"
    return "data:%s;base64,%s" % (mime.lower(), base64.b64encode(raw).decode("ascii"))


def sniff_image_mime(raw):
    """Trust the bytes, not the file name (Seedream URLs return JPEG even when saved as .png)."""
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def default_output(kind, ext, outdir="outputs"):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return str(Path(outdir) / ("%s-%s.%s" % (kind, stamp, ext)))


def speech_audio_url(code, content, headers):
    """PT /v1/audio/speech: docs say 302 + Location; live API (2026-10-20) returns 200 JSON
    {"data": {"audio": "<https url>", "status": 2}}. Accept both. Returns (url, parsed_json)."""
    loc = headers.get("Location") or headers.get("location")
    if code in (301, 302, 303, 307) and loc:
        return loc, {}
    try:
        parsed = json.loads(content.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None, {}
    if not isinstance(parsed, dict):
        return None, {}
    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
    url = data.get("audio") or parsed.get("audio") or parsed.get("url")
    if code == 200 and isinstance(url, str) and url.startswith("https://"):
        return url, parsed
    return None, parsed
