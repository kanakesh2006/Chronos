import pytest
import asyncio
from typing import Optional
from chronos.schemas import TextChunkEvent, VisualFrameEvent, SlotValue
from chronos.epoch import EpochArbiter
from chronos.effects import EffectGateway
from chronos.ledger import SnapshotLedger
from chronos.clock import VirtualClock
from chronos.belief.tier1 import filter_lexical, check_hard_override
from chronos.belief.fusion import resolve_contradiction
from chronos.schemas import ToolCallAction

class MockGateway:
    """Mock for Effect Gateway for this specific integration test"""
    def __init__(self):
        self.registry = {}
        self.poisoned = set()
        
    def cancel_sweep(self, current_epoch: int):
        for key, rec in list(self.registry.items()):
            if rec['epoch'] < current_epoch and rec['status'] == 'pending':
                rec['status'] = 'poisoned'
                self.poisoned.add(key)
                
    def dispatch(self, idem_key: str, epoch: int):
        self.registry[idem_key] = {'epoch': epoch, 'status': 'pending'}
        
    def commit(self, idem_key: str, current_epoch: int):
        rec = self.registry.get(idem_key)
        if rec and rec['status'] == 'poisoned':
            return False # Discarded
        if rec and rec['epoch'] == current_epoch:
            rec['status'] = 'committed'
            return True
        return False

@pytest.mark.asyncio
async def test_adversarial_trace_scenario_16():
    """
    Reproduces the adversarial trace described in Spec §16.
    """
    gateway = MockGateway()
    epoch_arbiter = EpochArbiter(effect_gateway=gateway)
    
    # 0.0s: Intent forms
    epoch_arbiter.force_epoch_bump()
    epoch = epoch_arbiter.current_epoch
    assert epoch == 1
    
    # 0.3s: Dispatch search_flights (read-only)
    gateway.dispatch("key1", epoch)
    
    # 0.6s: Result success
    assert gateway.commit("key1", epoch_arbiter.current_epoch) == True
    
    # 0.9s: Dispatch book_flight (mutating, dest=Chennai)
    gateway.dispatch("key2", epoch)
    in_flight_slots = ["destination"]
    
    # 1.2s: Audio interrupt, 1.35s ASR completes -> correction
    # "no wait — actually Bangalore, not Chennai"
    text = "no wait — actually Bangalore, not Chennai"
    lexical_signal = "correction" # mock filter_lexical output
    
    # check hard override
    # It corrects 'destination' which is in flight
    override = check_hard_override("destination", in_flight_slots)
    assert override == True
    
    # Hard override triggers epoch bump immediately
    epoch_arbiter.force_epoch_bump()
    new_epoch = epoch_arbiter.current_epoch
    assert new_epoch == 2
    
    # Cancel sweep
    # (already triggered by force_epoch_bump internally, but let's assert)
    assert "key2" in gateway.poisoned
    
    # 1.6s: Stale result for key2 arrives
    # Mock tool internal completion, tries to commit
    assert gateway.commit("key2", new_epoch) == False # Poisoned result discarded
    
    # 1.8s: Planner re-plans
    gateway.dispatch("key4", new_epoch)
    
    # 2.0s: Visual frame "6E-204"
    # 2.15s: OCR resolves
    visual_obs = SlotValue(value="6E-204", confidence=0.91, modality="visual", t_virtual=2.15, source_event_id="v1")
    delta1 = resolve_contradiction(None, visual_obs, "flight_id", [])
    assert delta1.kind == "silent_refine"
    
    # 2.3s: search_flights returns
    assert gateway.commit("key4", epoch_arbiter.current_epoch) == True
    
    # Mock search flight matching buffered visual obs
    audio_corroboration = SlotValue(value="6E-204", confidence=0.97, modality="audio", t_virtual=2.3, source_event_id="a1")
    delta2 = resolve_contradiction(visual_obs, audio_corroboration, "flight_id", [])
    assert delta2.kind == "silent_refine"
    
    # 2.6s: Dispatch book_flight (dest=Bangalore, flight=6E-204)
    gateway.dispatch("key5", new_epoch)
    
    # 4.6s: Result success
    assert gateway.commit("key5", epoch_arbiter.current_epoch) == True
    
    # Trace successfully reproduced without double booking!
