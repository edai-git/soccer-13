"""tests/package/test_release_deliverables.py
Unit tests verifying Phase 6 release deliverables, THIRD_PARTY.md licensing,
and automated session log analysis for Phase 4.
"""

from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TestReleaseDeliverables(unittest.TestCase):
    def test_third_party_notice_presence_and_licenses(self):
        """Verify THIRD_PARTY.md exists and covers all required upstream projects."""
        tp = ROOT / "THIRD_PARTY.md"
        self.assertTrue(tp.is_file(), "Missing THIRD_PARTY.md in project root")

        content = tp.read_text(encoding="utf-8")
        self.assertIn("orbis-win", content)
        self.assertIn("Wine", content)
        self.assertIn("Mesa / RADV", content)
        self.assertIn("DXVK", content)
        self.assertIn("OpenOrbis", content)
        self.assertIn("FreeType", content)
        self.assertIn("Clean-Room & Non-Affiliation", content)

    def test_analyze_session_log_success(self):
        """Test analyze-session-log.py parser on simulated successful gameplay log."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("analyze_log", ROOT / "scripts/analyze-session-log.py")
        analyze_log = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analyze_log)

        sample_log = """
PW_WINE64 build_marker=GLDS13013-01.00-pw50f5b26
PW_WINE64 relocatable eboot release status=0
win/wine/lib/wine/x86_64-windows/wow64native.dll mapped
loading pes2013.exe at 0x400000
reading C:\\Games\\SOCCER13\\settings.dat
win32u: headless surface: res 0
WINE_PS5_SCANOUT surface presented
wineps5: audio stream started
pw_wine_pad_read events active
guest processes ended: exit status 0
"""
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
            f.write(sample_log)
            temp_path = Path(f.name)

        try:
            report = analyze_log.analyze_session_log(temp_path)
            self.assertTrue(report["valid"])
            self.assertEqual(report["faults"], [])
            self.assertIn("PASS", report["verdict"])
            self.assertTrue(report["stages"]["stage1_wine_startup"])
            self.assertTrue(report["stages"]["stage2_process_startup"])
            self.assertTrue(report["stages"]["stage4_vulkan_surface"])
            self.assertTrue(report["stages"]["stage8_audio"])
            self.assertTrue(report["stages"]["stage9_controller"])
            self.assertTrue(report["stages"]["stage12_clean_exit"])
        finally:
            temp_path.unlink(missing_ok=True)

    def test_analyze_session_log_fault_detection(self):
        """Test analyze-session-log.py detection of PW_EXCEPTION32 or GPU allocation error."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("analyze_log", ROOT / "scripts/analyze-session-log.py")
        analyze_log = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analyze_log)

        fault_log = """
PW_WINE64 build_marker=GLDS13013-01.00
PW_EXCEPTION32 at 0x00451a2b: code=c0000005 flags=0
PW_ORBIS_VA_FAIL in radv_alloc_memory
"""
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
            f.write(fault_log)
            temp_path = Path(f.name)

        try:
            report = analyze_log.analyze_session_log(temp_path)
            self.assertTrue(report["valid"])
            self.assertEqual(len(report["faults"]), 2)
            self.assertEqual(report["verdict"], "FAIL_WITH_EXCEPTIONS")
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
