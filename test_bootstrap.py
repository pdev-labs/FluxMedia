"""Unit tests for web-dependency self-healing. Run: python3 test_bootstrap.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia import utils as U


class BootstrapTest(unittest.TestCase):
    def test_termux_pin_map(self):
        self.assertEqual(U.termux_pydantic_pin(3, 11), "pydantic==2.11.7")
        self.assertEqual(U.termux_pydantic_pin(3, 12), "pydantic==2.11.7")
        self.assertEqual(U.termux_pydantic_pin(3, 13), "pydantic==2.12.4")
        self.assertEqual(U.termux_pydantic_pin(3, 14), "pydantic==2.12.4")
        self.assertIsNone(U.termux_pydantic_pin(3, 9))
        self.assertIsNone(U.termux_pydantic_pin(3, 15))
        self.assertIsNone(U.termux_pydantic_pin(2, 7))

    def test_happy_path_no_pip(self):
        calls = []
        orig = U._pip_install_quiet
        U._pip_install_quiet = lambda *a, **k: calls.append((a, k)) or True
        try:
            self.assertTrue(U.ensure_web_deps())
        finally:
            U._pip_install_quiet = orig
        self.assertEqual(calls, [])  # everything importable -> pip never runs

    def _block(self, *names):
        import importlib.abc

        class Blocker(importlib.abc.MetaPathFinder):
            def find_spec(self, name, path, target=None):
                if name in names or name.split(".")[0] in names:
                    raise ImportError(f"blocked {name}")
                return None

        blocker = Blocker()
        sys.meta_path.insert(0, blocker)
        for n in list(sys.modules):
            if n in names or n.split(".")[0] in names:
                del sys.modules[n]
        return blocker

    def test_termux_plan_uses_pin_and_index(self):
        blocker = self._block("pydantic_core", "pydantic", "fastapi", "uvicorn")
        captured = {}
        orig_pip = U._pip_install_quiet
        orig_termux = U.is_termux
        orig_pin = U.termux_pydantic_pin
        U._pip_install_quiet = lambda pkgs, extra_indexes=None: captured.setdefault("calls", []).append((pkgs, extra_indexes)) or True
        U.is_termux = lambda: True
        U.termux_pydantic_pin = lambda major=3, minor=12: "pydantic==2.11.7"
        try:
            self.assertFalse(U.ensure_web_deps())  # re-import still blocked
        finally:
            sys.meta_path.remove(blocker)
            U._pip_install_quiet = orig_pip
            U.is_termux = orig_termux
            U.termux_pydantic_pin = orig_pin
        flat = [p for pkgs, _ in captured["calls"] for p in pkgs]
        self.assertIn("pydantic==2.11.7", flat)
        self.assertIn("fastapi", flat)
        idx = captured["calls"][0][1]
        self.assertTrue(any("termux-user-repository" in u for u in idx))

    def test_desktop_plan_is_plain(self):
        blocker = self._block("pydantic_core", "pydantic", "fastapi", "uvicorn")
        captured = {}
        orig_pip = U._pip_install_quiet
        orig_termux = U.is_termux
        U._pip_install_quiet = lambda pkgs, extra_indexes=None: captured.setdefault("calls", []).append((pkgs, extra_indexes)) or True
        U.is_termux = lambda: False
        try:
            self.assertFalse(U.ensure_web_deps())
        finally:
            sys.meta_path.remove(blocker)
            U._pip_install_quiet = orig_pip
            U.is_termux = orig_termux
        flat = [p for pkgs, _ in captured["calls"] for p in pkgs]
        self.assertIn("fastapi", flat)
        self.assertNotIn("pydantic==2.11.7", flat)


if __name__ == "__main__":
    unittest.main(verbosity=2)
