import importlib.util
import struct
import unittest
from pathlib import Path

# Load scripts/generate-settings.py dynamically
GEN_SETTINGS_PATH = Path(__file__).resolve().parents[2] / "scripts/generate-settings.py"
spec = importlib.util.spec_from_file_location("generate_settings", GEN_SETTINGS_PATH)
gen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_mod)

SIZE = gen_mod.SIZE
CHECKSUM_AT = gen_mod.CHECKSUM_AT
generate_settings = gen_mod.generate_settings
validate_settings = gen_mod.validate_settings


class TestSettingsDat(unittest.TestCase):
    def test_size_and_magic(self):
        data = generate_settings(1280, 720, quality=1)
        self.assertEqual(len(data), SIZE)
        self.assertEqual(data[:4], b"WECF")

    def test_known_1080p_checksum(self):
        # Reference settings.exe vector (Flags=0xCB: Frame Skipping ON, Movie Playback ON)
        ref_data = generate_settings(
            1920, 1080, quality=2, fullscreen=True, xinput=True,
            vsync=True, frame_skipping=True, disable_movie=False
        )
        self.assertTrue(validate_settings(ref_data))
        ref_crc = struct.unpack_from("<H", ref_data, CHECKSUM_AT)[0]
        self.assertEqual(ref_crc, 0x3B3C)

        # Default PS4 smooth 60 FPS vector (Flags=0xCD: Frame Skipping OFF, Disable Movie Playback ON)
        ps4_data = generate_settings(1920, 1080, quality=2, fullscreen=True, xinput=True)
        self.assertTrue(validate_settings(ps4_data))
        flags = struct.unpack_from("<H", ps4_data, 0x0E)[0]
        self.assertEqual(flags, 0x00CD)

    def test_dimensions_packed(self):
        data = generate_settings(1280, 720, quality=1)
        w = struct.unpack_from("<I", data, 0x10)[0]
        h = struct.unpack_from("<I", data, 0x14)[0]
        self.assertEqual(w, 1280)
        self.assertEqual(h, 720)
        self.assertTrue(validate_settings(data))

    def test_invalid_data_rejected(self):
        # Corrupted size
        self.assertFalse(validate_settings(b"WECF\x00\x00"))
        # Corrupted magic
        data = bytearray(generate_settings(1280, 720))
        data[0:4] = b"XXXX"
        self.assertFalse(validate_settings(bytes(data)))
        # Corrupted checksum
        data = bytearray(generate_settings(1280, 720))
        data[CHECKSUM_AT] ^= 0xFF
        self.assertFalse(validate_settings(bytes(data)))


if __name__ == "__main__":
    unittest.main()
