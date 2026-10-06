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


class ConfigPermsTest(unittest.TestCase):
    def test_config_writes_are_owner_only(self):
        import stat as _stat
        import fluxmedia.core as C
        orig = C.CONFIG_FILE
        tmp = os.path.join(tempfile.mkdtemp(), "config.json")
        C.CONFIG_FILE = tmp
        try:
            self.assertTrue(C.save_config({"a": 1}))
            mode = _stat.S_IMODE(os.stat(tmp).st_mode)
            self.assertEqual(mode, 0o600, oct(mode))
        finally:
            C.CONFIG_FILE = orig

    def test_lan_warning(self):
        import inspect
        import fluxmedia.api as A
        self.assertFalse(A._lan_warning("127.0.0.1"))
        self.assertFalse(A._lan_warning("localhost"))
        self.assertFalse(A._lan_warning("::1"))
        self.assertTrue(A._lan_warning("0.0.0.0"))
        self.assertTrue(A._lan_warning("192.168.1.5"))
        sig = inspect.signature(A.run_server)
        self.assertEqual(sig.parameters["host"].default, "127.0.0.1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
