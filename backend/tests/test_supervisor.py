import pytest
import asyncio
from unittest.mock import patch, MagicMock
from chronos.supervisor import ClockSupervisor
from chronos.effects import EffectGateway

def test_clock_supervisor_tiers():
    with patch("time.monotonic") as mock_monotonic:
        # Start time is read in __init__, then read again in wall_fraction
        
        # full
        mock_monotonic.side_effect = [0.0, 10.0]
        supervisor = ClockSupervisor(wall_budget_s=100.0)
        assert supervisor.tier() == "full"
        
        # throttled (0.5 to 0.75)
        mock_monotonic.side_effect = [0.0, 60.0]
        supervisor = ClockSupervisor(wall_budget_s=100.0)
        assert supervisor.tier() == "throttled"
        
        # degraded (0.75 to 0.9)
        mock_monotonic.side_effect = [0.0, 80.0]
        supervisor = ClockSupervisor(wall_budget_s=100.0)
        assert supervisor.tier() == "degraded"
        
        # terminal (>0.9)
        mock_monotonic.side_effect = [0.0, 95.0]
        supervisor = ClockSupervisor(wall_budget_s=100.0)
        assert supervisor.tier() == "terminal"


from chronos.schemas import StateSnapshot

@pytest.mark.asyncio
async def test_clock_supervisor_terminal_fallback():
    supervisor = ClockSupervisor()
    mock_gateway = MagicMock(spec=EffectGateway)
    
    snapshot = StateSnapshot(
        snapshot_id="head_123",
        epoch=5,
        parent_id=None,
        intent="book_flight",
        intent_status="stable",
        slots={},
        changed_slots=[],
        t_virtual=12.0
    )
    
    response = await supervisor.invoke_terminal_fallback(snapshot, mock_gateway)
    
    assert response.status == "degraded"
    assert response.snapshot.snapshot_id == "head_123"
    assert "terminal time budget" in response.text.lower()
    
    # Assert gateway cancel sweep was triggered to poison all pending tasks
    mock_gateway.cancel_sweep.assert_called_once_with(float('inf'))
