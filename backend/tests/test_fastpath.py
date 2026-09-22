import pytest
from chronos.fastpath import FastPathEmitter, FastPathAction
from chronos.schemas import SpokenAction, ClarificationAction, FinalResponseAction, StateSnapshot
from chronos.clock import VirtualClock
from typing import get_args

def test_invariant_3_typing():
    # Invariant 3: The Fast Path is structurally incapable of asserting task completion.
    allowed_types = get_args(FastPathAction)
    assert FinalResponseAction not in allowed_types
    assert SpokenAction in allowed_types
    assert ClarificationAction in allowed_types

def test_fast_path_templates():
    clock = VirtualClock()
    emitter = FastPathEmitter(clock_source=clock, session_id="s1")
    
    snapshot = StateSnapshot(
        snapshot_id="snap1",
        epoch=0,
        parent_id=None,
        intent=None,
        intent_status="forming",
        slots={},
        changed_slots=[],
        t_virtual=clock.now()
    )
    
    ack = emitter.emit_ack(snapshot, "Got it.")
    assert ack.kind == "spoken"
    assert ack.utterance_class == "ack"
    assert ack.floor_token is not None
    
    prev_token = ack.floor_token
    
    filler = emitter.emit_filler(epoch=0)
    assert filler.supersedes == prev_token
    assert filler.floor_token != prev_token
