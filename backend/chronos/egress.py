import json
from typing import Any, Optional
import structlog
from pydantic import TypeAdapter, ValidationError

from chronos.schemas import OutboundAction, FinalResponseAction, StateSnapshot

logger = structlog.get_logger(__name__)
outbound_adapter = TypeAdapter(OutboundAction)

class EgressSerializer:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def serialize(self, payload: Any) -> dict:
        """
        Validates an OutboundAction using Pydantic fail-closed schema validation.
        If validation fails, attempts a structural repair. If repair fails, emits a degraded response.
        Stamps protocol metadata and logs the telemetry tee.
        """
        try:
            if isinstance(payload, dict):
                validated = outbound_adapter.validate_python(payload)
                action_dict = validated.model_dump()
            else:
                validated = outbound_adapter.validate_python(payload.model_dump())
                action_dict = validated.model_dump()
                
        except ValidationError as e:
            logger.warning("egress_validation_failed", error=str(e), payload=str(payload))
            # Attempt one structural repair
            if isinstance(payload, dict):
                payload_copy = payload.copy()
                repaired = False
                if "session_id" not in payload_copy:
                    payload_copy["session_id"] = self.session_id
                    repaired = True
                if "t_virtual" not in payload_copy:
                    payload_copy["t_virtual"] = 0.0
                    repaired = True
                
                if repaired:
                    try:
                        validated = outbound_adapter.validate_python(payload_copy)
                        action_dict = validated.model_dump()
                    except ValidationError:
                        action_dict = self._degraded_fallback(payload).model_dump()
                else:
                    action_dict = self._degraded_fallback(payload).model_dump()
            else:
                action_dict = self._degraded_fallback(payload).model_dump()
        except Exception as e:
            logger.error("egress_serialization_error", error=str(e))
            action_dict = self._hard_fallback().model_dump()

        # Telemetry Tee
        logger.info("outbound_action", action=action_dict)
        return action_dict

    def _degraded_fallback(self, original_payload: Any) -> FinalResponseAction:
        epoch = 0
        t_virtual = 0.0
        
        if isinstance(original_payload, dict):
            epoch = original_payload.get("epoch", 0)
            t_virtual = original_payload.get("t_virtual", 0.0)
        elif hasattr(original_payload, "epoch"):
            epoch = getattr(original_payload, "epoch", 0)
            t_virtual = getattr(original_payload, "t_virtual", 0.0)
            
        snapshot = StateSnapshot(
            snapshot_id="fallback",
            epoch=epoch,
            parent_id=None,
            intent=None,
            intent_status="abandoned",
            slots={},
            changed_slots=[],
            t_virtual=t_virtual
        )
        return FinalResponseAction(
            action_id="degraded-fallback",
            session_id=self.session_id,
            epoch=epoch,
            t_virtual=t_virtual,
            kind="final_response",
            text="I'm sorry, I encountered an internal error and couldn't process that properly.",
            snapshot=snapshot,
            status="degraded"
        )
        
    def _hard_fallback(self) -> FinalResponseAction:
        snapshot = StateSnapshot(
            snapshot_id="hard-fallback",
            epoch=0,
            parent_id=None,
            intent=None,
            intent_status="abandoned",
            slots={},
            changed_slots=[],
            t_virtual=0.0
        )
        return FinalResponseAction(
            action_id="hard-fallback",
            session_id=self.session_id,
            epoch=0,
            t_virtual=0.0,
            kind="final_response",
            text="Fatal system error.",
            snapshot=snapshot,
            status="degraded"
        )
