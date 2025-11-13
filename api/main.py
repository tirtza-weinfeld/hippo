"""Neural Network Learning API - Main application.

Modern Python 3.14+ FastAPI backend for learning neural networks
following the 3Blue1Brown tutorial series.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import network, mnist
from api.state import state
from neural_networks import MNISTLoader
from schemas import HealthCheck

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load MNIST data on startup.

    Args:
        app: FastAPI application instance

    Yields:
        None after initialization
    """
    try:
        state.training_data, state.validation_data, state.test_data = MNISTLoader.load_data()
        state.mnist_loaded = True
    except RuntimeError as e:
        print(f"Warning: Failed to load MNIST data: {e}")

    yield


app = FastAPI(
    title="Neural Network Learning API",
    description="Backend for learning neural networks following 3Blue1Brown tutorial",
    version="1.0.0",
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
app.include_router(network.router)
app.include_router(mnist.router)


@app.get("/healthz", response_model=HealthCheck)
def health_check() -> HealthCheck:
    """Check API health and data loading status.

    Returns:
        Health check response with system status
    """
    return HealthCheck(
        status="healthy",
        network_loaded=state.network is not None,
        mnist_loaded=state.mnist_loaded,
    )
