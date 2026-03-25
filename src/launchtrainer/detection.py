from __future__ import annotations

from dataclasses import dataclass

from .parser import Sample


@dataclass(frozen=True)
class DetectionResult:
    method: str
    confidence: str
    start_idx: int
    end_idx: int
    start_time_s: float
    end_time_s: float
    sample_period_s: float
    warnings: list[str]


@dataclass(frozen=True)
class CandidateWindow:
    score: float
    start_idx: int
    end_idx: int
    apex_idx: int
    alt_gain_m: float
    speed_gain_kmh: float
    onset_activity: float
    mean_throttle_pct: float
    throttle_dominant: bool
    clear_apex: bool


def _window_mean(values: list[float], start_idx: int, end_idx: int) -> float:
    segment = values[start_idx : end_idx + 1]
    return sum(segment) / len(segment)


def _candidate_score(
    samples: list[Sample],
    smoothed_altitudes_m: list[float],
    start_idx: int,
    end_idx: int,
) -> CandidateWindow:
    window_altitudes = smoothed_altitudes_m[start_idx : end_idx + 1]
    base_altitude = smoothed_altitudes_m[start_idx]
    peak_altitude = max(window_altitudes)
    apex_offset = window_altitudes.index(peak_altitude)
    apex_idx = start_idx + apex_offset

    peak_speed = max(sample.speed_kmh for sample in samples[start_idx : end_idx + 1])
    mean_throttle_pct = _window_mean(
        [sample.throttle_pct for sample in samples],
        start_idx,
        end_idx,
    )
    mean_accel_mag_g = _window_mean(
        [sample.accel_mag_g for sample in samples],
        start_idx,
        min(end_idx, start_idx + 2),
    )
    mean_gyro_mag_dps = _window_mean(
        [sample.gyro_mag_dps for sample in samples],
        start_idx,
        min(end_idx, start_idx + 2),
    )

    alt_gain_m = peak_altitude - base_altitude
    speed_gain_kmh = peak_speed - samples[start_idx].speed_kmh
    onset_activity = max(mean_accel_mag_g - 1.0, 0.0) + (mean_gyro_mag_dps / 180.0)
    throttle_dominant = mean_throttle_pct >= 40.0
    clear_apex = apex_idx < end_idx

    score = (
        alt_gain_m * 2.0
        + speed_gain_kmh * 0.25
        + onset_activity * 6.0
        - (mean_throttle_pct / 100.0) * 10.0
    )
    if throttle_dominant:
        score -= 5.0
    if not clear_apex:
        score -= 2.0

    return CandidateWindow(
        score=score,
        start_idx=start_idx,
        end_idx=end_idx,
        apex_idx=apex_idx,
        alt_gain_m=alt_gain_m,
        speed_gain_kmh=speed_gain_kmh,
        onset_activity=onset_activity,
        mean_throttle_pct=mean_throttle_pct,
        throttle_dominant=throttle_dominant,
        clear_apex=clear_apex,
    )


def detect_launch(
    samples: list[Sample],
    smoothed_altitudes_m: list[float],
    sample_period_s: float,
) -> DetectionResult:
    warnings: list[str] = []

    if sample_period_s > 0.25:
        warnings.append(
            f"Coarse sampling cadence ({sample_period_s:.3f}s) may alias launch dynamics."
        )

    if len(samples) < 2:
        warnings.append("Insufficient samples for robust launch detection.")
        return DetectionResult(
            method="auto_v1",
            confidence="low",
            start_idx=0,
            end_idx=0,
            start_time_s=samples[0].t_s if samples else 0.0,
            end_time_s=samples[0].t_s if samples else 0.0,
            sample_period_s=sample_period_s,
            warnings=warnings,
        )

    min_duration_s = 2.0
    max_duration_s = 8.0

    min_window_samples = max(2, int(round(min_duration_s / sample_period_s))) if sample_period_s else 2
    max_window_samples = (
        max(min_window_samples, int(round(max_duration_s / sample_period_s)))
        if sample_period_s
        else min(len(samples), 16)
    )

    best: CandidateWindow | None = None

    for start_idx in range(0, len(samples) - min_window_samples + 1):
        for window_len in range(min_window_samples, max_window_samples + 1):
            end_idx = start_idx + window_len - 1
            if end_idx >= len(samples):
                break

            candidate = _candidate_score(samples, smoothed_altitudes_m, start_idx, end_idx)
            if best is None or candidate.score > best.score:
                best = candidate

    if best is None:
        warnings.append("Unable to score any launch candidate windows.")
        return DetectionResult(
            method="auto_v1",
            confidence="low",
            start_idx=0,
            end_idx=0,
            start_time_s=samples[0].t_s,
            end_time_s=samples[0].t_s,
            sample_period_s=sample_period_s,
            warnings=warnings,
        )

    confidence = "high"
    if best.alt_gain_m < 5.0 or best.onset_activity < 0.4 or best.throttle_dominant:
        confidence = "low"
    elif sample_period_s > 0.25 or best.speed_gain_kmh < 5.0:
        confidence = "medium"

    if best.throttle_dominant:
        warnings.append("Powered-flight-like data detected; launch interpretation is provisional.")
    if best.alt_gain_m < 5.0:
        warnings.append("Detected event has limited altitude gain and may not be a launch.")
    if best.onset_activity < 0.4:
        warnings.append("No clear launch onset found in accel/gyro activity.")
    if not best.clear_apex:
        warnings.append("No clear apex inside the best candidate window; using window end.")
    if confidence == "low":
        warnings.append("Low-confidence launch detection.")

    end_idx = best.apex_idx if best.clear_apex else best.end_idx

    return DetectionResult(
        method="auto_v1",
        confidence=confidence,
        start_idx=best.start_idx,
        end_idx=end_idx,
        start_time_s=samples[best.start_idx].t_s,
        end_time_s=samples[end_idx].t_s,
        sample_period_s=sample_period_s,
        warnings=warnings,
    )
