# models/constants.py
"""
Constants for Tailscale LocalAPI fields and allowed values.
"""
from enum import Enum


class BackendState(Enum):
    """
    Allowed values for the Tailscale LocalAPI 'BackendState' field.
    """
    RUNNING = 'Running'
    NEEDS_LOGIN = 'NeedsLogin'