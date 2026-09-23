FROM python:3.12-slim

WORKDIR /app

# Copy dependency list if a requirements.txt existed, else just pip install directly
# For hackathon simplicity, installing inline
RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic structlog faster-whisper pytesseract pillow \
    llama-cpp-python outlines \
    pytest pytest-asyncio hypothesis anyio

# Ensure tesseract-ocr is installed on the system
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

COPY backend/ /app/backend/

ENV PYTHONPATH=/app/backend

# Start the harness adapter
CMD ["uvicorn", "chronos.harness_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
