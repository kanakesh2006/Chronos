import time
import asyncio
from typing import Literal
import structlog
from chronos.schemas import FinalResponseAction

logger = structlog.get_logger(__name__)

class ClockSupervisor:
    def __init__(self, wall_budget_s: float = 120.0):
        self.wall_start = time.monotonic()  # real wall clock — never virtual
        self.wall_budget = wall_budget_s

    def wall_fraction(self) -> float:
        return (time.monotonic() - self.wall_start) / self.wall_budget

    def tier(self) -> Literal["full", "throttled", "degraded", "terminal"]:
        f = self.wall_fraction()
        if f < 0.50: return "full"
        if f < 0.75: return "throttled"
        if f < 0.90: return "degraded"
        return "terminal"
        
    async def invoke_terminal_fallback(self, snapshot, effect_gateway) -> FinalResponseAction:
        """
        The terminal fallback path. Independently tested as the emergency exit.
        Poisons all in-flight tasks and serializes the ledger head into a degraded response.
        Wrapped in an asyncio.timeout.
        """
        async def _terminal_routine():
            # Poison all pending effects. We just pass an infinitely large epoch to poison everything.
            effect_gateway.cancel_sweep(float('inf'))
            
            return FinalResponseAction(
                action_id="terminal_fallback_1",
                session_id="session_terminal",
                epoch=snapshot.epoch,
                t_virtual=snapshot.t_virtual,
                kind="final_response",
                text="System reached terminal time budget.",
                snapshot=snapshot,
                status="degraded"
            )
            
        try:
            # Enforce strict 1-second timeout for the terminal fallback itself
            async with asyncio.timeout(1.0):
                return await _terminal_routine()
        except asyncio.TimeoutError:
            logger.error("terminal_fallback_timeout")
            # If even the fallback hangs, force an absolute bare minimum response
            return FinalResponseAction(
                action_id="terminal_fallback_timeout",
                session_id="session_terminal",
                epoch=snapshot.epoch,
                t_virtual=snapshot.t_virtual,
                kind="final_response",
                text="Terminal fallback timeout.",
                snapshot=snapshot,
                status="degraded"
            )
