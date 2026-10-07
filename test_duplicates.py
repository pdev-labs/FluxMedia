"""Unit tests for duplicate detection. Run: python3 test_duplicates.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia.core import normalize_url, find_duplicate


class NormalizeTest(unittest.TestCase):
    def test_youtube_variants_collapse(self):
        base = "https://www.youtube.com/watch?v=eVvqFTG25GQ"
        for variant in [
            "https://youtu.be/eVvqFTG25GQ",
            "http://youtu.be/eVvqFTG25GQ?t=20s",
            "https://www.youtube.com/shorts/eVvqFTG25GQ",
            "https://www.youtube.com/embed/eVvqFTG25GQ",
            "https://www.youtube.com/live/eVvqFTG25GQ?feature=share",
            "https://m.youtube.com/watch?v=eVvqFTG25GQ",
            "https://www.youtube.com/watch?v=eVvqFTG25GQ&t=20s",
            "https://www.youtube.com/watch?feature=shared&v=eVvqFTG25GQ",
            "HTTPS://WWW.YOUTUBE.COM/watch?v=eVvqFTG25GQ",
            "www.youtube.com/watch?v=eVvqFTG25GQ",
            "https://www.youtube.com/watch?v=eVvqFTG25GQ#t=20",
        ]:
            self.assertEqual(normalize_url(variant), base, variant)

    def test_tracking_params_stripped(self):
        self.assertEqual(
            normalize_url("https://example.com/f.pdf?utm_source=x&fbclid=abc&id=5"),
            "https://example.com/f.pdf?id=5",
        )
        self.assertEqual(
            normalize_url("https://example.com/a?b=2&a=1"),
            "https://example.com/a?a=1&b=2",
        )

    def test_host_case_and_ports(self):
        self.assertEqual(normalize_url("HTTPS://EXAMPLE.COM:443/x/"), "https://example.com/x")
        self.assertEqual(normalize_url("http://example.com:80/x"), "http://example.com/x")
        self.assertEqual(normalize_url("http://example.com:8080/x"), "http://example.com:8080/x")

    def test_garbage(self):
        self.assertEqual(normalize_url(""), "")
        self.assertEqual(normalize_url("   "), "")
        self.assertEqual(normalize_url("not a url at all %%"), "https://not a url at all %%/")

    def test_different_videos_differ(self):
        self.assertNotEqual(normalize_url("https://youtu.be/AAA"),
                            normalize_url("https://youtu.be/BBB"))


class FindDuplicateTest(unittest.TestCase):
    def test_history_hit(self):
        hist = [{"url": "https://youtu.be/eVvqFTG25GQ", "title": "T",
                 "timestamp": "2026-01-01"}]
        hit = find_duplicate("https://www.youtube.com/watch?v=eVvqFTG25GQ&t=30",
                             history=hist, queue=[])
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit["where"], "history")

    def test_queue_hit(self):
        q = [{"url": "https://example.com/f.pdf?utm_source=x", "status": "Pending"}]
        hit = find_duplicate("https://example.com/f.pdf", history=[], queue=q)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit["where"], "queue")

    def test_no_hit_and_non_pending_ignored(self):
        hist = [{"url": "https://example.com/other"}]
        q = [{"url": "https://example.com/f.pdf", "status": "Completed"}]
        self.assertIsNone(find_duplicate("https://example.com/f.pdf", history=hist, queue=q))
        self.assertIsNone(find_duplicate("", history=hist, queue=q))


class ApiDuplicateTest(unittest.TestCase):
    def test_duplicate_response_without_job(self):
        import fluxmedia.api as A
        req = A.DownloadRequest(url="https://youtu.be/eVvqFTG25GQ", type="video")
        # stub history lookup: patch find_duplicate via module attr
        import fluxmedia.core as C
        real_load = C.load_history
        C.load_history = lambda: [{"url": "https://www.youtube.com/watch?v=eVvqFTG25GQ",
                                   "title": "T", "timestamp": "t"}]
        real_queue = C.load_queue
        C.load_queue = lambda: []
        try:
            resp = A.download_media(req, background_tasks=None)  # type: ignore
        finally:
            C.load_history = real_load
            C.load_queue = real_queue
        self.assertEqual(resp["status"], "duplicate")
        self.assertIsNone(resp["job_id"])
        self.assertEqual(resp["duplicate"]["where"], "history")



class SubtitleLangsTest(unittest.TestCase):
    def test_parser(self):
        from fluxmedia.core import parse_subtitle_langs as p
        self.assertEqual(p("en"), ["en"])
        self.assertEqual(p("en,es,pt-BR"), ["en", "es", "pt-BR"])
        self.assertEqual(p("en; es ;en"), ["en", "es"])
        self.assertEqual(p("EN"), ["en"] if "EN" == "en" else ["en"])
        self.assertEqual(p(""), ["en"])
        self.assertEqual(p(None), ["en"])
        self.assertEqual(p("eñ,toolongcode,fr"), ["fr"])
        self.assertEqual(p("123"), ["en"])

    def test_api_field_and_opts(self):
        import fluxmedia.api as A
        req = A.DownloadRequest(url="https://example.com/v", type="video", subtitle_langs="es,en")
        self.assertEqual(req.subtitle_langs, "es,en")
        captured = {}

        class FakeYDL:
            def __init__(self, opts):
                captured.update(opts)
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def download(self, urls):
                return None

        orig_ydl, orig_cfg = A.yt_dlp.YoutubeDL, A.load_config
        A.yt_dlp.YoutubeDL = FakeYDL
        A.load_config = lambda: {"download_dir": "/tmp", "filename_format": "%(t)s.%(e)s",
                                 "embed_subtitles": True, "subtitle_langs": "fr"}
        A.DOWNLOAD_JOBS["testjob123"] = {"status": "starting", "progress": 0,
                                         "speed": 0, "eta": 0, "logs": []}
        from fluxmedia import plugins as _P
        orig_mgr = _P.get_manager
        _P.get_manager = lambda *a, **k: type("M", (), {"emit": lambda self, *a, **k: None})()
        try:
            A.run_download_job("testjob123", req)
        finally:
            A.yt_dlp.YoutubeDL = orig_ydl
            A.load_config = orig_cfg
            _P.get_manager = orig_mgr
            A.DOWNLOAD_JOBS.pop("testjob123", None)
        self.assertEqual(captured.get("subtitleslangs"), ["es", "en"])
        self.assertTrue(captured.get("writesubtitles"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
