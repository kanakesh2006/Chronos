"""
Virtual Clock Façade & Dual-Clock Supervisor
"""
import time
from typing import Literal

class VirtualClock:
    """
    Virtual time facade to guarantee determinism under replay.
    Never call time.time() directly inside causal logic.
    """
    def __init__(self):
        self._t_virtual: float = 0.0

    def set_time(self, t_virtual: float) -> None:
        self._t_virtual = t_virtual

    def now(self) -> float:
        return self._t_virtual


class ClockSupervisor:
    """
    Tracks real wall-clock time independently of virtual time, with a 50/75/90% degradation ladder.
    """
    def __init__(self, wall_budget_s: float = 120.0):
        self.wall_start: float = time.monotonic()  # real wall clock — never virtual
        self.wall_budget: float = wall_budget_s

    def wall_fraction(self) -> float:
        return (time.monotonic() - self.wall_start) / self.wall_budget

    def tier(self) -> Literal["full", "throttled", "degraded", "terminal"]:
        f = self.wall_fraction()
        if f < 0.50: 
            return "full"
        if f < 0.75: 
            return "throttled"
        if f < 0.90: 
            return "degraded"
        return "terminal"
