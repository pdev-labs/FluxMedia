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


if __name__ == "__main__":
    unittest.main(verbosity=2)
