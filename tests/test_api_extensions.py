from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from src.main import app, get_controller
from src.controller_service import ControllerService

# Fixture to mock the ControllerService
@pytest.fixture
def mock_controller():
    controller = MagicMock(spec=ControllerService)
    # Default status to healthy
    controller.check_status.return_value = {
        "status": "healthy",
        "connected": True,
        "port": "/dev/ttyUSB0"
    }
    return controller

# Fixture to override the dependency in the app
@pytest.fixture
def client(mock_controller):
    app.dependency_overrides[get_controller] = lambda: mock_controller
    with TestClient(app) as test_client:
        yield test_client
    # Clean up overrides
    app.dependency_overrides = {}

def test_set_light_mode(client, mock_controller):
    response = client.post("/api/v1/light", json={"mode": "flow"})
    assert response.status_code == 200
    assert response.json()["message"] == "Light mode set to flow"
    mock_controller.set_light_mode.assert_called_once_with("flow")

def test_set_fan_mode(client, mock_controller):
    response = client.post("/api/v1/fan", json={"mode": "auto"})
    assert response.status_code == 200
    assert response.json()["message"] == "Fan mode set to auto"
    mock_controller.set_fan_mode.assert_called_once_with("auto")

def test_set_audio_source(client, mock_controller):
    response = client.post("/api/v1/audio/source", json={"port": 2})
    assert response.status_code == 200
    assert response.json()["message"] == "Audio source set to PC2"
    mock_controller.set_audio_source.assert_called_once_with(2)

def test_set_network_power(client, mock_controller):
    response = client.post("/api/v1/network", json={"port": 1, "enabled": True})
    assert response.status_code == 200
    assert response.json()["message"] == "Network for PC1 enabled"
    mock_controller.set_network_power.assert_called_once_with(1, True)

def test_set_usb_focus(client, mock_controller):
    response = client.post("/api/v1/usb/focus", json={"target": "pc1"})
    assert response.status_code == 200
    assert response.json()["message"] == "USB focus switched to pc1"
    mock_controller.set_usb_focus.assert_called_once_with("pc1")

def test_feature_toggle(client, mock_controller):
    response = client.post("/api/v1/system/autodetect", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["message"] == "Auto-detect disabled"
    mock_controller.set_feature_state.assert_called_once_with("AUTODETECT", False, "Auto-detect")
