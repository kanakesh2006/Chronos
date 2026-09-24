# Chronos - Samsung PRISM GenAI Hackathon 2026

**Theme 05: Interruptible Real-Time Agents**

Chronos is a virtual-clock-native agent kernel designed for full-duplex, interruptible conversations. It safely handles interruptions, mid-dispatch cancellations, and out-of-order multimodal inputs using a deterministic, epoch-based effect gateway, strictly ensuring no double-mutations (e.g. double booking) ever occur.

## Architecture Highlights
- **Epoch Arbiter & Effect Gateway:** A monotonically increasing session epoch stamps all effects. If an intent is corrected (e.g., via audio interruption), the epoch is bumped. The effect gateway synchronously "poisons" all pending mutating effects from the older epoch. When a stale tool call completes, its result is refused at the commit gate.
- **Fail-Closed Egress Validation:** `EgressSerializer` leverages strict Pydantic v2 validation. If the LLM generates a hallucinated tool format, it initiates a single repair attempt before cleanly degrading to a fallback response.
- **Multimodal Contradiction Resolver:** Deterministic priority table resolution. Visual signals override audio for identity (e.g., flight codes), while audio overrides visual for intent (e.g., "cancel that"). 
- **Clock Supervisor:** Enforces a 120s wall-clock cap with a four-tier degradation ladder (`full`, `throttled`, `degraded`, `terminal`), independently of the virtual clock.

## Reproducible Docker Setup

As per NFR-3, this project can be run locally using Docker without any external network dependencies (all models are mocked or run via local CPU-friendly integrations like `faster-whisper`).

### Prerequisites
- Docker and Docker Compose installed.

### Running the Project
```bash
docker compose up --build
```

This will launch two services:
1. **Backend API (Port 8000)**: The core Chronos FastAPI engine and WebSocket tee.
2. **Dashboard (Port 3000)**: The Next.js telemetry UI that visualizes the timeline, snapshot lattice, and effect registry in real-time.

Navigate to `http://localhost:3000` to view the telemetry dashboard.

## Running Tests

All core invariants (Invariant 1, 3, 5, 6, 7) are validated via a mix of `pytest` unit tests, `hypothesis` property-based tests for randomized interruption timing, and programmatic integration tests.

To run the test suite locally:
```bash
# Set PYTHONPATH to the backend directory
export PYTHONPATH=$(pwd)/backend

# Run pytest
pytest backend/tests/
```
The suite includes the `test_integration.py` which precisely reproduces the end-to-end adversarial trace specified in Section 16 of the Project Spec, asserting that the stale tool result is discarded and no double-booking occurs.
