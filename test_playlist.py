"""Unit tests for playlist flat-extract. Run: python3 test_playlist.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import fluxmedia.api as A
from fluxmedia.api import _entry_play_url


class PlayUrlTest(unittest.TestCase):
    def test_youtube_flat_entry(self):
        e = {"id": "ABC123", "ie_key": "Youtube", "title": "T"}
        self.assertEqual(_entry_play_url(e), "https://www.youtube.com/watch?v=ABC123")

    def test_direct_url_wins(self):
        e = {"id": "x", "webpage_url": "https://example.com/v/x", "url": "x"}
        self.assertEqual(_entry_play_url(e), "https://example.com/v/x")

    def test_unresolvable(self):
        self.assertEqual(_entry_play_url({"id": "", "title": "t"}), "")
        self.assertEqual(_entry_play_url({}), "")


class PlaylistEndpointTest(unittest.TestCase):
    def _run(self, info, limit=50):
        class FakeYDL:
            def __init__(self, opts):
                self.opts = opts
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def extract_info(self, url, download=False):
                assert download is False
                return info

        orig = A.yt_dlp.YoutubeDL
        A.yt_dlp.YoutubeDL = FakeYDL
        try:
            return A.list_playlist(A.PlaylistRequest(url="https://example.com/list", limit=limit))
        finally:
            A.yt_dlp.YoutubeDL = orig

    def test_playlist_entries(self):
        info = {"_type": "playlist", "title": "Mix",
                "entries": [
                    {"id": "A1", "title": "One", "ie_key": "Youtube"},
                    {"id": "B2", "title": "Two", "ie_key": "Youtube"},
                    None,
                    {"title": "No URL anywhere"},
                ]}
        res = self._run(info)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Mix")
        self.assertEqual(res["count"], 2)
        self.assertEqual(res["entries"][0]["url"], "https://www.youtube.com/watch?v=A1")

    def test_single_video(self):
        info = {"id": "Z9", "title": "Solo",
                "webpage_url": "https://example.com/v/Z9", "extractor_key": "generic"}
        res = self._run(info)
        self.assertEqual(res["count"], 1)

    def test_empty_and_limit_clamp(self):
        res = self._run({"title": "Empty", "entries": []})
        self.assertEqual(res["count"], 0)
        big = {"title": "Big",
               "entries": [{"id": f"v{i}", "title": f"T{i}", "ie_key": "Youtube"} for i in range(300)]}
        res = self._run(big, limit=9999)
        self.assertLessEqual(res["count"], 200)
        self.assertTrue(res["truncated"])

    def test_backend_error_is_400(self):
        class Boom:
            def __init__(self, opts):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def extract_info(self, url, download=False):
                raise RuntimeError("nope")

        orig = A.yt_dlp.YoutubeDL
        A.yt_dlp.YoutubeDL = Boom
        try:
            with self.assertRaises(Exception) as ctx:
                A.list_playlist(A.PlaylistRequest(url="https://example.com/x"))
            self.assertIn("nope", str(ctx.exception))
        finally:
            A.yt_dlp.YoutubeDL = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)
