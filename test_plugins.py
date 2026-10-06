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
        # NEVER touch the real config.json: set_enabled() persists via core.
        import fluxmedia.core as _core
        self._orig_save = _core.save_config
        _core.save_config = lambda *a, **k: True

    def tearDown(self):
        import fluxmedia.core as _core
        _core.save_config = self._orig_save
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

    def test_filter_plugins(self):
        from fluxmedia.plugins import Plugin, filter_plugins, parse_multi_pick
        ps = [
            Plugin(name="csv-logger", description="Logs downloads", author="Flux"),
            Plugin(name="doc-bridge", description="Routes via engine", author="Pdev"),
            Plugin(name="hello-world", description="Greets", author="Flux"),
        ]
        self.assertEqual(len(filter_plugins(ps, "")), 3)
        self.assertEqual(len(filter_plugins(ps, "  ")), 3)
        self.assertEqual([p.name for p in filter_plugins(ps, "csv")], ["csv-logger"])
        self.assertEqual([p.name for p in filter_plugins(ps, "FLUX")], ["csv-logger", "hello-world"])
        self.assertEqual([p.name for p in filter_plugins(ps, "engine")], ["doc-bridge"])
        self.assertEqual([p.name for p in filter_plugins(ps, "pdev")], ["doc-bridge"])
        self.assertEqual(filter_plugins(ps, "zzz"), [])

    def test_parse_multi_pick(self):
        from fluxmedia.plugins import parse_multi_pick
        self.assertEqual(parse_multi_pick("1 3 4", 5), [0, 2, 3])
        self.assertEqual(parse_multi_pick("2", 3), [1])
        self.assertEqual(parse_multi_pick("3 3 1", 3), [2, 0])  # deduped
        self.assertEqual(parse_multi_pick("  1   2  ", 2), [0, 1])
        self.assertIsNone(parse_multi_pick("", 3))
        self.assertIsNone(parse_multi_pick("   ", 3))
        self.assertIsNone(parse_multi_pick("0", 3))
        self.assertIsNone(parse_multi_pick("4", 3))   # out of range
        self.assertIsNone(parse_multi_pick("1 x", 3))  # whole input rejected
        self.assertIsNone(parse_multi_pick("abc", 3))

    def test_permissions_and_safe_mode(self):
        from fluxmedia.plugins import (
            PluginManager, declared_permissions, granted_permissions,
            record_grants, set_safe_mode, KNOWN_PERMISSIONS,
        )
        mod = type("M", (), {})()
        mod.PERMISSIONS = ["network", " Filesystem ", 42, "network", "custom-cap"]
        self.assertEqual(declared_permissions(mod),
                         ["network", "filesystem", "custom-cap"])
        self.assertEqual(declared_permissions(object()), [])
        self.assertTrue({"network", "filesystem", "web"} <= KNOWN_PERMISSIONS)

        cfg: dict = {}
        self.assertEqual(granted_permissions(cfg, "p"), [])
        record_grants(cfg, "p", ["network"])
        self.assertEqual(granted_permissions(cfg, "p"), ["network"])
        self.assertEqual(cfg["plugins_granted"], {"p": ["network"]})

        set_safe_mode(True)
        try:
            m = PluginManager({}).load()
            self.assertEqual(m.plugins, [])
            self.assertEqual(m.menu_items, [])
        finally:
            set_safe_mode(False)
        # env-var path
        os.environ["FLUXMEDIA_SAFE_MODE"] = "1"
        try:
            m2 = PluginManager({}).load()
            self.assertEqual(m2.plugins, [])
        finally:
            del os.environ["FLUXMEDIA_SAFE_MODE"]

    def test_vendored_dependency_importable(self):
        # A helper folder/file sitting beside the plugin (not a plugin
        # itself) must be importable without the plugin hacking sys.path.
        with open(os.path.join(self.tmp, "vendored_helper.py"), "w", encoding="utf-8") as f:
            f.write('VALUE = 42\n')
        self._write("p.py", 'PLUGIN = {"name": "p"}\nimport vendored_helper\nRESULT = vendored_helper.VALUE\n')
        m = P.PluginManager(self.config).load()
        self.assertTrue(m.plugins[0].enabled)
        self.assertEqual(sys.modules["fluxmedia_user_plugin_p"].RESULT, 42)


if __name__ == "__main__":
    unittest.main(verbosity=2)
