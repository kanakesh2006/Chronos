"""
Versioned Snapshot Ledger
"""
import uuid
from typing import Dict, List
from .schemas import StateSnapshot, SlotValue
from .clock import VirtualClock

class SnapshotLedger:
    def __init__(self, clock: VirtualClock):
        """
        Session-scoped append-only ledger.
        """
        self.ledger: Dict[str, StateSnapshot] = {}
        self.head_by_epoch: Dict[int, str] = {}
        self.clock = clock

    def refine(self, parent: StateSnapshot, slot: str, new_val: SlotValue) -> StateSnapshot:
        """
        Appends a new snapshot referencing the parent, creating a causal DAG.
        """
        new_slots = {**parent.slots, slot: new_val}
        new_id = str(uuid.uuid4())
        
        snap = StateSnapshot(
            snapshot_id=new_id, 
            epoch=parent.epoch, 
            parent_id=parent.snapshot_id,
            intent=parent.intent, 
            intent_status=parent.intent_status,
            slots=new_slots, 
            changed_slots=[slot], 
            t_virtual=self.clock.now()
        )
        self.ledger[snap.snapshot_id] = snap
        self.head_by_epoch[parent.epoch] = snap.snapshot_id
        return snap

    def lineage(self, snapshot_id: str) -> List[StateSnapshot]:
        """
        Walks the parent pointers to reconstruct the history of a given snapshot branch.
        """
        out = []
        cur = snapshot_id
        while cur:
            s = self.ledger.get(cur)
            if not s:
                break
            out.append(s)
            cur = s.parent_id
        return list(reversed(out))
