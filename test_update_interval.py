"""Unit tests for the update-check interval. Run: python3 test_update_interval.py"""
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import core without triggering heavy deps: core imports yt_dlp at top,
# which the test env provides (same env that runs test_plugins.py).
from fluxmedia.core import should_check_for_updates, UPDATE_INTERVALS


class UpdateIntervalTest(unittest.TestCase):
    def base(self, **over):
        cfg = {"auto_update": True, "update_interval": "weekly",
               "last_update_check": 0.0}
        cfg.update(over)
        return cfg

    def test_never_checked_means_due(self):
        self.assertTrue(should_check_for_updates(self.base()))

    def test_weekly_blocks_after_fresh_check(self):
        self.assertFalse(should_check_for_updates(
            self.base(last_update_check=time.time())))

    def test_daily(self):
        self.assertFalse(should_check_for_updates(
            self.base(update_interval="daily",
                      last_update_check=time.time() - 3600)))
        self.assertTrue(should_check_for_updates(
            self.base(update_interval="daily",
                      last_update_check=time.time() - 90000)))

    def test_monthly(self):
        self.assertFalse(should_check_for_updates(
            self.base(update_interval="monthly",
                      last_update_check=time.time() - 86400)))
        self.assertTrue(should_check_for_updates(
            self.base(update_interval="monthly",
                      last_update_check=time.time() - 31 * 86400)))

    def test_never_interval(self):
        self.assertFalse(should_check_for_updates(
            self.base(update_interval="never")))

    def test_auto_update_false_is_master_switch(self):
        self.assertFalse(should_check_for_updates(
            self.base(auto_update=False, update_interval="daily",
                      last_update_check=0.0)))

    def test_unknown_interval_falls_back_to_weekly(self):
        self.assertFalse(should_check_for_updates(
            self.base(update_interval="fortnightly",
                      last_update_check=time.time())))
        self.assertTrue(should_check_for_updates(
            self.base(update_interval="fortnightly",
                      last_update_check=0.0)))

    def test_bad_timestamp_treated_as_never_checked(self):
        self.assertTrue(should_check_for_updates(
            self.base(last_update_check="garbage")))
        self.assertTrue(should_check_for_updates(
            self.base(last_update_check=None)))

    def test_interval_table_sane(self):
        self.assertEqual(UPDATE_INTERVALS["daily"], 86400)
        self.assertEqual(UPDATE_INTERVALS["weekly"], 7 * 86400)
        self.assertEqual(UPDATE_INTERVALS["monthly"], 30 * 86400)
        self.assertIsNone(UPDATE_INTERVALS["never"])


class IgnoreVersionTest(unittest.TestCase):
    def base(self, **over):
        cfg = {"auto_update": True, "update_interval": "daily",
               "last_update_check": 0.0, "ignored_versions": []}
        cfg.update(over)
        return cfg

    def test_is_version_ignored(self):
        from fluxmedia.core import is_version_ignored
        self.assertTrue(is_version_ignored("1.2.3", self.base(ignored_versions=["1.2.3"])))
        self.assertFalse(is_version_ignored("1.2.4", self.base(ignored_versions=["1.2.3"])))
        self.assertFalse(is_version_ignored("1.2.3", self.base()))
        self.assertFalse(is_version_ignored(None, self.base(ignored_versions=["1.2.3"])))
        self.assertFalse(is_version_ignored("1.2.3", {"ignored_versions": "nope"}))
        self.assertFalse(is_version_ignored("1.2.3", {}))

    def _run_check(self, cfg, fake_version):
        import fluxmedia.core as core

        class Resp:
            status_code = 200

            def json(self):
                return {"info": {"version": fake_version}}

        calls = {"net": 0, "saved": 0, "prompt": 0}
        orig_get, orig_save, orig_prompt = core.requests.get, core.save_config, core.Prompt

        def fake_get(*a, **k):
            calls["net"] += 1
            return Resp()

        def fake_save(c):
            calls["saved"] += 1
            return True

        class FakePrompt:
            @staticmethod
            def ask(*a, **k):
                calls["prompt"] += 1
                return "2"

        core.requests.get, core.save_config, core.Prompt = fake_get, fake_save, FakePrompt
        try:
            core.check_fluxmedia_update_sync(cfg)
        finally:
            core.requests.get, core.save_config, core.Prompt = orig_get, orig_save, orig_prompt
        return calls

    def test_ignored_version_skips_prompt_but_stamps(self):
        calls = self._run_check(self.base(ignored_versions=["9.9.9"]), "9.9.9")
        self.assertEqual(calls["net"], 1)     # one cheap version fetch to learn the version
        self.assertEqual(calls["prompt"], 0)  # ...but never shown to the user
        self.assertEqual(calls["saved"], 1)   # interval timer still stamped

    def test_non_ignored_version_prompts(self):
        calls = self._run_check(self.base(), "9.9.9")
        self.assertEqual(calls["prompt"], 1)


class QueueRecoveryTest(unittest.TestCase):
    def setUp(self):
        import fluxmedia.core as C
        self.C = C
        self.tmp = tempfile.mkdtemp()
        self.orig = C.QUEUE_FILE
        C.QUEUE_FILE = os.path.join(self.tmp, "queue.json")

    def tearDown(self):
        self.C.QUEUE_FILE = self.orig

    def test_crash_recovery_requeues_downloading(self):
        import json as _json
        queue = [
            {"id": 1, "url": "u1", "status": "Downloading"},
            {"id": 2, "url": "u2", "status": "Pending"},
            {"id": 3, "url": "u3", "status": "Completed"},
            {"id": 4, "url": "u4", "status": "Failed"},
        ]
        with open(self.C.QUEUE_FILE, "w", encoding="utf-8") as f:
            _json.dump(queue, f)
        self.assertEqual(self.C.recover_interrupted_queue(), 1)
        reloaded = self.C.load_queue()
        by_id = {i["id"]: i["status"] for i in reloaded}
        self.assertEqual(by_id, {1: "Pending", 2: "Pending", 3: "Completed", 4: "Failed"})

    def test_recovery_is_idempotent_and_empty_safe(self):
        self.assertEqual(self.C.recover_interrupted_queue(), 0)
        with open(self.C.QUEUE_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        self.assertEqual(self.C.recover_interrupted_queue(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
