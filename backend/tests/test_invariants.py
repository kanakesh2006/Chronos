import pytest
import asyncio
from hypothesis import given, settings, strategies as st
from chronos.schemas import ToolCallAction, BeliefDelta
from chronos.effects import EffectGateway
from chronos.epoch import EpochArbiter
from typing import Dict, List

class MockClock:
    def __init__(self):
        self._time = 0.0
    def __call__(self):
        return self._time
    def advance(self, amount: float):
        self._time += amount

@pytest.fixture
def mock_clock():
    return MockClock()

@pytest.fixture
def effect_gateway(mock_clock):
    return EffectGateway(clock_source=mock_clock)

@pytest.fixture
def epoch_arbiter(effect_gateway):
    return EpochArbiter(effect_gateway=effect_gateway)

@pytest.mark.asyncio
async def test_invariant_1_no_commit_on_mismatch(mock_clock, effect_gateway):
    call = ToolCallAction(
        action_id="a1", session_id="s1", epoch=0, t_virtual=mock_clock(),
        kind="tool_call", call_id="c1", tool_name="dummy", args={"a": 1},
        idem_key="k1", mutating=True, speculative=False
    )
    
    current_epoch = [0]
    
    async def invoke_fn(c):
        await asyncio.sleep(0.01)
        current_epoch[0] = 1 # Simulate bump
        return "done"

    result = await effect_gateway.dispatch_effect(call, 0, invoke_fn, lambda: current_epoch[0])
    assert result is None
    assert effect_gateway.registry["k1"].status == "abandoned"

@pytest.mark.asyncio
async def test_invariant_6_poisoning_on_cancel(mock_clock, epoch_arbiter):
    call = ToolCallAction(
        action_id="a1", session_id="s1", epoch=0, t_virtual=mock_clock(),
        kind="tool_call", call_id="c1", tool_name="dummy", args={},
        idem_key="k1", mutating=True, speculative=False
    )
    
    async def invoke_fn(c):
        await asyncio.sleep(0.05)
        return "done"

    task = asyncio.create_task(
        epoch_arbiter.effect_gateway.dispatch_effect(call, 0, invoke_fn, lambda: epoch_arbiter.current_epoch)
    )
    
    await asyncio.sleep(0.01)
    epoch_arbiter.force_epoch_bump()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert epoch_arbiter.effect_gateway.registry["k1"].status == "poisoned"

@pytest.mark.asyncio
@given(
    interrupt_tick=st.floats(min_value=0.001, max_value=0.04),
    sleep_tick=st.floats(min_value=0.01, max_value=0.05)
)
@settings(max_examples=50)
async def test_randomized_interruption(interrupt_tick, sleep_tick):
    """
    Property test: randomized interruption timing never results in a committed state if epoch < session_epoch.
    """
    clock = MockClock()
    gateway = EffectGateway(clock_source=clock)
    arbiter = EpochArbiter(effect_gateway=gateway)
    
    call = ToolCallAction(
        action_id="a1", session_id="s1", epoch=0, t_virtual=clock(),
        kind="tool_call", call_id="c1", tool_name="dummy", args={},
        idem_key="k1", mutating=True, speculative=False
    )
    
    async def invoke_fn(c):
        await asyncio.sleep(sleep_tick)
        return "done"
        
    task = asyncio.create_task(
        gateway.dispatch_effect(call, 0, invoke_fn, lambda: arbiter.current_epoch)
    )
    
    await asyncio.sleep(interrupt_tick)
    arbiter.force_epoch_bump()
    
    try:
        await task
    except asyncio.CancelledError:
        pass
        
    rec = gateway.registry["k1"]
    
    if interrupt_tick < sleep_tick:
        # The interruption happened before the tool could finish
        assert rec.status in ("poisoned", "abandoned")
    elif interrupt_tick >= sleep_tick:
        # The tool finished before the interruption. It might be committed or abandoned 
        # depending on exact event loop scheduling.
        assert rec.status in ("committed", "abandoned", "poisoned")
