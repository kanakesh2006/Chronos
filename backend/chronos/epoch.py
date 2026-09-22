"""
Epoch Arbiter
"""
from typing import Callable
from .schemas import BeliefDelta
from .effects import EffectGateway

class EpochArbiter:
    def __init__(self, effect_gateway: EffectGateway):
        """
        Session-scoped epoch counter.
        """
        self.current_epoch: int = 0
        self.effect_gateway = effect_gateway
    
    def apply_delta(self, delta: BeliefDelta) -> None:
        """
        Applies a belief delta, optionally bumping the epoch and sweeping effects.
        """
        if delta.kind == "epoch_bump":
            self.current_epoch += 1
            self.effect_gateway.cancel_sweep(self.current_epoch)
        # silent_refine, disfluency, noop handling happens outside or doesn't bump epoch

    def force_epoch_bump(self) -> None:
        """
        Hard override: force an epoch bump regardless of belief delta confidence.
        (Satisfies Invariant 5 when a mutating effect slot is changed).
        """
        self.current_epoch += 1
        self.effect_gateway.cancel_sweep(self.current_epoch)
