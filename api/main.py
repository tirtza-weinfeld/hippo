"""Neural Network Inference API - Main application.

Inference-only FastAPI backend that loads pre-trained models from Hugging Face Hub.
Models are trained locally and uploaded to HF Hub separately.
"""

from dotenv import load_dotenv

# Load environment variables BEFORE any imports that depend on them
# This must be called before importing db module (which reads DATABASE_URL)
_ = load_dotenv()

# ruff: noqa: E402 - imports after load_dotenv() are intentional
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.routes import inference
from api.routes.dictionary import router as dictionary_router
from api.state import state
from api.utils import logger
from db import engine
from hf_hub import ModelManager, get_default_model
from schemas import HealthCheck


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Initialize database and load model from HF Hub on startup.

    Args:
        _app: FastAPI application instance (unused)

    Yields:
        None after initialization
    """
    # Check database connection (tables should be created via migrations)
    try:
        with engine.connect() as conn:
            # Check if dictionary tables exist
            query = (
                "SELECT EXISTS ("
                "SELECT FROM information_schema.tables WHERE table_name = 'words')"
            )
            result = conn.execute(text(query))
            tables_exist = result.scalar()

            if tables_exist:
                logger.info("✓ Database connection verified")
            else:
                logger.warning("Database tables not found!")
                logger.warning("Run migrations: make upgrade")
    except Exception as e:
        logger.warning("Database connection check failed: %s", e)
        logger.warning("Dictionary endpoints may not work without database access")
        logger.warning("Ensure migrations are run: make upgrade")

    # Load model from Hugging Face Hub
    try:
        logger.info("Loading model from Hugging Face Hub...")
        model_name = get_default_model()
        manager = ModelManager()
        state.network = manager.load_model(model_name)
        logger.info("✓ Loaded model: %s", model_name)
        logger.info("  Architecture: %s", state.network.sizes)
        logger.info("  Activation: %s", state.network.activation_name)
    except Exception:
        logger.exception("Failed to load model from HF Hub")
        logger.error("Please check your .env configuration:")
        logger.error("  - HF_MODEL_REPO=your-username/hippo-models")
        logger.error("  - DEFAULT_MODEL=model-name")
        logger.error("  - HUGGINGFACE_TOKEN=hf_... (optional for public repos)")

    yield


app = FastAPI(
    title="Neural Network Inference API",
    description=(
        "Inference-only API for neural networks trained locally. "
        "Models loaded from Hugging Face Hub."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inference.router)
app.include_router(dictionary_router)


@app.get("/healthz", response_model=HealthCheck)
def health_check() -> HealthCheck:
    """Check API health, model loading status, and database connectivity.

    Returns:
        Health check response with system status
    """
    # Check database connectivity
    database_connected = False
    try:
        with engine.connect() as conn:
            _ = conn.execute(text("SELECT 1"))
            database_connected = True
    except Exception:
        logger.exception("Database health check failed")
        database_connected = False

    return HealthCheck(
        status="healthy",
        network_loaded=state.network is not None,
        database_connected=database_connected,
    )
