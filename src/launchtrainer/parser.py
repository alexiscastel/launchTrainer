from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


TIME_FORMAT = "%H:%M:%S.%f"
REQUIRED_COLUMNS = (
    "Time",
    "GAlt(m)",
    "GSpd(kmh)",
    "AccX(g)",
    "AccY(g)",
    "AccZ(g)",
    "GYRX(°)",
    "GYRY(°)",
    "GYRZ(°)",
    "ETHR(%)",
    "FM",
)


class LaunchTrainerError(Exception):
    pass


class CSVSchemaError(LaunchTrainerError):
    pass


class CSVDataError(LaunchTrainerError):
    pass


@dataclass(frozen=True)
class Sample:
    row_number: int
    time_label: str
    t_s: float
    alt_m: float
    speed_kmh: float
    throttle_pct: float
    accel_mag_g: float
    gyro_mag_dps: float
    flight_mode: str


def parse_time_value(raw_time: str) -> datetime:
    try:
        return datetime.strptime(raw_time, TIME_FORMAT)
    except ValueError as exc:
        raise CSVDataError(f"malformed time value: {raw_time!r}") from exc


def parse_csv(csv_path: str | Path) -> list[Sample]:
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CSVDataError("empty file or missing CSV header")

        missing_columns = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing_columns:
            missing_list = ", ".join(missing_columns)
            raise CSVSchemaError(f"missing required columns: {missing_list}")

        rows = list(reader)

    if not rows:
        raise CSVDataError("file contains no telemetry rows")

    first_time = parse_time_value(rows[0]["Time"])
    samples: list[Sample] = []

    for row_number, row in enumerate(rows, start=2):
        timestamp = parse_time_value(row["Time"])
        t_s = (timestamp - first_time).total_seconds()

        try:
            accel_mag_g = math.sqrt(
                float(row["AccX(g)"]) ** 2
                + float(row["AccY(g)"]) ** 2
                + float(row["AccZ(g)"]) ** 2
            )
            gyro_mag_dps = math.sqrt(
                float(row["GYRX(°)"]) ** 2
                + float(row["GYRY(°)"]) ** 2
                + float(row["GYRZ(°)"]) ** 2
            )
            sample = Sample(
                row_number=row_number,
                time_label=row["Time"],
                t_s=t_s,
                alt_m=float(row["GAlt(m)"]),
                speed_kmh=float(row["GSpd(kmh)"]),
                throttle_pct=float(row["ETHR(%)"]),
                accel_mag_g=accel_mag_g,
                gyro_mag_dps=gyro_mag_dps,
                flight_mode=row["FM"].strip(),
            )
        except ValueError as exc:
            raise CSVDataError(f"non-numeric telemetry value on row {row_number}") from exc

        samples.append(sample)

    return samples
