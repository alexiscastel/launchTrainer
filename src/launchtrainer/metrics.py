from __future__ import annotations

from dataclasses import dataclass

from .detection import DetectionResult
from .parser import Sample


@dataclass(frozen=True)
class MetricResult:
    launch_height_m: float
    time_to_apex_s: float
    max_climb_rate_mps: float


def compute_metrics(
    samples: list[Sample],
    smoothed_altitudes_m: list[float],
    climb_rates_mps: list[float],
    detection: DetectionResult,
) -> MetricResult:
    start_idx = detection.start_idx
    end_idx = detection.end_idx

    start_altitude_m = smoothed_altitudes_m[start_idx]
    peak_altitude_m = max(smoothed_altitudes_m[start_idx : end_idx + 1])
    max_climb_rate_mps = max(climb_rates_mps[start_idx : end_idx + 1], default=0.0)

    launch_height_m = max(0.0, peak_altitude_m - start_altitude_m)
    time_to_apex_s = max(0.0, detection.end_time_s - detection.start_time_s)

    return MetricResult(
        launch_height_m=launch_height_m,
        time_to_apex_s=time_to_apex_s,
        max_climb_rate_mps=max(0.0, max_climb_rate_mps),
    )
