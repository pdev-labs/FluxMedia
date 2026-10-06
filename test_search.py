"""Unit tests for entry search (?q=). Run: python3 test_search.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia.core import search_entries


class SearchEntriesTest(unittest.TestCase):
    ENTRIES = [
        {"title": "Best Macbook Deals", "url": "https://youtu.be/AAA", "type": "video", "status": "Success"},
        {"title": "LoFi Mix", "url": "https://youtu.be/BBB", "type": "audio", "status": "Failed"},
        {"name": "x36xhzz.mp4", "type": "videos", "ext": ".mp4"},
    ]

    def test_empty_query_returns_all(self):
        self.assertEqual(len(search_entries(self.ENTRIES, "", ("title",))), 3)
        self.assertEqual(len(search_entries(self.ENTRIES, "   ", ("title",))), 3)
        self.assertEqual(search_entries(None, "x", ("title",)), [])

    def test_case_insensitive_substring(self):
        hit = search_entries(self.ENTRIES, "macbook", ("title", "url"))
        self.assertEqual(len(hit), 1)
        hit = search_entries(self.ENTRIES, "YOUTU.BE/BBB", ("title", "url"))
        self.assertEqual(len(hit), 1)

    def test_multi_field(self):
        self.assertEqual(len(search_entries(self.ENTRIES, "audio", ("title", "type"))), 1)
        self.assertEqual(len(search_entries(self.ENTRIES, "mp4", ("name", "ext"))), 1)
        self.assertEqual(len(search_entries(self.ENTRIES, "zzz", ("title", "url", "type"))), 0)

    def test_tolerates_bad_rows(self):
        rows = ["not-a-dict", None, {"title": None}]
        self.assertEqual(search_entries(rows, "x", ("title",)), [])


class ApiQueryParamsTest(unittest.TestCase):
    def test_history_q_filters(self):
        import fluxmedia.api as A
        real_load = A.load_history
        A.load_history = lambda: [
            {"title": "Cats", "url": "u1", "type": "video", "status": "Success"},
            {"title": "Dogs", "url": "u2", "type": "video", "status": "Success"},
        ]
        try:
            all_r = A.get_history(limit=100, q="")
            self.assertEqual(all_r["total"], 2)
            cats = A.get_history(limit=100, q="cats")
            self.assertEqual(cats["total"], 1)
            self.assertEqual(cats["history"][0]["title"], "Cats")
        finally:
            A.load_history = real_load

    def test_files_q_filters(self):
        import fluxmedia.api as A
        import fluxmedia.core as C
        import tempfile
        d = tempfile.mkdtemp()
        open(os.path.join(d, "alpha_video.mp4"), "w").write("x")
        open(os.path.join(d, "beta_audio.mp3"), "w").write("x")
        real_load = A.load_config
        A.load_config = lambda: {"download_dir": d}
        try:
            all_r = A.list_files(category="all", q="")
            self.assertEqual(len(all_r["files"]), 2)
            one = A.list_files(category="all", q="ALPHA")
            self.assertEqual(len(one["files"]), 1)
            self.assertIn("alpha", one["files"][0]["name"])
        finally:
            A.load_config = real_load


if __name__ == "__main__":
    unittest.main(verbosity=2)
