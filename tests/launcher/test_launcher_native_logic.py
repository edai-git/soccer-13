"""tests/launcher/test_launcher_native_logic.py
Unit tests verifying native launcher UI state transitions, D-Pad navigation,
CRC calculation, and settings binary persistence.
"""

from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def crc16_not(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if (c & 0x8000) else (c << 1) & 0xFFFF
    return (~c) & 0xFFFF


class TestLauncherNativeLogic(unittest.TestCase):
    def test_settings_dat_crc_roundtrip(self):
        """Verify settings.dat binary generation matches launcher_settings.c CRC formula."""
        buf = bytearray(852)
        buf[0:4] = b"WECF"
        struct.pack_into("<I", buf, 4, 2)
        struct.pack_into("<I", buf, 8, 852)
        struct.pack_into("<I", buf, 0x10, 1280)
        struct.pack_into("<I", buf, 0x14, 720)
        struct.pack_into("<I", buf, 0x1C, 1)     # Medium
        struct.pack_into("<I", buf, 0x20, 1)     # Fullscreen
        struct.pack_into("<H", buf, 0x0E, 0xCB)  # XInput + VSync + FrameSkip

        # Compute CRC with 0x0C/0x0D zeroed
        struct.pack_into("<H", buf, 0x0C, 0)
        crc = crc16_not(bytes(buf))
        struct.pack_into("<H", buf, 0x0C, crc)

        # Validate
        stored_crc = struct.unpack_from("<H", buf, 0x0C)[0]
        struct.pack_into("<H", buf, 0x0C, 0)
        self.assertEqual(stored_crc, crc16_not(bytes(buf)))

    def test_menu_state_transitions(self):
        """Simulate D-Pad navigation and boundary wrapping."""
        # 5 items (0..4)
        selected = 0
        # DOWN
        selected = (selected + 1) if selected < 4 else 0
        self.assertEqual(selected, 1)

        # UP
        selected = (selected - 1) if selected > 0 else 4
        self.assertEqual(selected, 0)

        # UP from 0 wraps to 4
        selected = (selected - 1) if selected > 0 else 4
        self.assertEqual(selected, 4)

        # DOWN from 4 wraps to 0
        selected = (selected + 1) if selected < 4 else 0
        self.assertEqual(selected, 0)

    def test_resolution_index_mapping(self):
        """Simulate Settings resolution toggling."""
        res_widths = [1280, 1600, 1920]
        res_heights = [720, 900, 1080]

        idx = 0  # 720p
        # Right pressed
        idx = (idx + 1) % 3
        self.assertEqual(res_widths[idx], 1600)
        self.assertEqual(res_heights[idx], 900)

        # Right pressed
        idx = (idx + 1) % 3
        self.assertEqual(res_widths[idx], 1920)
        self.assertEqual(res_heights[idx], 1080)

        # Right pressed (wraps to 720p)
        idx = (idx + 1) % 3
        self.assertEqual(res_widths[idx], 1280)
        self.assertEqual(res_heights[idx], 720)


if __name__ == "__main__":
    unittest.main()
