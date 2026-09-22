import pytest
from chronos.belief.fusion import resolve_contradiction, THETA_LOW, THETA_HIGH
from chronos.schemas import SlotValue
from chronos.belief.tier1 import filter_lexical, check_hard_override, TextChunkEvent

def test_resolve_contradiction_first_write():
    incoming = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    delta = resolve_contradiction(None, incoming, "serial", [])
    assert delta.kind == "silent_refine"
    assert delta.affected_slots == ["serial"]

def test_resolve_contradiction_visual_outranks_audio_identity():
    # visual > audio for 'serial'
    existing = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    incoming = SlotValue(value="B", confidence=0.8, modality="visual", t_virtual=2.0, source_event_id="e2")
    delta = resolve_contradiction(existing, incoming, "serial", [])
    assert delta.kind == "silent_refine" # outranks -> silent refine

def test_resolve_contradiction_audio_outranks_visual_intent():
    # audio > visual for 'intent'
    existing = SlotValue(value="A", confidence=0.9, modality="visual", t_virtual=1.0, source_event_id="e1")
    incoming = SlotValue(value="B", confidence=0.8, modality="audio", t_virtual=2.0, source_event_id="e2")
    delta = resolve_contradiction(existing, incoming, "intent", [])
    assert delta.kind == "silent_refine"

def test_resolve_contradiction_gap_less_than_theta_low():
    # gap < THETA_LOW -> silent refine
    existing = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    incoming = SlotValue(value="B", confidence=0.8, modality="visual", t_virtual=2.0, source_event_id="e2")
    # 'intent' has audio > visual, so incoming (visual) does NOT outrank.
    # gap is 0.1 < THETA_LOW (0.2)
    delta = resolve_contradiction(existing, incoming, "intent", [])
    assert delta.kind == "silent_refine"

def test_resolve_contradiction_gap_less_than_theta_high():
    # gap < THETA_HIGH -> narrate=True -> silent_refine (in our simplified delta schema)
    existing = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    incoming = SlotValue(value="B", confidence=0.5, modality="visual", t_virtual=2.0, source_event_id="e2")
    # gap is 0.4. Not < THETA_LOW. Not outranking. But < THETA_HIGH (0.8).
    delta = resolve_contradiction(existing, incoming, "intent", [])
    assert delta.kind == "silent_refine"

def test_resolve_contradiction_hard_override():
    # Invariant 5: If slot is in in_flight_slots, force epoch bump
    existing = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    # gap is 0.9 (>= 0.8), so it reaches the in-flight check
    incoming = SlotValue(value="B", confidence=0.0, modality="visual", t_virtual=2.0, source_event_id="e2")
    
    delta = resolve_contradiction(existing, incoming, "intent", ["intent"])
    assert delta.kind == "epoch_bump"
    
def test_resolve_contradiction_unmapped_recency():
    existing = SlotValue(value="A", confidence=0.9, modality="audio", t_virtual=1.0, source_event_id="e1")
    # T_virtual is greater, so it outranks via recency
    incoming = SlotValue(value="B", confidence=0.0, modality="audio", t_virtual=2.0, source_event_id="e2")
    delta = resolve_contradiction(existing, incoming, "unknown_slot", [])
    assert delta.kind == "silent_refine"

def test_tier1_lexical_filter():
    assert filter_lexical(TextChunkEvent(event_id="1", session_id="1", t_virtual=0, kind="text_chunk", text="actually no", is_end_of_turn=True)) == "correction"
    assert filter_lexical(TextChunkEvent(event_id="2", session_id="1", t_virtual=0, kind="text_chunk", text="stop what you are doing", is_end_of_turn=True)) == "cancel"
    assert filter_lexical(TextChunkEvent(event_id="3", session_id="1", t_virtual=0, kind="text_chunk", text="um I think so", is_end_of_turn=True)) == "disfluency"
    assert filter_lexical(TextChunkEvent(event_id="4", session_id="1", t_virtual=0, kind="text_chunk", text="yes that's right", is_end_of_turn=True)) == "clear"

def test_tier1_hard_override():
    assert check_hard_override("slot_a", ["slot_a", "slot_b"]) == True
    assert check_hard_override("slot_c", ["slot_a", "slot_b"]) == False
