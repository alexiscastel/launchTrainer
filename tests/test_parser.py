from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from launchtrainer.parser import CSVDataError, CSVSchemaError, parse_csv, parse_time_value


class ParserTests(unittest.TestCase):
    def test_parse_sample_fixture(self) -> None:
        samples = parse_csv(Path("tests/Timber-2024-11-09-162030.csv"))

        self.assertEqual(len(samples), 945)
        self.assertEqual(samples[0].t_s, 0.0)
        self.assertGreater(samples[1].t_s, samples[0].t_s)
        self.assertGreater(samples[0].accel_mag_g, 0.0)
        self.assertEqual(samples[0].flight_mode, "3 AS3X")

    def test_parse_time_value_rejects_bad_time(self) -> None:
        with self.assertRaises(CSVDataError):
            parse_time_value("16:20")

    def test_parse_csv_rejects_missing_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "missing.csv"
            csv_path.write_text("Time,GAlt(m)\n16:20:30.210,178.2\n", encoding="utf-8")

            with self.assertRaises(CSVSchemaError):
                parse_csv(csv_path)

    def test_parse_csv_rejects_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            csv_path.write_text("", encoding="utf-8")

            with self.assertRaises(CSVDataError):
                parse_csv(csv_path)

    def test_parse_csv_rejects_bad_numeric_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "bad.csv"
            csv_path.write_text(
                (
                    "Time,GAlt(m),GSpd(kmh),AccX(g),AccY(g),AccZ(g),"
                    "GYRX(°),GYRY(°),GYRZ(°),ETHR(%),FM\n"
                    "16:20:30.210,bad,0,0.1,0.2,0.3,0,0,0,0,Mode\n"
                ),
                encoding="utf-8",
            )

            with self.assertRaises(CSVDataError):
                parse_csv(csv_path)
