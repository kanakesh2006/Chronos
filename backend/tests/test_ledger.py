import pytest
from chronos.ledger import SnapshotLedger
from chronos.schemas import StateSnapshot, SlotValue
from chronos.clock import VirtualClock

def test_ledger_refine_and_lineage():
    clock = VirtualClock()
    ledger = SnapshotLedger(clock)
    
    # Create an initial empty snapshot
    root_snap = StateSnapshot(
        snapshot_id="root",
        epoch=0,
        parent_id=None,
        intent=None,
        intent_status="forming",
        slots={},
        changed_slots=[],
        t_virtual=clock.now()
    )
    ledger.ledger[root_snap.snapshot_id] = root_snap
    
    # Refine
    val1 = SlotValue(value="BOS", confidence=0.9, modality="text", t_virtual=clock.now(), source_event_id="e1")
    snap1 = ledger.refine(root_snap, "origin", val1)
    
    assert snap1.parent_id == "root"
    assert snap1.slots["origin"].value == "BOS"
    assert "origin" in snap1.changed_slots
    
    # Refine again
    val2 = SlotValue(value="LHR", confidence=0.95, modality="audio", t_virtual=clock.now(), source_event_id="e2")
    snap2 = ledger.refine(snap1, "destination", val2)
    
    # Check lineage
    lineage = ledger.lineage(snap2.snapshot_id)
    assert len(lineage) == 3
    assert lineage[0].snapshot_id == "root"
    assert lineage[1].snapshot_id == snap1.snapshot_id
    assert lineage[2].snapshot_id == snap2.snapshot_id

    # The slots should inherit
    assert "origin" in snap2.slots
    assert snap2.slots["origin"].value == "BOS"
    assert "destination" in snap2.slots
    assert snap2.slots["destination"].value == "LHR"
