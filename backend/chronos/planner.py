from typing import List, Dict, Any, Optional
from chronos.schemas import ToolCallAction, StateSnapshot
from chronos.supervisor import ClockSupervisor
import structlog

logger = structlog.get_logger(__name__)

class ToolManifest:
    def __init__(self, tools: List[Dict[str, Any]]):
        self.tools = tools
        
    def get_tool_names(self) -> List[str]:
        return [t.get("name") for t in self.tools]
        
    def is_read_only(self, tool_name: str) -> bool:
        for t in self.tools:
            if t.get("name") == tool_name:
                return t.get("read_only", False)
        return False

class SlowPathPlanner:
    def __init__(self, manifest: ToolManifest, supervisor: ClockSupervisor):
        self.manifest = manifest
        self.supervisor = supervisor
        
    def generate_plan(self, snapshot: StateSnapshot) -> Optional[List[ToolCallAction]]:
        """
        Mock slow path planner.
        Obeys degradation policies.
        """
        tier = self.supervisor.tier()
        
        if tier == "terminal":
            return None
            
        if tier == "degraded":
            # Bypass Tier 2 and Planning. Clarification preferred over new tool dispatch.
            logger.info("planner_bypassed_degraded")
            return None
            
        if tier == "throttled":
            # Speculation disabled; single-tool-per-turn planning
            logger.info("planner_throttled_single_tool")
            # Mock single tool action
            if not snapshot.intent:
                return None
            return [
                ToolCallAction(
                    call_id="mock_call_1",
                    tool_name="mock_tool",
                    args={},
                    idem_key="mock_idem_1"
                )
            ]
            
        # full
        logger.info("planner_full")
        # Speculation enabled (read-only only); multi-step plans allowed
        return [
            ToolCallAction(
                call_id="mock_call_1",
                tool_name="mock_tool_ro",
                args={},
                idem_key="mock_idem_1"
            ),
            ToolCallAction(
                call_id="mock_call_2",
                tool_name="mock_tool",
                args={},
                idem_key="mock_idem_2"
            )
        ]
