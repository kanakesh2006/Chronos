import re
from typing import List
from chronos.schemas import TextChunkEvent
import structlog

logger = structlog.get_logger(__name__)

# Precompiled regexes for sub-millisecond filtering
CORRECTION_MARKERS = re.compile(r"\b(no wait|actually|sorry I meant|scratch that)\b", re.IGNORECASE)
EXPLICIT_CANCEL = re.compile(r"\b(stop|cancel that)\b", re.IGNORECASE)
DISFLUENCIES = re.compile(r"\b(um|uh|hmm)\b", re.IGNORECASE)

def filter_lexical(event: TextChunkEvent) -> str:
    """
    Tier-1 Lexical Fast-Filter.
    Returns one of: 'correction', 'cancel', 'disfluency', 'clear', 'ambiguous'
    """
    text = event.text
    
    if EXPLICIT_CANCEL.search(text):
        return "cancel"
        
    if CORRECTION_MARKERS.search(text):
        # Could be correction + value
        return "correction"
        
    if DISFLUENCIES.search(text):
        return "disfluency"
        
    return "clear"

def check_hard_override(slot_name: str, in_flight_slots: List[str]) -> bool:
    """
    Invariant 5: If the slot backs an in-flight mutating effect, force epoch bump.
    """
    return slot_name in in_flight_slots
