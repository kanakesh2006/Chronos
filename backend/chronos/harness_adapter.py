import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import structlog
from typing import Optional

logger = structlog.get_logger(__name__)

app = FastAPI(title="Chronos Telemetry Tee")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"websocket_broadcast_error: {e}")

manager = ConnectionManager()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def emit_telemetry_sync(trace_event: dict):
    """
    Called by the EgressSerializer to tee telemetry output.
    """
    json_str = json.dumps(trace_event)
    logger.info("telemetry_tee", event=json_str)
    
    # Fire and forget broadcast
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(json_str))
    except RuntimeError:
        pass # Not in an event loop

@app.get("/health")
async def health():
    return {"status": "ok"}
