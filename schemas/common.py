"""Common schemas used across the API."""

from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    network_loaded: bool
