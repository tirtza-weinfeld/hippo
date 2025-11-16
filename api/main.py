"""Neural Network Inference API - Main application.

Inference-only FastAPI backend that loads pre-trained models from Hugging Face Hub.
Models are trained locally and uploaded to HF Hub separately.
"""

from dotenv import load_dotenv

# Load environment variables BEFORE any imports that depend on them
# This must be called before importing db module (which reads DATABASE_URL)
load_dotenv()

# ruff: noqa: E402 - imports after load_dotenv() are intentional
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import inference, vocabulary
from api.state import state
from db import Base, engine
from hf_hub import ModelManager, get_default_model
from schemas import HealthCheck

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database and load model from HF Hub on startup.

    Args:
        app: FastAPI application instance

    Yields:
        None after initialization
    """
    # Check database connection (tables should be created via migrations)
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            # Check if vocabulary tables exist
            result = conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'words')"
                )
            )
            tables_exist = result.scalar()

            if tables_exist:
                logger.info("✓ Database connection verified")
            else:
                logger.warning("Database tables not found!")
                logger.warning("Run migrations: make upgrade")
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        logger.warning("Vocabulary endpoints may not work without database access")
        logger.warning("Ensure migrations are run: make upgrade")

    # Load model from Hugging Face Hub
    try:
        logger.info("Loading model from Hugging Face Hub...")
        model_name = get_default_model()
        manager = ModelManager()
        state.network = manager.load_model(model_name)
        logger.info(f"✓ Loaded model: {model_name}")
        logger.info(f"  Architecture: {state.network.sizes}")
        logger.info(f"  Activation: {state.network.activation_name}")
    except Exception as e:
        logger.error(f"Failed to load model from HF Hub: {e}")
        logger.error("Please check your .env configuration:")
        logger.error("  - HF_MODEL_REPO=your-username/hippo-models")
        logger.error("  - DEFAULT_MODEL=model-name")
        logger.error("  - HUGGINGFACE_TOKEN=hf_... (optional for public repos)")

    yield


app = FastAPI(
    title="Neural Network Inference API",
    description="Inference-only API for neural networks trained locally. Models loaded from Hugging Face Hub.",
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
app.include_router(vocabulary.router)


@app.get("/healthz", response_model=HealthCheck)
def health_check() -> HealthCheck:
    """Check API health and model loading status.

    Returns:
        Health check response with system status
    """
    return HealthCheck(
        status="healthy",
        network_loaded=state.network is not None,
    )
