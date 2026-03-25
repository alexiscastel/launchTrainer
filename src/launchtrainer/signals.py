from __future__ import annotations

from statistics import median

from .parser import Sample


def centered_moving_average(values: list[float], window: int = 3) -> list[float]:
    if not values:
        return []

    radius = window // 2
    smoothed: list[float] = []

    for index in range(len(values)):
        start = max(0, index - radius)
        end = min(len(values), index + radius + 1)
        segment = values[start:end]
        smoothed.append(sum(segment) / len(segment))

    return smoothed


def estimate_sample_period(samples: list[Sample]) -> float:
    if len(samples) < 2:
        return 0.0

    deltas = [
        samples[index].t_s - samples[index - 1].t_s
        for index in range(1, len(samples))
        if samples[index].t_s > samples[index - 1].t_s
    ]
    if not deltas:
        return 0.0
    return median(deltas)


def climb_rates(times_s: list[float], altitudes_m: list[float]) -> list[float]:
    if not times_s or not altitudes_m:
        return []

    rates = [0.0]
    for index in range(1, len(times_s)):
        dt = times_s[index] - times_s[index - 1]
        if dt <= 0:
            rates.append(rates[-1])
            continue
        rates.append((altitudes_m[index] - altitudes_m[index - 1]) / dt)
    return rates
