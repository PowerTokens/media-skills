"""Shared helpers for PowerTokens media skills (Python 3.8+ stdlib only).

Auth order: POWERTOKENS_API_KEY env var  >  token saved by `pt_login.py login`.
"""
import base64
import json
import mimetypes
import os
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
    def __init__(self, message, kind="UNKNOWN", exit_code=4):
        super().__init__(message)
        self.kind, self.exit_code = kind, exit_code


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def run(main):
    """Run a CLI main(); print errors as JSON with stable error_type and exit codes."""
    try:
        sys.exit(main() or 0)
    except PTError as exc:
        out = {"ok": False, "error_type": exc.kind, "error": str(exc)}
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


def classify(code, body):
    text = json.dumps(body, ensure_ascii=False).lower() if body else ""
    if code == 402 or any(s in text for s in ("insufficient_user_quota", "insufficient", "quota",
                                                "余额不足", "credit")):
        return "INSUFFICIENT_CREDITS"
    if code == 429 or "rate limit" in text or "too many requests" in text:
        return "RATE_LIMIT"
    if code == 401 or "invalid token" in text or "token_invalid" in text or "expired" in text:
        return "AUTH"
    if code == 403:
        return "NOT_ALLOWED"
    if code and 400 <= code < 500:
        return "BAD_REQUEST"
    return "SERVER"


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


def raise_for(code, body, what):
    kind = classify(code, body)
    msg = body.get("error", {}).get("message") if isinstance(body.get("error"), dict) else None
    msg = msg or body.get("message") or body.get("msg") or json.dumps(body)[:300]
    raise PTError("%s failed (HTTP %s): %s" % (what, code, msg), kind,
                  3 if kind == "BAD_REQUEST" else 4)


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
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return "data:%s;base64,%s" % (mime.lower(), base64.b64encode(p.read_bytes()).decode("ascii"))


def default_output(kind, ext, outdir="outputs"):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return str(Path(outdir) / ("%s-%s.%s" % (kind, stamp, ext)))
