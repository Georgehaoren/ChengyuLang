from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


class SetupScriptTests(unittest.TestCase):
    脚本 = Path(__file__).resolve().parents[1] / "setup_venv.sh"

    def test_script_is_executable_and_valid_bash(self) -> None:
        self.assertTrue(os.access(self.脚本, os.X_OK))
        进程 = subprocess.run(
            ["bash", "-n", str(self.脚本)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(进程.returncode, 0, 进程.stderr)

    def test_help_does_not_create_an_environment(self) -> None:
        进程 = subprocess.run(
            ["bash", str(self.脚本), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(进程.returncode, 0, 进程.stderr)
        self.assertIn("Usage: setup_venv.sh", 进程.stdout)
        self.assertIn("CHENGYULANG_OFFLINE", 进程.stdout)


if __name__ == "__main__":
    unittest.main()

