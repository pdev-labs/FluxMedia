"""Unit tests for session log files. Run: python3 test_logging.py"""
import logging
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import fluxmedia.core as C


class LoggingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig = (C.DATA_DIR, C.LOG_DIR, C.LOG_FILE)
        C.DATA_DIR = self.tmp
        C.LOG_DIR = os.path.join(self.tmp, "logs")
        C.LOG_FILE = os.path.join(self.tmp, "fluxmedia.log")
        self.root_handlers = list(logging.getLogger().handlers)

    def tearDown(self):
        for h in list(logging.getLogger().handlers):
            if h not in self.root_handlers:
                try:
                    logging.getLogger().removeHandler(h)
                    h.close()
                except Exception:
                    pass
        C.DATA_DIR, C.LOG_DIR, C.LOG_FILE = self.orig

    def test_setup_creates_session_file(self):
        path = C.setup_file_logging()
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(os.path.basename(path).startswith("fluxmedia-"))
        self.assertEqual(C.LOG_FILE, path)

    def test_log_line_format_parseable(self):
        path = C.setup_file_logging()
        logging.getLogger("fluxmedia.test").warning("hello %s", "world")
        for h in logging.getLogger().handlers:
            try:
                h.flush()
            except Exception:
                pass
        with open(path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertTrue(lines)
        parts = lines[-1].split(" - ", 3)
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[1], "WARNING")

    def test_prune_keeps_retention(self):
        os.makedirs(C.LOG_DIR, exist_ok=True)
        for i in range(16):
            p = os.path.join(C.LOG_DIR, f"fluxmedia-20200101-0000{i:02d}.log")
            with open(p, "w", encoding="utf-8") as f:
                f.write("x")
            old = time.time() - (100 - i)
            os.utime(p, (old, old))
        C.setup_file_logging()
        files = C.get_log_files()
        self.assertLessEqual(len(files), C.KEEP_SESSION_LOGS + 1)
        self.assertEqual(files, sorted(files, key=lambda x: x["mtime"], reverse=True))

    def test_current_log_file(self):
        self.assertEqual(C.current_log_file(), "")
        path = C.setup_file_logging()
        self.assertEqual(C.current_log_file(), path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
