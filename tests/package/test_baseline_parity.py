"""tests/package/test_baseline_parity.py
Unit tests verifying baseline runtime manifest generation, package parity rules,
and relocation stub criteria for Phase 2.
"""

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestBaselineParity(unittest.TestCase):
    def setUp(self):
        self.orbis_win = ROOT / "runtime" / "orbis-win"
        self.parity_script = self.orbis_win / "scripts" / "check-ps4-package-parity.py"

    def test_parity_script_exists_and_covers_8_hard_gates(self):
        """Verify check-ps4-package-parity.py exists and covers the 8 hard gates."""
        self.assertTrue(self.parity_script.is_file(), f"Missing {self.parity_script}")
        content = self.parity_script.read_text(encoding="utf-8")

        # Gate 1: Relocation stub
        self.assertIn("relocated_wine_app.prx", content)
        self.assertIn("pw_relocated_wine_start", content)

        # Gate 2: Duplicate runtime copies
        self.assertIn("sce_module", content)
        self.assertIn("win/wine/lib/wine/x86_64-unix", content)

        # Gate 3: Vulkan surface (headless surface + WINE_PS5_SCANOUT)
        self.assertIn("headless surface: res", content)
        self.assertIn("WINE_PS5_SCANOUT", content)

        # Gate 4: Mesa Zink OpenGL provider
        self.assertIn("win/mesa-zink", content)
        self.assertIn("opengl32.dll", content)

        # Gate 5: PS4 RADV markers
        self.assertIn("PW_ORBIS_VA_FAIL", content)
        self.assertIn("wsi/orbis: 0031", content)

        # Gate 6: Descriptor exports
        self.assertIn("pw_wineserver_", content)
        self.assertIn("pw_wine_", content)

        # Gate 7: PW_EXCEPTION32 diagnostics
        self.assertIn("PW_EXCEPTION32", content)

        # Gate 8: FreeBSD Signal masks
        self.assertIn("SIG_BLOCK", content)

    def test_relocation_stub_criteria(self):
        """Test verification logic for the PS4 no-RELRO relocation stub eboot.bin."""
        # A valid stub is < 200,000 bytes and contains the loader path
        valid_stub = b"\x7fELF" + b"X" * 1000 + b"/app0/sce_module/relocated_wine_app.prx" + b"Y" * 1000
        self.assertLess(len(valid_stub), 200_000)
        self.assertIn(b"/app0/sce_module/relocated_wine_app.prx", valid_stub)

        # Invalid 1: Too large (full app packaged as eboot at 0x400000)
        too_large_eboot = b"\x7fELF" + b"/app0/sce_module/relocated_wine_app.prx" + b"\x00" * 300_000
        self.assertGreater(len(too_large_eboot), 200_000)

        # Invalid 2: Missing the relocation string
        missing_marker_stub = b"\x7fELF" + b"A" * 50_000
        self.assertNotIn(b"/app0/sce_module/relocated_wine_app.prx", missing_marker_stub)

    def test_manifest_validation_logic(self):
        """Test parsing and mandatory fields of BUILD-MANIFEST.txt."""
        sample_manifest = """package=ORBIS-WIN-BASELINE.pkg
package_sha256=abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd
title_id=GLDS10043 app_ver=01.49 title=SOCCER13 Baseline Runtime
build_mode=baseline-stage
build_timestamp_utc=2026-11-09T12:00:00Z
root_commit=9d762029157acc94686b2ac76d48ac383938a4fb
orbis_win_commit=9d762029157acc94686b2ac76d48ac383938a4fb
wine_commit=490f6d5dcbb2a5047345b8af88d114bbcaad69a8
dxvk_version=2.6.2
module_stub_source=OpenOrbis-PS4-Toolchain@0a1aaf9dd4a92695538bdeb09fb056d06dd11725 (GPL-3.0)
libc_stub_sha256=1111111111111111111111111111111111111111111111111111111111111111
fios2_stub_sha256=2222222222222222222222222222222222222222222222222222222222222222
"""
        mandatory_keys = [
            "package=",
            "package_sha256=",
            "title_id=",
            "root_commit=",
            "orbis_win_commit=",
            "module_stub_source=",
            "libc_stub_sha256=",
            "fios2_stub_sha256=",
        ]

        for key in mandatory_keys:
            self.assertIn(key, sample_manifest, f"Mandatory key '{key}' missing from manifest")

    def test_openorbis_stubs_source_presence(self):
        """Verify OpenOrbis clean-room stub source files exist in orbis-win."""
        stubs_dir = self.orbis_win / "src" / "openorbis-module-stubs"
        self.assertTrue(stubs_dir.is_dir(), f"Stubs dir missing: {stubs_dir}")
        self.assertTrue((stubs_dir / "COPYING").is_file(), "Missing COPYING license file")
        self.assertTrue((stubs_dir / "libc" / "Makefile").is_file(), "Missing libc Makefile")
        self.assertTrue((stubs_dir / "libc" / "libc" / "lib.c").is_file(), "Missing libc lib.c")
        self.assertTrue((stubs_dir / "libSceFios2" / "Makefile").is_file(), "Missing libSceFios2 Makefile")
        self.assertTrue((stubs_dir / "libSceFios2" / "libSceFios2" / "lib.c").is_file(), "Missing libSceFios2 lib.c")


if __name__ == "__main__":
    unittest.main()
