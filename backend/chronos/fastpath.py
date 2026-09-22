import uuid
from typing import Union, Optional, List
from chronos.schemas import SpokenAction, ClarificationAction, StateSnapshot
from chronos.clock import VirtualClock

# Return type enforces Invariant 3: Fast Path cannot assert task completion
FastPathAction = Union[SpokenAction, ClarificationAction]

class FastPathEmitter:
    def __init__(self, clock_source: VirtualClock, session_id: str):
        self.clock = clock_source
        self.session_id = session_id
        self.last_floor_token: Optional[str] = None
        self._action_counter = 0

    def _generate_id(self, prefix: str) -> str:
        self._action_counter += 1
        return f"{prefix}-{self._action_counter}-{uuid.uuid4().hex[:8]}"

    def _generate_floor_token(self) -> str:
        # Monotonic floor token based on virtual time and counter
        token = f"ft-{self.clock.now()}-{self._action_counter}"
        self.last_floor_token = token
        return token

    def emit_ack(self, snapshot: StateSnapshot, text: str = "Got it.") -> SpokenAction:
        supersedes = self.last_floor_token
        return SpokenAction(
            action_id=self._generate_id("ack"),
            session_id=self.session_id,
            epoch=snapshot.epoch,
            t_virtual=self.clock.now(),
            kind="spoken",
            utterance_class="ack",
            text=text,
            floor_token=self._generate_floor_token(),
            supersedes=supersedes
        )

    def emit_filler(self, epoch: int, text: str = "Hmm...") -> SpokenAction:
        supersedes = self.last_floor_token
        return SpokenAction(
            action_id=self._generate_id("fill"),
            session_id=self.session_id,
            epoch=epoch,
            t_virtual=self.clock.now(),
            kind="spoken",
            utterance_class="filler",
            text=text,
            floor_token=self._generate_floor_token(),
            supersedes=supersedes
        )
        
    def emit_progress(self, epoch: int, text: str = "Working on it...") -> SpokenAction:
        supersedes = self.last_floor_token
        return SpokenAction(
            action_id=self._generate_id("prog"),
            session_id=self.session_id,
            epoch=epoch,
            t_virtual=self.clock.now(),
            kind="spoken",
            utterance_class="progress",
            text=text,
            floor_token=self._generate_floor_token(),
            supersedes=supersedes
        )

    def emit_clarification(self, epoch: int, slot: str, question: str, candidates: Optional[List[str]] = None) -> ClarificationAction:
        return ClarificationAction(
            action_id=self._generate_id("clarify"),
            session_id=self.session_id,
            epoch=epoch,
            t_virtual=self.clock.now(),
            kind="clarification",
            slot=slot,
            question=question,
            candidates=candidates
        )
