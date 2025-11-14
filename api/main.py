"""Neural Network Inference API - Main application.

Inference-only FastAPI backend that loads pre-trained models from Hugging Face Hub.
Models are trained locally and uploaded to HF Hub separately.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import inference
from api.state import state
from hf_hub import ModelManager, get_default_model
from schemas import HealthCheck

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load model from HF Hub on startup.

    Args:
        app: FastAPI application instance

    Yields:
        None after initialization
    """
    # Load model from Hugging Face Hub
    try:
        print("Loading model from Hugging Face Hub...")
        model_name = get_default_model()
        manager = ModelManager()
        state.network = manager.load_model(model_name)
        print(f"✓ Loaded model: {model_name}")
        print(f"  Architecture: {state.network.sizes}")
        print(f"  Activation: {state.network.activation_name}")
    except Exception as e:
        print(f"ERROR: Failed to load model from HF Hub: {e}")
        print("Please check your .env configuration:")
        print("  - HF_MODEL_REPO=your-username/hippo-models")
        print("  - DEFAULT_MODEL=model-name")
        print("  - HUGGINGFACE_TOKEN=hf_... (optional for public repos)")

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
