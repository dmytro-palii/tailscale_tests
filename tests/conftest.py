# tests/conftest.py
"""
Conftest module defining shared pytest fixtures for Tailscale test automation.
Fixtures in this module set up and tear down the Tailscale client and network mesh
for end-to-end and integration tests.
"""
from contextlib import suppress
import pytest
import subprocess
import requests
from config import TAILSCALE_LOCALAPI


@pytest.fixture(scope='session')
def tailscale_client():
    """
    Session-scoped fixture that ensures the Tailscale client is installed,
    running, and reachable via its LocalAPI.

    Yields:
    None: after verifying client status, allowing tests to run.
    Teardown:
    Logs out the client via `tailscale logout` after all tests complete.
    """
    response = requests.get(f'{TAILSCALE_LOCALAPI}/status')
    assert response.status_code == 200, "LocalAPI status check failed"
    yield
    subprocess.run(['tailscale', 'logout'], check=False)


@pytest.fixture(scope='session')
def network_mesh():
    """
    Session-scoped fixture that represents the test mesh configuration.
    
    In an end-user context, assumes runners are already joined to a shared tailnet.
    Can be extended to programmatically configure a Headscale-controlled tailnet.
    """
    yield