# config.py
"""
Configuration module for the Tailscale test suite.
Houses environment-driven constants used across tests.
"""

import os

#: LocalAPI base URL for the Tailscale client endpoints.
#:
#: Can be overridden by setting the TAILSCALE_LOCALAPI environment variable,
#: e.g., in CI workflows or local development.
TAILSCALE_LOCALAPI: str = os.getenv(
    "TAILSCALE_LOCALAPI",
    "http://localhost:41112/localapi/v0"
)
