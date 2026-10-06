"""Unit tests for notify_event gating. Run: python3 test_notify.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia.core import notify_event


class NotifyTest(unittest.TestCase):
    def setUp(self):
        import fluxmedia.utils as U
        self.U = U
        self.calls = []
        self._orig_desktop = U.send_desktop_notification
        calls = self.calls

        def fake_desktop(title, message):
            calls.append(("desktop", title, message))

        U.send_desktop_notification = fake_desktop
        import urllib.request as R
        self._orig_urlopen = R.urlopen

        def fake_urlopen(req, timeout=None):
            calls.append(("webhook", req.full_url, req.data))
            class Ctx:
                def __enter__(self):
                    return self
                def __exit__(self, *a):
                    return False
            return Ctx()

        R.urlopen = fake_urlopen

    def tearDown(self):
        self.U.send_desktop_notification = self._orig_desktop
        import urllib.request as R
        R.urlopen = self._orig_urlopen

    def base(self, **over):
        cfg = {"notify_on": "both", "ntfy_url": ""}
        cfg.update(over)
        return cfg

    def test_both_by_default(self):
        self.assertTrue(notify_event("complete", "T", "m", self.base()))
        self.assertTrue(notify_event("failed", "T", "m", self.base()))
        self.assertEqual(len(self.calls), 2)

    def test_modes(self):
        self.assertTrue(notify_event("complete", "T", "m", self.base(notify_on="complete")))
        self.assertFalse(notify_event("failed", "T", "m", self.base(notify_on="complete")))
        self.assertFalse(notify_event("complete", "T", "m", self.base(notify_on="failed")))
        self.assertTrue(notify_event("failed", "T", "m", self.base(notify_on="failed")))
        self.assertFalse(notify_event("complete", "T", "m", self.base(notify_on="never")))
        # unknown modes fail open (behave as "both"), documented in code
        self.assertTrue(notify_event("complete", "T", "m", self.base(notify_on="bogus")))

    def test_webhook(self):
        self.assertTrue(notify_event("complete", "Done!", "file.mp4",
                                     self.base(ntfy_url="https://ntfy.sh/mytopic")))
        kinds = [c[0] for c in self.calls]
        self.assertIn("desktop", kinds)
        self.assertIn("webhook", kinds)
        hook = [c for c in self.calls if c[0] == "webhook"][0]
        self.assertEqual(hook[1], "https://ntfy.sh/mytopic")
        self.assertIn(b"file.mp4", hook[2])

    def test_never_touches_network(self):
        self.assertFalse(notify_event("complete", "T", "m", self.base(notify_on="never")))
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
