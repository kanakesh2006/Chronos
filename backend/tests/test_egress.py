import pytest
from chronos.egress import EgressSerializer
from chronos.schemas import SpokenAction

def test_egress_serializer_valid():
    serializer = EgressSerializer(session_id="s1")
    action = SpokenAction(
        action_id="a1",
        session_id="s1",
        epoch=0,
        t_virtual=0.0,
        kind="spoken",
        utterance_class="ack",
        text="test",
        floor_token="ft-1"
    )
    
    result = serializer.serialize(action)
    assert result["action_id"] == "a1"
    assert result["kind"] == "spoken"

def test_egress_serializer_repair():
    serializer = EgressSerializer(session_id="s2")
    
    bad_payload = {
        "action_id": "a2",
        "epoch": 0,
        "kind": "spoken",
        "utterance_class": "ack",
        "text": "test",
        "floor_token": "ft-2"
    }
    
    result = serializer.serialize(bad_payload)
    assert result["session_id"] == "s2"
    assert result["t_virtual"] == 0.0
    assert result["kind"] == "spoken"

def test_egress_serializer_degrade():
    serializer = EgressSerializer(session_id="s3")
    
    bad_payload = {
        "action_id": "a3",
        "epoch": 0,
        "kind": "spoken",
        "utterance_class": "ack"
    }
    
    result = serializer.serialize(bad_payload)
    assert result["kind"] == "final_response"
    assert result["status"] == "degraded"
