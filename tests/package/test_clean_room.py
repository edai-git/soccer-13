import subprocess
import unittest
from pathlib import Path


class TestCleanRoomHygiene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]

    def test_no_forbidden_files_in_git(self):
        # Query git for tracked files in top-level repo
        res = subprocess.run(
            ["git", "-C", str(self.root), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]

        forbidden_exts = {".exe", ".dll", ".img", ".sorbisdmp", ".pkg"}
        for f in tracked_files:
            # Skip checking inside submodule pointer
            if f.startswith("runtime/orbis-win"):
                continue
            path = Path(f)
            self.assertNotIn(
                path.suffix.lower(),
                forbidden_exts,
                f"Forbidden binary file tracked in git: {f}",
            )

    def test_no_hardcoded_ips_in_committed_files(self):
        res = subprocess.run(
            ["git", "-C", str(self.root), "grep", "-I", "-E", r"\b192\.168\.[0-9]+\.[0-9]+\b"],
            capture_output=True,
            text=True,
        )
        # git grep returns 0 if found, 1 if not found
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            # Allow examples in documentation or config.env.example
            filtered = [
                line for line in lines
                if not any(allowed in line for allowed in ["docs/", "README.md", "runtime/orbis-win"])
            ]
            self.assertEqual(len(filtered), 0, f"Potential real console IP hardcoded: {filtered}")


if __name__ == "__main__":
    unittest.main()

