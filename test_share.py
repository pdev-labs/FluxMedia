"""Unit tests for share-link limits. Run: python3 test_share.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia.server.classic_portal import link_limits_reached


class ShareLimitsTest(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertEqual(link_limits_reached(0, 0, 0, 0, now=1000), "")
        self.assertEqual(link_limits_reached(0, None, 5, None, now=1000), "")

    def test_ttl_expiry(self):
        self.assertEqual(link_limits_reached(0, 10, 0, 0, now=599), "")
        self.assertEqual(link_limits_reached(0, 10, 0, 0, now=601), "expired")
        self.assertEqual(link_limits_reached(100, 0.05, 0, 0, now=104), "expired")

    def test_download_cap(self):
        self.assertEqual(link_limits_reached(0, 0, 1, 2, now=10), "")
        self.assertEqual(link_limits_reached(0, 0, 2, 2, now=10), "limit")
        self.assertEqual(link_limits_reached(0, 0, 9, 2, now=10), "limit")

    def test_expiry_wins_over_limit(self):
        self.assertEqual(link_limits_reached(0, 1, 99, 2, now=61), "expired")

    def test_bad_config_values_are_safe(self):
        self.assertEqual(link_limits_reached(0, "soon", 0, "many", now=10**9), "")
        self.assertEqual(link_limits_reached(0, -5, 0, -1, now=10**9), "")

    def test_new_config_defaults_exist(self):
        from fluxmedia.core import DEFAULT_CONFIG
        self.assertEqual(DEFAULT_CONFIG["share_link_ttl_minutes"], 0)
        self.assertEqual(DEFAULT_CONFIG["share_max_downloads"], 0)
        self.assertEqual(DEFAULT_CONFIG["share_pairing_confirm"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
