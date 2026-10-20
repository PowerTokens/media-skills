"""Offline tests: no network, no credits. Run: python3 -m unittest discover tests"""
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.environ["POWERTOKENS_CONFIG_DIR"] = tempfile.mkdtemp()
os.environ.pop("POWERTOKENS_API_KEY", None)
sys.path.insert(0, str(ROOT / "tools" / "shared"))
import pt_common as pt  # noqa: E402
import pt_login  # noqa: E402
import video  # noqa: E402


class VideoTests(unittest.TestCase):
    def test_wan_request_shape(self):
        ep, body = video.build("wan3.0-video", "fox", 5, "720p", "9:16")
        self.assertEqual(ep, "/v1/videos")
        self.assertEqual(body["size"], "720P")
        self.assertEqual(body["seconds"], "5")

    def test_seedance_media_items(self):
        ep, body = video.build("dreamina-seedance-2-0-fast-260128", "fox", 5, "720p", "16:9",
                               image="https://example.com/a.png")
        self.assertEqual(body["media"][0], {"type": "text", "text": "fox"})
        self.assertEqual(body["media"][1]["type"], "first_frame")

    def test_kling_i2v_route(self):
        ep, body = video.build("kling-v3", "spin", 5, "1080p", "16:9", image="https://example.com/a.png")
        self.assertEqual(ep, "/kling/v1/videos/image2video")
        self.assertEqual(body["mode"], "pro")

    def test_poll_then_download(self):
        replies = iter([(200, {"status": "in_progress", "progress": 40}, {}),
                        (200, {"status": "succeeded", "metadata": {"url": "https://cdn.example.com/v.mp4"}}, {})])
        with mock.patch.object(pt, "request", side_effect=lambda *a, **k: next(replies)), \
             mock.patch.object(pt, "download", return_value="/tmp/v.mp4") as dl, \
             mock.patch.object(video.time, "sleep"):
            out = video.wait_and_download("k", "wan3.0-video", "task_1", "/tmp/v.mp4")
        self.assertEqual(out, "/tmp/v.mp4")
        dl.assert_called_once_with("https://cdn.example.com/v.mp4", "/tmp/v.mp4", "k")

    def test_credit_error_classified(self):
        body = {"error": {"code": "insufficient_user_quota", "message": "Insufficient account quota"}}
        self.assertEqual(pt.classify(429, body), "INSUFFICIENT_CREDITS")


class LiveShapeTests(unittest.TestCase):
    """Response shapes seen on the live API (2026-10-20)."""
    def test_speech_200_json_audio_url(self):
        body = json.dumps({"data": {"audio": "https://cdn.example.com/a.mp3", "status": 2}}).encode()
        self.assertEqual(pt.speech_audio_url(200, body, {})[0], "https://cdn.example.com/a.mp3")

    def test_speech_302_location(self):
        self.assertEqual(pt.speech_audio_url(302, b"", {"Location": "https://x/a.mp3"})[0], "https://x/a.mp3")

    def test_speech_error_json(self):
        url, parsed = pt.speech_audio_url(400, b'{"error": {"message": "bad voice"}}', {})
        self.assertIsNone(url)
        self.assertIn("error", parsed)

    def test_sniff_jpeg_named_png(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
            fh.write(b"\xff\xd8\xff\xe0fakejpeg")
        self.assertTrue(pt.to_media_ref(fh.name).startswith("data:image/jpeg;base64,"))
        os.unlink(fh.name)


class LoginTests(unittest.TestCase):
    def test_placeholders_block_login(self):
        with self.assertRaises(pt.PTError) as ctx:
            pt_login.login(no_browser=True)
        self.assertEqual(ctx.exception.kind, "LOGIN_UNAVAILABLE")

    def test_pkce_loopback_flow_and_token_used(self):
        cfg = {"authorize_url": "https://auth.example.test/oauth/authorize",
               "token_url": "https://auth.example.test/oauth/token", "client_id": "test-client"}
        printed = io.StringIO()

        def fake_browser():  # play the browser: read printed URL, hit the loopback callback
            import time
            for _ in range(50):
                if "redirect_uri" in printed.getvalue():
                    break
                time.sleep(0.05)
            url = printed.getvalue().strip().splitlines()[-1]
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
            assert q["code_challenge_method"] == "S256"
            urllib.request.urlopen(q["redirect_uri"] + "?code=abc&state=" + q["state"]).read()

        real_urlopen = urllib.request.urlopen

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, *a, **k):
            if isinstance(req, urllib.request.Request) and req.full_url == cfg["token_url"]:
                form = dict(urllib.parse.parse_qsl(req.data.decode()))
                assert form["code"] == "abc" and form["code_verifier"]
                return Resp(json.dumps({"access_token": "tok_123", "expires_in": 3600}).encode())
            return real_urlopen(req, *a, **k)

        with mock.patch.object(pt_login, "oauth_config", return_value=cfg), \
             mock.patch.object(pt_login.urllib.request, "urlopen", side_effect=fake_urlopen), \
             mock.patch("sys.stderr", printed):
            t = threading.Thread(target=fake_browser); t.start()
            result = pt_login.login(no_browser=True, timeout=10)
            t.join()
        self.assertTrue(result["ok"])
        self.assertEqual(oct(pt.CREDENTIALS_PATH.stat().st_mode & 0o777), "0o600")
        cred, source = pt.get_credential()
        self.assertEqual(cred, "tok_123")
        self.assertTrue(source.startswith("login:"))
        with mock.patch.dict(os.environ, {"POWERTOKENS_API_KEY": "sk-env"}):
            self.assertEqual(pt.get_credential()[0], "sk-env")  # env key wins


if __name__ == "__main__":
    unittest.main()
