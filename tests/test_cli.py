from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def test_cli_analyze_writes_json_and_warning_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "result.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "launchtrainer",
                    "analyze",
                    "tests/Timber-2024-11-09-162030.csv",
                    "--json-out",
                    str(json_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(json_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "warning")
            self.assertEqual(payload["detection"]["method"], "auto_v1")
            self.assertIn(payload["detection"]["confidence"], {"high", "medium", "low"})
            self.assertGreaterEqual(payload["metrics"]["launch_height_m"], 0.0)
            self.assertGreaterEqual(payload["metrics"]["time_to_apex_s"], 0.0)
            self.assertGreaterEqual(payload["metrics"]["max_climb_rate_mps"], 0.0)
            self.assertTrue(payload["warnings"])
            self.assertIn("Status: warning", result.stdout)

    def test_cli_repeat_runs_are_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_a = Path(temp_dir) / "a.json"
            json_b = Path(temp_dir) / "b.json"

            for json_path in (json_a, json_b):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "launchtrainer",
                        "analyze",
                        "tests/Timber-2024-11-09-162030.csv",
                        "--json-out",
                        str(json_path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)

            self.assertEqual(
                json.loads(json_a.read_text(encoding="utf-8")),
                json.loads(json_b.read_text(encoding="utf-8")),
            )

    def test_cli_returns_error_for_bad_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "bad_time.csv"
            json_path = Path(temp_dir) / "bad_time.json"
            csv_path.write_text(
                (
                    "Time,GAlt(m),GSpd(kmh),AccX(g),AccY(g),AccZ(g),"
                    "GYRX(°),GYRY(°),GYRZ(°),ETHR(%),FM\n"
                    "bad-time,100,0,0.1,0.2,0.3,0,0,0,0,Mode\n"
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "launchtrainer",
                    "analyze",
                    str(csv_path),
                    "--json-out",
                    str(json_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "error")
            self.assertTrue(any("malformed time value" in warning for warning in payload["warnings"]))
