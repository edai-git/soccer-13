import tempfile
import unittest
from pathlib import Path


def validate_installation_source(src_dir: Path) -> tuple[bool, str]:
    if not (src_dir / "pes2013.exe").is_file():
        return False, "Missing pes2013.exe"
    if not (src_dir / "img").is_dir():
        return False, "Missing img directory"
    return True, "Valid"


def read_product_code(src_dir: Path) -> str:
    code_file = src_dir / "code.txt"
    if not code_file.is_file():
        return ""
    return code_file.read_text(encoding="utf-8").strip()


def seed_save_files(seed_dir: Path, target_dir: Path) -> list[str]:
    """Copy save files only if they do not exist in target_dir (never overwrite)."""
    copied = []
    target_dir.mkdir(parents=True, exist_ok=True)
    if not seed_dir.exists():
        return copied
    for src_file in seed_dir.glob("*"):
        if src_file.is_file():
            dst = target_dir / src_file.name
            if not dst.exists():
                dst.write_bytes(src_file.read_bytes())
                copied.append(src_file.name)
    return copied


class TestLauncherLogic(unittest.TestCase):
    def test_installation_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            valid, reason = validate_installation_source(tmp_path)
            self.assertFalse(valid)
            self.assertEqual(reason, "Missing pes2013.exe")

            (tmp_path / "pes2013.exe").touch()
            valid, reason = validate_installation_source(tmp_path)
            self.assertFalse(valid)
            self.assertEqual(reason, "Missing img directory")

            (tmp_path / "img").mkdir()
            valid, reason = validate_installation_source(tmp_path)
            self.assertTrue(valid)
            self.assertEqual(reason, "Valid")

    def test_read_product_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self.assertEqual(read_product_code(tmp_path), "")

            (tmp_path / "code.txt").write_text("XXXX-YYYY-ZZZZ\n", encoding="utf-8")
            self.assertEqual(read_product_code(tmp_path), "XXXX-YYYY-ZZZZ")

    def test_save_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            seed = tmp_path / "seed"
            target = tmp_path / "target"
            seed.mkdir()
            target.mkdir()

            (seed / "EDIT.bin").write_bytes(b"NEW_EDIT_DATA")
            # Target already has an existing save
            (target / "EDIT.bin").write_bytes(b"EXISTING_USER_SAVE")

            copied = seed_save_files(seed, target)
            self.assertEqual(copied, [])
            self.assertEqual((target / "EDIT.bin").read_bytes(), b"EXISTING_USER_SAVE")

            # Add a file target doesn't have
            (seed / "OPTION.bin").write_bytes(b"OPTION_DATA")
            copied = seed_save_files(seed, target)
            self.assertEqual(copied, ["OPTION.bin"])
            self.assertEqual((target / "OPTION.bin").read_bytes(), b"OPTION_DATA")


if __name__ == "__main__":
    unittest.main()

