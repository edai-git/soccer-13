import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

# Load validate-game module
val_spec = importlib.util.spec_from_file_location("validate_game", ROOT / "scripts/validate-game.py")
validate_game = importlib.util.module_from_spec(val_spec)
val_spec.loader.exec_module(validate_game)


def make_dummy_pe32() -> bytes:
    """Generates minimal valid PE32 headers for testing."""
    # Dos header (64 bytes)
    dos = bytearray(b"MZ" + b"\x00" * 58)
    dos += (0x80).to_bytes(4, "little")  # e_lfanew = 0x80
    dos += b"\x00" * (0x80 - len(dos))

    # PE Signature
    pe = bytearray(b"PE\x00\x00")
    # File Header: Machine=0x014c (i386), nsections=1, chars=0x0102 (executable, 32-bit)
    pe += (0x014C).to_bytes(2, "little")
    pe += (1).to_bytes(2, "little")
    pe += b"\x00" * 12
    pe += (0x00E0).to_bytes(2, "little")  # sizeof opt header
    pe += (0x0102).to_bytes(2, "little")

    # Optional Header (PE32 magic=0x10b)
    opt = bytearray((0x010B).to_bytes(2, "little"))
    opt += b"\x00" * 26
    opt += (0x00400000).to_bytes(4, "little")  # ImageBase
    opt += b"\x00" * 64
    opt += (16).to_bytes(4, "little")  # NumberOfRvaAndSizes

    # Data directories (need at least 6 for reloc)
    dd = bytearray()
    for _ in range(5):
        dd += b"\x00" * 8
    # 6th is reloc
    dd += (0x1000).to_bytes(4, "little")  # RVA
    dd += (0x0100).to_bytes(4, "little")  # Size

    payload = bytes(dos + pe + opt + dd)
    return payload.ljust(0x600, b"\x00")


class TestLauncherLogic(unittest.TestCase):
    def test_installation_validator_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report = validate_game.validate_game_installation(tmp_path)
            self.assertFalse(report["valid"])
            self.assertTrue(any("pes2013.exe" in e for e in report["errors"]))

    def test_installation_validator_valid_pe32_and_repack(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "pes2013.exe").write_bytes(make_dummy_pe32())
            (tmp_path / "img").mkdir()
            (tmp_path / "img/dt00_e.img").touch()

            # No code.txt -> Repack mode
            report = validate_game.validate_game_installation(tmp_path)
            self.assertTrue(report["valid"])
            self.assertTrue(report["is_repack"])
            self.assertEqual(report["product_code"], validate_game.DEFAULT_PRODUCT_CODE)
            self.assertEqual(report["img_count"], 1)

    def test_installation_validator_with_code_and_mods(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "pes2013.exe").write_bytes(make_dummy_pe32())
            (tmp_path / "img").mkdir()
            (tmp_path / "img/dt00_e.img").touch()
            (tmp_path / "code.txt").write_text("CUSTOM-SERIAL-12345", encoding="utf-8")

            # Add mod folder & DLL
            (tmp_path / "kitserver13").mkdir()
            (tmp_path / "kload.dll").touch()

            report = validate_game.validate_game_installation(tmp_path)
            self.assertTrue(report["valid"])
            self.assertFalse(report["is_repack"])
            self.assertEqual(report["product_code"], "CUSTOM-SERIAL-12345")
            self.assertIn("dir:kitserver13", report["mods_detected"])
            self.assertIn("dll:kload.dll", report["mods_detected"])


if __name__ == "__main__":
    unittest.main()
