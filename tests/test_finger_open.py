"""The renderer opens the throwing fingers by the change the solve made.

The wrist flick opens the fingers at the release. The engine's solve carries
that as `fingerOpenDegrees` in the render job, and the renderer makes the same
change on its own hand by backing every knuckle off the ball by one amount.
`finger_curl.knuckle_release_for` is that search, and it imports without
Blender, so it is tested here against hands made of arithmetic.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from finger_curl import (  # noqa: E402
    OPEN_TOLERANCE_DEGREES,
    FingerOpenError,
    knuckle_release_for,
)


def linear_hand(gain: float):
    """A hand whose angle opens `gain` degrees for each degree backed off."""
    return lambda amount: gain * amount


def curved_hand(amount: float) -> float:
    """Opens quickly at first and then less, as a real finger does."""
    return 30.0 * (1.0 - (1.0 - amount / 60.0) ** 2)


class TheFingersOpenByTheChangeAsked(unittest.TestCase):
    def test_the_hand_opens_as_far_as_asked(self):
        for hand, ceiling in ((linear_hand(0.8), 60.0), (curved_hand, 60.0)):
            for asked in (2.0, 10.0, 24.0):
                amount, gave = knuckle_release_for(hand, asked, ceiling)
                self.assertAlmostEqual(gave, asked, delta=0.01)
                self.assertGreater(amount, 0.0)
                self.assertLessEqual(amount, ceiling)

    def test_a_larger_ask_backs_the_knuckles_off_further(self):
        small, _ = knuckle_release_for(curved_hand, 5.0, 60.0)
        large, _ = knuckle_release_for(curved_hand, 20.0, 60.0)
        self.assertGreater(large, small)

    def test_no_change_asked_moves_no_knuckle(self):
        amount, gave = knuckle_release_for(linear_hand(0.8), 0.0, 60.0)
        self.assertEqual((amount, gave), (0.0, 0.0))

    def test_a_close_past_the_grip_is_refused(self):
        with self.assertRaises(FingerOpenError) as caught:
            knuckle_release_for(linear_hand(0.8), -5.0, 60.0)
        self.assertIn("into the ball", str(caught.exception))

    def test_an_ask_the_hand_cannot_make_is_refused(self):
        """THE REFUSAL THAT KEEPS A LABEL TRUE. A figure that shows less than
        the solve asked is not the candidate its caption names."""
        with self.assertRaises(FingerOpenError) as caught:
            knuckle_release_for(linear_hand(0.5), 40.0, 60.0)
        self.assertIn("opens 30.0", str(caught.exception))

    def test_an_ask_inside_the_tolerance_of_the_most_is_made(self):
        most = 30.0
        amount, gave = knuckle_release_for(
            linear_hand(0.5), most + 0.5 * OPEN_TOLERANCE_DEGREES, 60.0
        )
        self.assertAlmostEqual(gave, most, delta=0.01)
        self.assertAlmostEqual(amount, 60.0, delta=0.01)


if __name__ == "__main__":
    unittest.main()
