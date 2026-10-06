"""Unit tests for install detection + doctor report. Run: python3 test_doctor.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fluxmedia.core import get_install_info


class DoctorTest(unittest.TestCase):
    def test_report_shape(self):
        info = get_install_info()
        for key in ("method", "binary", "python", "python_path", "in_venv"):
            self.assertIn(key, info)
        self.assertIn(info["method"],
                      ("pipx", "editable", "venv", "system", "source", "unknown"))
        self.assertRegex(info["python"], r"^\d+\.\d+\.\d+$")

    def test_repo_checkout_detected(self):
        info = get_install_info()
        self.assertEqual(info["method"], "editable")
        self.assertTrue(os.path.isdir(os.path.join(info["source_dir"], ".git")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
