# models/models_validation.py
"""
Data models for validating Tailscale LocalAPI responses.
"""
from pydantic import BaseModel
from models.constants import BackendState


class BackendStateInfo(BaseModel):
    """
    Data model representing the 'BackendState' field
    returned by the Tailscale LocalAPI.
    """
    BackendState: BackendState