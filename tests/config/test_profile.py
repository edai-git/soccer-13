import configparser
import unittest
from pathlib import Path


class TestSoccer13Profile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile_path = Path(__file__).resolve().parents[2] / "app/profiles/soccer13.profile"
        cls.config = configparser.ConfigParser(strict=False)
        cls.assertTrue(cls.profile_path.exists(), f"Profile not found at {cls.profile_path}")
        cls.config.read(cls.profile_path, encoding="utf-8")

    def test_application_section(self):
        self.assertIn("application", self.config)
        app = self.config["application"]
        self.assertEqual(app.get("id"), "soccer13")
        self.assertIn(app.get("name"), ("SOCCER 13", "SOCCER13"))
        self.assertEqual(app.get("prefix"), "soccer13")
        self.assertEqual(app.get("architecture"), "pe32")
        self.assertEqual(app.get("graphics"), "dxvk")
        self.assertEqual(app.get("runtime"), "wine-wow64")
        self.assertTrue(app.get("executable").endswith("pes2013.exe"))

    def test_display_section(self):
        self.assertIn("display", self.config)
        self.assertEqual(self.config["display"].get("desktop"), "1920x1080")

    def test_input_section(self):
        self.assertIn("input", self.config)
        inp = self.config["input"]
        self.assertEqual(inp.get("mode"), "xinput")
        self.assertEqual(inp.get("touchpad"), "mouse_left")

    def test_runtime_section(self):
        self.assertIn("runtime", self.config)
        self.assertEqual(self.config["runtime"].get("cpu"), "native")


if __name__ == "__main__":
    unittest.main()

