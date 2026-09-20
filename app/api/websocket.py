"""WebSocket handler providing live streaming of the agent's internal thought and execution loop."""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import settings
from app.graph.workflow import create_agent_graph

logger = logging.getLogger(__name__)
ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """Streams step-by-step agent graph updates over a persistent WebSocket."""
    await websocket.accept()
    logger.info("Client connected to agent WebSocket stream.")

    try:
        while True:
            # Expecting client message: {"goal": "...", "max_retries": 3}
            raw_data = await websocket.receive_text()
            payload = json.loads(raw_data)
            goal = payload.get("goal")

            if not goal:
                await websocket.send_json({
                    "event": "error",
                    "message": "Goal parameter is required."
                })
                continue

            max_retries = payload.get("max_retries", settings.MAX_RETRY_LOOPS)

            # Send initial acknowledgment
            await websocket.send_json({
                "event": "started",
                "goal": goal,
                "llm_provider": settings.LLM_PROVIDER,
                "search_provider": settings.SEARCH_PROVIDER,
            })

            # Prepare graph
            app_graph = create_agent_graph()
            initial_state = {
                "goal": goal,
                "plan": [],
                "current_task_index": 0,
                "research_notes": [],
                "evaluation_history": [],
                "retry_count": 0,
                "max_retries": max_retries,
                "final_report": None,
                "status": "started",
                "logs": [],
            }

            # Run stream in an executor so blocking network/LLM calls don't freeze the event loop
            loop = asyncio.get_running_loop()

            def run_stream():
                # returns list of (node, output)
                events = []
                for event in app_graph.stream(initial_state, stream_mode="updates"):
                    events.append(event)
                return events

            # To provide true live streaming without blocking, we can iterate asynchronously
            def stream_generator():
                for step in app_graph.stream(initial_state, stream_mode="updates"):
                    yield step

            # Stream steps
            for update in await loop.run_in_executor(None, lambda: list(stream_generator())):
                for node_name, node_state in update.items():
                    logger.info(f"[WebSocket] Emitting update from node: {node_name}")
                    await websocket.send_json({
                        "event": "node_update",
                        "node": node_name,
                        "data": node_state,
                    })
                    # Brief breath for smooth UI animation
                    await asyncio.sleep(0.05)

            await websocket.send_json({
                "event": "finished",
                "message": "Agent execution cycle concluded.",
            })

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket stream.")
    except Exception as e:
        logger.exception("Error during WebSocket streaming session")
        try:
            await websocket.send_json({
                "event": "error",
                "message": str(e)
            })
        except Exception:
            pass
