import asyncio
from concurrent.futures import ThreadPoolExecutor
from chronos.schemas import SlotValue
import structlog

logger = structlog.get_logger(__name__)

class OCRWorker:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._semaphore = asyncio.Semaphore(2)

    async def extract_text(self, image_path: str, event_id: str, t_virtual: float) -> SlotValue:
        async with self._semaphore:
            text = await asyncio.get_running_loop().run_in_executor(
                self._executor,
                self._extract_sync,
                image_path
            )

        return SlotValue(
            value=text,
            confidence=0.9, 
            modality="visual",
            t_virtual=t_virtual,
            source_event_id=event_id
        )

    def _extract_sync(self, image_path: str) -> str:
        import pytesseract
        from PIL import Image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image).strip()
        return text
