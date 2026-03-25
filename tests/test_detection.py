from __future__ import annotations

import unittest

from launchtrainer.detection import detect_launch
from launchtrainer.parser import Sample
from launchtrainer.signals import centered_moving_average, estimate_sample_period


def make_sample(
    t_s: float,
    alt_m: float,
    speed_kmh: float,
    throttle_pct: float,
    accel_mag_g: float,
    gyro_mag_dps: float,
) -> Sample:
    return Sample(
        row_number=int(t_s * 10) + 2,
        time_label=f"00:00:{t_s:06.3f}",
        t_s=t_s,
        alt_m=alt_m,
        speed_kmh=speed_kmh,
        throttle_pct=throttle_pct,
        accel_mag_g=accel_mag_g,
        gyro_mag_dps=gyro_mag_dps,
        flight_mode="Launch",
    )


class DetectionTests(unittest.TestCase):
    def test_detection_is_deterministic_for_same_samples(self) -> None:
        samples = [
            make_sample(0.0, 100.0, 10.0, 0.0, 1.0, 10.0),
            make_sample(0.1, 101.0, 15.0, 0.0, 2.2, 85.0),
            make_sample(0.2, 103.5, 22.0, 0.0, 2.0, 90.0),
            make_sample(0.3, 107.0, 24.0, 0.0, 1.6, 70.0),
            make_sample(0.4, 110.0, 20.0, 0.0, 1.2, 35.0),
            make_sample(0.5, 112.0, 16.0, 0.0, 1.1, 25.0),
            make_sample(0.6, 111.0, 12.0, 0.0, 1.0, 18.0),
            make_sample(0.7, 109.0, 10.0, 0.0, 1.0, 12.0),
            make_sample(0.8, 108.0, 9.0, 0.0, 1.0, 8.0),
        ]
        smoothed = centered_moving_average([sample.alt_m for sample in samples], window=3)
        sample_period_s = estimate_sample_period(samples)

        first = detect_launch(samples, smoothed, sample_period_s)
        second = detect_launch(samples, smoothed, sample_period_s)

        self.assertEqual(first, second)
        self.assertIn(first.confidence, {"high", "medium", "low"})
        self.assertLessEqual(first.start_idx, first.end_idx)

    def test_detection_warns_on_powered_like_data(self) -> None:
        samples = [
            make_sample(0.0, 100.0, 0.0, 70.0, 1.1, 5.0),
            make_sample(0.5, 101.0, 10.0, 75.0, 1.4, 30.0),
            make_sample(1.0, 103.0, 18.0, 80.0, 1.7, 55.0),
            make_sample(1.5, 105.0, 20.0, 78.0, 1.3, 25.0),
            make_sample(2.0, 106.0, 18.0, 72.0, 1.2, 18.0),
        ]
        smoothed = centered_moving_average([sample.alt_m for sample in samples], window=3)
        sample_period_s = estimate_sample_period(samples)

        result = detect_launch(samples, smoothed, sample_period_s)

        self.assertEqual(result.confidence, "low")
        self.assertTrue(any("Powered-flight-like" in warning for warning in result.warnings))
