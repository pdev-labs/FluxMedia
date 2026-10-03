"""Unit tests for the plugin system. Run: python3 test_plugins.py"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia import plugins as P


class PluginTest(unittest.TestCase):
    def setUp(self):
        P.reset_manager()
        self.tmp = tempfile.mkdtemp()
        # Isolate the plugins dir + config per test.
        P.get_plugins_dir = lambda: self.tmp
        self.config: dict = {}

    def tearDown(self):
        P.reset_manager()

    def _write(self, name, body):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def test_full_plugin_lifecycle(self):
        self._write("demo.py", '''
PLUGIN = {"name": "demo", "version": "2.0", "description": "d", "author": "t"}
seen = []
def register(hooks):
    hooks.on("startup", lambda config=None: seen.append(("startup", config)))
    hooks.on("download_complete", lambda url=None, filepath=None, **kw: seen.append((url, filepath)))
    hooks.menu_item("Hi", lambda config: seen.append("menu"))
    hooks.on_api(lambda app: setattr(app, "demo_mounted", True))
''')
        m = P.PluginManager(self.config).load()
        self.assertEqual([p.name for p in m.plugins], ["demo"])
        self.assertTrue(m.plugins[0].enabled)
        m.emit("startup", config=self.config)
        m.emit("download_complete", url="u", filepath="f")
        self.assertIn(("startup", self.config), sys.modules["fluxmedia_user_plugin_demo"].seen)
        self.assertIn(("u", "f"), sys.modules["fluxmedia_user_plugin_demo"].seen)
        # menu item runs
        m.menu_items[0]["handler"](self.config)
        self.assertIn("menu", sys.modules["fluxmedia_user_plugin_demo"].seen)
        # api mount
        class FakeApp:
            def __init__(self):
                self.routes = []
                self.demo_mounted = False

            def get(self, path):
                def deco(fn):
                    self.routes.append(path)
                    return fn
                return deco
        app = FakeApp()
        m.mount_api(app)
        self.assertTrue(app.demo_mounted)

    def test_broken_plugin_isolated(self):
        self._write("bad.py", 'raise RuntimeError("boom")\n')
        self._write("good.py", 'PLUGIN = {"name": "good"}\n')
        m = P.PluginManager(self.config).load()
        by_name = {p.name: p for p in m.plugins}
        self.assertFalse(by_name["bad.py"].enabled)
        self.assertTrue(by_name["bad.py"].error)
        self.assertTrue(by_name["good"].enabled)
        # emitting with a broken plugin loaded must not raise
        m.emit("startup", config=self.config)

    def test_bad_listener_isolated(self):
        self._write("p.py", 'PLUGIN = {"name": "p"}\n')
        m = P.PluginManager(self.config).load()
        calls = []
        m._listeners["startup"].append(lambda config=None: (_ for _ in ()).throw(ValueError("x")))
        m._listeners["startup"].append(lambda config=None: calls.append(1))
        m.emit("startup", config=self.config)
        self.assertEqual(calls, [1])

    def test_enable_disable_persists(self):
        self._write("p.py", 'PLUGIN = {"name": "p"}\n')
        m = P.PluginManager(self.config).load()
        self.assertTrue(m.set_enabled("p", False))
        self.assertEqual(self.config["plugins_disabled"], ["p"])
        m2 = P.PluginManager(self.config).load()
        self.assertFalse(m2.plugins[0].enabled)
        m2.set_enabled("p", True)
        self.assertEqual(self.config["plugins_disabled"], [])

    def test_unknown_event_rejected(self):
        m = P.PluginManager(self.config)
        with self.assertRaises(ValueError):
            P.Hooks(m).on("nope", lambda: None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
