import asyncio
from concurrent.futures import ThreadPoolExecutor
from chronos.schemas import TextChunkEvent
import structlog

logger = structlog.get_logger(__name__)

class ModelLoadGuard:
    warmup_complete: bool = False

    @classmethod
    def assert_live_safe(cls):
        if not cls.warmup_complete:
            raise RuntimeError("cold load attempted inside live execution window")

class ASRWorker:
    def __init__(self):
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._semaphore = asyncio.Semaphore(2)

    def warmup(self):
        """
        Loads the model during the 300s warmup hook.
        """
        from faster_whisper import WhisperModel
        # Use a small CPU model per constraints.
        self._model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        ModelLoadGuard.warmup_complete = True
        logger.info("asr_warmup_complete")

    async def transcribe(self, audio_path: str, event_id: str, session_id: str, t_virtual: float) -> TextChunkEvent:
        ModelLoadGuard.assert_live_safe()

        async with self._semaphore:
            text = await asyncio.get_running_loop().run_in_executor(
                self._executor,
                self._transcribe_sync,
                audio_path
            )

        return TextChunkEvent(
            event_id=f"asr-{event_id}",
            session_id=session_id,
            t_virtual=t_virtual,
            kind="text_chunk",
            text=text,
            is_end_of_turn=True,
            origin="asr"
        )

    def _transcribe_sync(self, audio_path: str) -> str:
        if not self._model:
            raise RuntimeError("ASR model not initialized")
            
        segments, info = self._model.transcribe(audio_path, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text
