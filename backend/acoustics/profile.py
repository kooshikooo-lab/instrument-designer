"""Stepped bore profile representation."""
from __future__ import annotations

from typing import List, Optional


class Profile:
    """
    A stepped bore profile: arrays of (position, low_diameter, high_diameter).
    low = diameter at bottom of segment, high = diameter at top of segment.
    For cylindrical bores, low == high at each position.
    """

    def __init__(self, pos: List[float], low: List[float], high: Optional[List[float]] = None):
        self.pos = list(pos)
        self.low = list(low)
        self.high = list(high) if high is not None else list(low)

    def at(self, location: float, use_high: bool = False) -> float:
        """Interpolate diameter at a given position along the bore."""
        if location <= self.pos[0]:
            return self.low[0]
        if location >= self.pos[-1]:
            return self.high[-1]
        lo, hi = 0, len(self.pos) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.pos[mid] <= location:
                lo = mid
            else:
                hi = mid
        t = (location - self.pos[lo]) / (self.pos[hi] - self.pos[lo])
        return (1.0 - t) * self.high[lo] + t * self.low[hi]

    def as_stepped(self, max_step: float) -> 'Profile':
        """
        Create a smooth stepped version of the profile.
        Replaces hard diameter changes with a sequence of smaller steps.
        """
        new_pos = []
        for i in range(len(self.pos) - 1):
            new_pos.append(self.pos[i])
            lower_top_pos = self.pos[i]
            lower_top_diam = self.high[i]
            higher_bot_pos = self.pos[i + 1]
            higher_bot_diam = self.low[i + 1]
            n_steps = int(abs(higher_bot_diam - lower_top_diam) / max_step) + 1
            if n_steps <= 1:
                continue
            for s in range(1, n_steps):
                frac = s / n_steps
                new_pos.append((higher_bot_pos - lower_top_pos) * frac + lower_top_pos)
        new_pos.append(self.pos[-1])

        new_diams = []
        for i in range(len(new_pos) - 1):
            mid = 0.5 * (new_pos[i] + new_pos[i + 1])
            new_diams.append(self.at(mid, use_high=False))
        new_low = [new_diams[0]] + new_diams
        new_high = new_diams + [new_diams[-1]]
        return Profile(new_pos, new_low, new_high)