import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.assistants.orchestrator_assistant import orchestrator_loop
from app.assistants.state import SessionState

app = FastAPI(title="Reframe Edge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections: dict[str, WebSocket] = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "Reframe Edge API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket

    logger.info(f"WebSocket connection established for session: {session_id}")

    try:
        # Create session state
        session_state = SessionState(session_id=session_id)

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            logger.info(f"Received message: {message}")

            if message.get("type") == "init":
                # Send acknowledgment
                await websocket.send_json({
                    "type": "init_ack",
                    "session_id": session_id
                })

            elif message.get("type") == "user_msg":
                user_message = message.get("data", {}).get("message", "")

                # Process message through orchestrator
                async for event in orchestrator_loop(user_message, session_state):
                    if event["type"] == "assistant_message":
                        # Stream assistant response
                        await websocket.send_json({
                            "type": "assistant_stream",
                            "data": {
                                "content": event["content"],
                                "phase": session_state.current_phase
                            }
                        })

                    elif event["type"] == "phase_change":
                        # Notify phase change
                        await websocket.send_json({
                            "type": "phase_change",
                            "data": {
                                "from_phase": event["from_phase"],
                                "to_phase": event["to_phase"]
                            }
                        })

                    elif event["type"] == "pdf_ready":
                        # Notify PDF is ready
                        await websocket.send_json({
                            "type": "pdf_ready",
                            "data": {
                                "url": event["url"],
                                "filename": event["filename"]
                            }
                        })

                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "session_id": session_id,
                        "phase": session_state.current_phase
                    }
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e!s}")
        active_connections.pop(session_id, None)
        await websocket.close()


@app.on_event("startup")
async def startup_event():
    logger.info("Reframe Edge API started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Reframe Edge API shutting down")
    # Close all active connections
    for session_id, websocket in active_connections.items():
        await websocket.close()
