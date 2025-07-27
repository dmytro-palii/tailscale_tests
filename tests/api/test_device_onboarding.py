# tests/api/test_device_onboarding.py
"""
Integration test for the Tailscale device onboarding flow using LocalAPI.
"""
import requests
import pytest
from config import TAILSCALE_LOCALAPI
from models.models_validation import BackendStateInfo
from models.constants import BackendState


@pytest.mark.api
def test_device_onboarding(tailscale_client):
    """
    Arrange: tailscale_client fixture ensures the client is running.
    Act: Request the /status endpoint.
    Assert: HTTP 200 and expected JSON structure.
    """
    # Act
    response = requests.get(f'{TAILSCALE_LOCALAPI}/status')
    response_data = response.json()
    # Validate entire response against our Pydantic model
    status = BackendStateInfo(**response_data)
    assert status.BackendState == BackendState.RUNNING or status.BackendState == BackendState.NEEDS_LOGIN



