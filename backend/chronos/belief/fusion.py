from chronos.schemas import SlotValue, BeliefDelta
from typing import Optional, List

THETA_LOW = 0.2
THETA_HIGH = 0.8

# Priority Table: lower index means lower priority, higher index means higher priority
PRIORITY_TABLE = {
    # visual > audio
    "model_number": ["audio", "visual"],
    "serial": ["audio", "visual"],
    "screen_state": ["audio", "visual"],
    "flight_code": ["audio", "visual"],
    
    # audio > visual
    "intent": ["visual", "audio"],
    "quantity": ["visual", "audio"]
}

def resolve_contradiction(
    existing: Optional[SlotValue], 
    incoming: SlotValue, 
    slot_type: str, 
    in_flight_slots: List[str]
) -> BeliefDelta:
    """
    Implements the deterministic contradiction policy.
    """
    if existing is None:
        return BeliefDelta(
            kind="silent_refine",
            affected_slots=[slot_type],
            new_intent=None,
            confidence=incoming.confidence,
            evidence_event_id=incoming.source_event_id
        )

    is_unmapped = slot_type not in PRIORITY_TABLE
    table = PRIORITY_TABLE.get(slot_type, [])
    
    if is_unmapped:
        outranks = incoming.t_virtual > existing.t_virtual
    else:
        try:
            incoming_rank = table.index(incoming.modality)
        except ValueError:
            incoming_rank = -1
            
        try:
            existing_rank = table.index(existing.modality)
        except ValueError:
            existing_rank = -1
            
        outranks = incoming_rank > existing_rank
        
    gap = abs(incoming.confidence - existing.confidence)

    if outranks or gap < THETA_LOW:
        return BeliefDelta(
            kind="silent_refine",
            affected_slots=[slot_type],
            new_intent=None,
            confidence=incoming.confidence,
            evidence_event_id=incoming.source_event_id
        )
        
    if gap < THETA_HIGH:
        return BeliefDelta(
            kind="silent_refine",
            affected_slots=[slot_type],
            new_intent=None,
            confidence=incoming.confidence,
            evidence_event_id=incoming.source_event_id
        )
        
    if slot_type in in_flight_slots:
        return BeliefDelta(
            kind="epoch_bump",
            affected_slots=[slot_type],
            new_intent=None,
            confidence=incoming.confidence,
            evidence_event_id=incoming.source_event_id
        )
        
    return BeliefDelta(
        kind="silent_refine",
        affected_slots=[slot_type],
        new_intent=None,
        confidence=incoming.confidence,
        evidence_event_id=incoming.source_event_id
    )
