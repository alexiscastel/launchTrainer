from __future__ import annotations

import unittest

from launchtrainer.signals import centered_moving_average, climb_rates


class SignalTests(unittest.TestCase):
    def test_centered_moving_average_uses_neighboring_samples(self) -> None:
        self.assertEqual(
            centered_moving_average([1.0, 2.0, 4.0, 8.0], window=3),
            [1.5, 7.0 / 3.0, 14.0 / 3.0, 6.0],
        )

    def test_climb_rates_returns_positive_derivatives(self) -> None:
        rates = climb_rates([0.0, 0.5, 1.0], [100.0, 101.0, 103.0])
        self.assertEqual(rates, [0.0, 2.0, 4.0])
