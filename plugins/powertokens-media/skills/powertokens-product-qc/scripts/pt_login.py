#!/usr/bin/env python3
"""One-time browser sign-in for PowerTokens (OAuth 2.0 Authorization Code + PKCE, loopback redirect).

    python3 pt_login.py login     # opens the browser, saves a token to ~/.config/powertokens/
    python3 pt_login.py status    # shows which credential the skills will use
    python3 pt_login.py logout    # deletes the saved token

STATUS: PowerTokens has not published the OAuth client registration yet. The endpoints and
client_id below are PLACEHOLDERS (None). Until they are filled in (here, or via the env vars /
~/.config/powertokens/oauth.json), `login` explains that and points to the API-key path.
Nothing here guesses or fakes an endpoint.
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pt_common as pt  # noqa: E402

# ----------------------------------------------------------------------------------------------
# PLACEHOLDERS — to be provided by PowerTokens engineering (see README "Browser sign-in status").
OAUTH_DEFAULTS = {
    "authorize_url": None,   # e.g. https://<pt-auth-host>/oauth/authorize   (NOT YET PUBLISHED)
    "token_url": None,       # e.g. https://<pt-auth-host>/oauth/token       (NOT YET PUBLISHED)
    "client_id": None,       # public client for media-skills                 (NOT YET REGISTERED)
    "scope": None,           # scope string that grants generation access     (NOT YET DEFINED)
    "userinfo_url": None,    # optional: account / credits endpoint           (NOT YET PUBLISHED)
}
# Redirect: http://127.0.0.1:<random port>/callback (RFC 8252 loopback). PT must allow any port.
# ----------------------------------------------------------------------------------------------


def oauth_config():
    cfg = dict(OAUTH_DEFAULTS)
    path = pt.CONFIG_DIR / "oauth.json"
    if path.is_file():
        try:
            cfg.update({k: v for k, v in json.loads(path.read_text("utf-8")).items() if v})
        except ValueError:
            pass
    for key in cfg:
        val = os.environ.get("POWERTOKENS_OAUTH_" + key.upper())
        if val:
            cfg[key] = val
    return cfg


def _pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def login(no_browser=False, timeout=300):
    cfg = oauth_config()
    missing = [k for k in ("authorize_url", "token_url", "client_id") if not cfg.get(k)]
    if missing:
        raise pt.PTError(
            "Browser sign-in is not enabled yet (PowerTokens OAuth client not published: missing %s). "
            "For now create an API key at %s and run: export POWERTOKENS_API_KEY=..."
            % (", ".join(missing), pt.KEYS_URL), "LOGIN_UNAVAILABLE", 2)
    for k in ("authorize_url", "token_url"):
        if not cfg[k].startswith("https://"):
            raise pt.PTError("%s must be https://" % k, "BAD_CONFIG", 3)

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(24)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != "/callback":
                self.send_response(404); self.end_headers(); return
            q = dict(urllib.parse.parse_qsl(parsed.query))
            result.update(q)
            ok = q.get("state") == state and "code" in q
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = ("Signed in to PowerTokens. You can close this tab and return to your agent."
                   if ok else "Sign-in failed. Return to your agent and try again.")
            self.wfile.write(("<html><body style='font-family:sans-serif'><h3>%s</h3></body></html>"
                              % msg).encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect_uri = "http://127.0.0.1:%d/callback" % server.server_port
    params = {"response_type": "code", "client_id": cfg["client_id"], "redirect_uri": redirect_uri,
              "state": state, "code_challenge": challenge, "code_challenge_method": "S256"}
    if cfg.get("scope"):
        params["scope"] = cfg["scope"]
    url = cfg["authorize_url"] + ("&" if "?" in cfg["authorize_url"] else "?") + urllib.parse.urlencode(params)

    print("Open this URL to sign in to PowerTokens (no account yet? you can sign up there):\n" + url,
          file=sys.stderr, flush=True)
    if not no_browser:
        webbrowser.open(url)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    deadline = time.time() + timeout
    while time.time() < deadline and not result:
        time.sleep(0.3)
    server.shutdown()
    if not result:
        raise pt.PTError("Timed out waiting for the browser sign-in.", "LOGIN_TIMEOUT")
    if result.get("state") != state:
        raise pt.PTError("State mismatch; sign-in aborted.", "LOGIN_FAILED")
    if "code" not in result:
        raise pt.PTError("Sign-in was not completed: %s" % result.get("error", "unknown"), "LOGIN_FAILED")

    form = urllib.parse.urlencode({"grant_type": "authorization_code", "code": result["code"],
                                   "redirect_uri": redirect_uri, "client_id": cfg["client_id"],
                                   "code_verifier": verifier}).encode()
    req = urllib.request.Request(cfg["token_url"], data=form, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
        "User-Agent": pt.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tok = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise pt.PTError("Token exchange failed (HTTP %s)." % exc.code, "LOGIN_FAILED")
    if not tok.get("access_token"):
        raise pt.PTError("Token endpoint returned no access_token.", "LOGIN_FAILED")
    saved = {"access_token": tok["access_token"], "token_type": tok.get("token_type", "Bearer"),
             "refresh_token": tok.get("refresh_token"), "scope": tok.get("scope"),
             "obtained_at": int(time.time()),
             "expires_at": int(time.time()) + int(tok["expires_in"]) if tok.get("expires_in") else None}
    pt.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(pt.CONFIG_DIR, 0o700)
    fd = os.open(str(pt.CREDENTIALS_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(saved, fh, indent=2)
    return {"ok": True, "saved_to": str(pt.CREDENTIALS_PATH), "expires_at": saved["expires_at"]}


def status():
    try:
        cred, source = pt.get_credential()
    except pt.PTError:
        return {"ok": False, "credential": None,
                "next_step": "Run `python3 pt_login.py login` or export POWERTOKENS_API_KEY. Sign up: "
                             + pt.SIGNUP_URL}
    return {"ok": True, "source": source, "credential": pt.mask(cred),
            "browser_login_enabled": all(oauth_config().get(k) for k in ("authorize_url", "token_url", "client_id"))}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["login", "status", "logout"])
    ap.add_argument("--no-browser", action="store_true", help="print the URL instead of opening a browser")
    args = ap.parse_args()
    if args.command == "login":
        pt.emit(login(args.no_browser))
    elif args.command == "status":
        out = status(); pt.emit(out); return 0 if out["ok"] else 2
    else:
        try:
            pt.CREDENTIALS_PATH.unlink()
            pt.emit({"ok": True, "removed": str(pt.CREDENTIALS_PATH)})
        except FileNotFoundError:
            pt.emit({"ok": True, "removed": None})


if __name__ == "__main__":
    pt.run(main)
