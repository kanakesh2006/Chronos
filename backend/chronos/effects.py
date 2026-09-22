"""
Two-Phase Effect Gateway & Poisoning Registry
"""
import asyncio
import json
from typing import Dict, Any, Callable, Awaitable
from .schemas import EffectRecord, ToolCallAction


def _normalize_for_canonical(value: Any) -> Any:
    """Normalize values for canonical argument hashing.
    - Keeps bools distinct from ints (True != 1)
    - Converts integral floats to ints (1.0 -> 1)
    - Recursively normalizes dicts and lists
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _normalize_for_canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_for_canonical(v) for v in value]
    return value


def hash_canonical(args: dict) -> str:
    """
    Argument canonicalization is mandatory before hashing into an idempotency key.
    (Invariant 7)
    """
    normalized = _normalize_for_canonical(args)
    return json.dumps(normalized, sort_keys=True, separators=(',', ':'))


class EffectGateway:
    def __init__(self, clock_source: Callable[[], float]):
        """
        Session-scoped registry to guarantee no cross-session leakage.
        """
        self.registry: Dict[str, EffectRecord] = {}
        self.in_flight_tasks: Dict[str, asyncio.Task] = {}
        self.now_v = clock_source

    def cancel_sweep(self, new_epoch: int) -> None:
        """
        Synchronous cancel sweep poisoning every pending registry entry with epoch < new_epoch,
        and cancelling the corresponding asyncio tasks.
        """
        for rec in self.registry.values():
            if rec.status == "pending" and rec.epoch < new_epoch:
                rec.status = "poisoned"  # synchronous — precedes any late COMMIT
                task = self.in_flight_tasks.get(rec.call_id)
                if task and not task.done():
                    task.cancel()

    async def dispatch_effect(self, call: ToolCallAction, epoch: int, invoke_fn: Callable[[ToolCallAction], Awaitable[Any]], current_epoch_fn: Callable[[], int]) -> Any:
        """
        Two-phase commit for tool invocation.
        """
        rec = self.registry.get(call.idem_key)
        if rec and rec.status in ("pending", "committed"):
            return None  # dedup, no dispatch
            
        self.registry[call.idem_key] = EffectRecord(
            idem_key=call.idem_key, 
            call_id=call.call_id, 
            epoch=epoch,
            status="pending", 
            tool_name=call.tool_name,
            args_hash=hash_canonical(call.args), 
            created_t_virtual=self.now_v(),
        )
        
        try:
            self.in_flight_tasks[call.call_id] = asyncio.current_task()
            result = await invoke_fn(call)  # cancellable
        except asyncio.CancelledError:
            self.registry[call.idem_key].status = "poisoned"
            raise  # never swallow (Invariant 6)
        finally:
            self.in_flight_tasks.pop(call.call_id, None)
            
        rec = self.registry[call.idem_key]
        if rec.epoch != current_epoch_fn():  # post-return check
            rec.status = "abandoned"
            return None
            
        rec.status = "committed"
        rec.committed_t_virtual = self.now_v()
        return result