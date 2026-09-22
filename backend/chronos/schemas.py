from typing import Literal, Union, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import Annotated

# 7.1 Inbound Events
class BaseEvent(BaseModel):
    event_id: str
    session_id: str
    t_virtual: float

class TextChunkEvent(BaseEvent):
    kind: Literal["text_chunk"]
    text: str
    is_end_of_turn: bool
    partial: bool = True
    asr_confidence: Optional[float] = None
    origin: Literal["direct_text", "asr"] = "direct_text"

class AudioClipEvent(BaseEvent):
    kind: Literal["audio_clip"]
    audio_ref: str
    duration_ms: int
    sample_rate: int
    encoding: Literal["pcm16", "wav"]

class VisualFrameEvent(BaseEvent):
    kind: Literal["visual_frame"]
    frame_ref: str
    width: int
    height: int
    capture_t_virtual: float

class InterruptSignalEvent(BaseEvent):
    kind: Literal["interrupt"]
    reason: Literal["barge_in", "explicit_cancel", "external"]
    target_call_id: Optional[str] = None

class ToolResultEvent(BaseEvent):
    kind: Literal["tool_result"]
    call_id: str
    idem_key: str
    epoch_origin: int
    status: Literal["success", "error", "timeout"]
    payload: dict

class ToolSpec(BaseModel):
    name: str
    mutating: bool
    args_schema: dict
    cancellable: bool = True
    expected_latency_ms: Optional[int] = None

class ToolManifestEvent(BaseEvent):
    kind: Literal["tool_manifest"]
    tools: List[ToolSpec]

InboundEvent = Annotated[
    Union[TextChunkEvent, AudioClipEvent, VisualFrameEvent,
          InterruptSignalEvent, ToolResultEvent, ToolManifestEvent],
    Field(discriminator="kind")
]

# 7.2 Outbound Actions
class BaseAction(BaseModel):
    action_id: str
    session_id: str
    epoch: int
    t_virtual: float

class SpokenAction(BaseAction):
    kind: Literal["spoken"]
    utterance_class: Literal["ack", "filler", "progress", "clarify"]
    text: str
    floor_token: str
    supersedes: Optional[str] = None

class ToolCallAction(BaseAction):
    kind: Literal["tool_call"]
    call_id: str
    tool_name: str
    args: dict
    idem_key: str
    mutating: bool
    speculative: bool = False

class CancellationAction(BaseAction):
    kind: Literal["cancellation"]
    target_call_id: str
    reason: Literal["epoch_superseded", "explicit_interrupt", "wall_clock_terminal"]

class ClarificationAction(BaseAction):
    kind: Literal["clarification"]
    slot: str
    question: str
    candidates: Optional[List[str]] = None

class SlotValue(BaseModel):
    value: Any
    confidence: float
    modality: Literal["text", "audio", "visual", "corroborated"]
    t_virtual: float
    source_event_id: str

class StateSnapshot(BaseModel):
    snapshot_id: str
    epoch: int
    parent_id: Optional[str]
    intent: Optional[str]
    intent_status: Literal["forming", "stable", "confirmed", "abandoned"]
    slots: Dict[str, SlotValue]
    changed_slots: List[str]
    t_virtual: float

class FinalResponseAction(BaseAction):
    kind: Literal["final_response"]
    text: str
    snapshot: StateSnapshot
    status: Literal["completed", "degraded", "uncertain"]

OutboundAction = Annotated[
    Union[SpokenAction, ToolCallAction, CancellationAction,
          ClarificationAction, FinalResponseAction],
    Field(discriminator="kind")
]

# 7.3 Internal Records
class EffectRecord(BaseModel):
    idem_key: str
    call_id: str
    epoch: int
    status: Literal["pending", "committed", "poisoned", "abandoned"]
    tool_name: str
    args_hash: str
    created_t_virtual: float
    committed_t_virtual: Optional[float] = None

class BeliefDelta(BaseModel):
    kind: Literal["epoch_bump", "silent_refine", "disfluency", "noop"]
    affected_slots: List[str]
    new_intent: Optional[str]
    confidence: float
    evidence_event_id: str
