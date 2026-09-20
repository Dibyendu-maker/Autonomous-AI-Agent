"""FastAPI application entrypoint configuring routers, middleware, and static UI."""
import os
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router as api_router
from app.api.websocket import ws_router
from app.config import settings

# Configure logging format
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycles."""
    logger.info("=" * 60)
    logger.info("Autonomous AI Agent System Initialized")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER} ({settings.LLM_MODEL})")
    logger.info(f"Search Provider: {settings.SEARCH_PROVIDER}")
    logger.info(f"Max Retries: {settings.MAX_RETRY_LOOPS}")
    logger.info("=" * 60)
    yield
    logger.info("Autonomous AI Agent System shutting down.")


app = FastAPI(
    title="Autonomous AI Agent - LangGraph Research System",
    description="Multi-agent architecture with planning, tool invocation, self-reflection, and retry loops.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API and WebSocket routers
app.include_router(api_router)
app.include_router(ws_router)

# Mount static directory for visualization UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the single-page interactive agent dashboard."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Autonomous Agent API running. Visit /docs for OpenAPI specifications."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
