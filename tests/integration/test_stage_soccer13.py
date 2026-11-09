"""tests/integration/test_stage_soccer13.py
Integration tests for SOCCER13 prefix staging, registry injection,
settings.dat generation, mod copying, and non-destructive save protection.
"""

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

# Load modules
stg_spec = importlib.util.spec_from_file_location("stage_soccer13", ROOT / "scripts/stage-soccer13-prefix.py")
stage_soccer13 = importlib.util.module_from_spec(stg_spec)
stg_spec.loader.exec_module(stage_soccer13)

set_spec = importlib.util.spec_from_file_location("generate_settings", ROOT / "scripts/generate-settings.py")
generate_settings = importlib.util.module_from_spec(set_spec)
set_spec.loader.exec_module(generate_settings)


def make_dummy_pe32() -> bytes:
    dos = bytearray(b"MZ" + b"\x00" * 58)
    dos += (0x80).to_bytes(4, "little")
    dos += b"\x00" * (0x80 - len(dos))
    pe = bytearray(b"PE\x00\x00")
    pe += (0x014C).to_bytes(2, "little")
    pe += (1).to_bytes(2, "little")
    pe += b"\x00" * 12
    pe += (0x00E0).to_bytes(2, "little")
    pe += (0x0102).to_bytes(2, "little")
    opt = bytearray((0x010B).to_bytes(2, "little"))
    opt += b"\x00" * 26
    opt += (0x00400000).to_bytes(4, "little")
    opt += b"\x00" * 64
    opt += (16).to_bytes(4, "little")
    dd = bytearray()
    for _ in range(5):
        dd += b"\x00" * 8
    dd += (0x1000).to_bytes(4, "little")
    dd += (0x0100).to_bytes(4, "little")
    return bytes(dos + pe + opt + dd).ljust(0x600, b"\x00")


class TestStageSoccer13(unittest.TestCase):
    def test_full_staging_pipeline_and_mod_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            game_src = tmp_path / "game_source"
            game_src.mkdir()
            (game_src / "pes2013.exe").write_bytes(make_dummy_pe32())
            (game_src / "img").mkdir()
            (game_src / "img/dt00_e.img").write_bytes(b"DATA00")
            (game_src / "kitserver13").mkdir()
            (game_src / "kitserver13/config.txt").write_text("mod=1", encoding="utf-8")
            (game_src / "dinput8.dll").write_bytes(b"HOOKDLL")

            target_prefix = tmp_path / "prefix"

            # Stage
            res = stage_soccer13.stage_soccer13_prefix(
                prefix_dir=target_prefix,
                game_source=game_src,
                width=1280,
                height=720,
                quality=1,
            )

            self.assertEqual(res["errors"], [])
            self.assertTrue(res["game_copied"])
            self.assertIn("kitserver13", res["mods_copied"])
            self.assertIn("dinput8.dll", res["mods_copied"])

            # Verify staged files in drive_c/Games/SOCCER13
            games_dir = target_prefix / "drive_c/Games/SOCCER13"
            self.assertTrue((games_dir / "pes2013.exe").is_file())
            self.assertTrue((games_dir / "img/dt00_e.img").is_file())
            self.assertTrue((games_dir / "kitserver13/config.txt").is_file())
            self.assertTrue((games_dir / "dinput8.dll").is_file())
            self.assertTrue((games_dir / "dxvk.conf").is_file())

            # Verify settings.dat
            settings_path = target_prefix / "drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/settings.dat"
            self.assertTrue(settings_path.is_file())
            self.assertEqual(settings_path.stat().st_size, 852)
            # Verify CRC
            payload = settings_path.read_bytes()
            crc = int.from_bytes(payload[0x0C:0x0E], "little")
            self.assertEqual(crc, generate_settings.crc16_not(payload[:0x0C] + b"\x00\x00" + payload[0x0E:]))

            # Verify registry
            sys_reg = (target_prefix / "system.reg").read_text(encoding="utf-8")
            self.assertIn("[Software\\Wow6432Node\\KONAMI\\PES2013]", sys_reg)
            self.assertIn('"installdir"="C:\\\\Games\\\\SOCCER13\\\\"', sys_reg)
            self.assertIn("[Hardware\\Description\\System\\CentralProcessor\\0]", sys_reg)

            user_reg = (target_prefix / "user.reg").read_text(encoding="utf-8")
            self.assertIn("[Software\\Wine\\Direct3D]", user_reg)
            self.assertIn('"VideoMemorySize"="2048"', user_reg)
            self.assertIn('"renderer"="no3d"', user_reg)

    def test_save_data_protection_during_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            game_src = tmp_path / "game_source"
            game_src.mkdir()
            (game_src / "pes2013.exe").write_bytes(make_dummy_pe32())
            (game_src / "img").mkdir()
            (game_src / "img/dt00_e.img").touch()
            (game_src / "save").mkdir()
            (game_src / "save/EDIT.bin").write_bytes(b"SEED_SAVE")

            target_prefix = tmp_path / "prefix"

            # Stage 1: initial install
            stage_soccer13.stage_soccer13_prefix(prefix_dir=target_prefix, game_source=game_src)
            save_path = target_prefix / "drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/save/EDIT.bin"
            self.assertTrue(save_path.is_file())
            self.assertEqual(save_path.read_bytes(), b"SEED_SAVE")

            # User plays game, edits players/teams:
            save_path.write_bytes(b"USER_CUSTOMIZED_SAVED_CAREER_DATA")

            # Stage 2: repair mode
            res = stage_soccer13.stage_soccer13_prefix(
                prefix_dir=target_prefix,
                game_source=game_src,
                repair=True,
            )

            self.assertEqual(res["errors"], [])
            self.assertEqual(res["saves_protected"], 1)
            # Verify user's career save was NOT overwritten
            self.assertEqual(save_path.read_bytes(), b"USER_CUSTOMIZED_SAVED_CAREER_DATA")


if __name__ == "__main__":
    unittest.main()
