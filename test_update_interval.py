"""Unit tests for the update-check interval. Run: python3 test_update_interval.py"""
import os
import sys
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
