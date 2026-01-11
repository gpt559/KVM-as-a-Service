from unittest.mock import MagicMock, patch
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

def test_get_status(client, mock_controller):
    """Test the /api/v1/status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "connected": True,
        "port": "/dev/ttyUSB0"
    }
    mock_controller.check_status.assert_called_once()

def test_switch_port_success(client, mock_controller):
    """Test switching port successfully."""
    response = client.post("/api/v1/switch", json={"port": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Switched to Port 1" in data["message"]
    mock_controller.switch_port.assert_called_once_with(1)

def test_switch_port_invalid_input(client, mock_controller):
    """Test switching port with invalid input (validation error)."""
    # Port 9 is out of range (1-8)
    response = client.post("/api/v1/switch", json={"port": 9})
    assert response.status_code == 422 # FastAPI default validation error
    mock_controller.switch_port.assert_not_called()

def test_switch_port_value_error(client, mock_controller):
    """Test switching port when controller raises ValueError."""
    mock_controller.switch_port.side_effect = ValueError("Invalid port ID")
    
    # Even if pydantic validates it, if controller rejects it (double check), it should return 400
    # Note: Pydantic usually catches this first, but this tests the exception handler
    response = client.post("/api/v1/switch", json={"port": 1})
    assert response.status_code == 400
    assert "Invalid port ID" in response.json()["detail"]

def test_switch_port_hardware_failure(client, mock_controller):
    """Test switching port when hardware fails."""
    mock_controller.switch_port.side_effect = Exception("Serial timeout")
    
    response = client.post("/api/v1/switch", json={"port": 1})
    assert response.status_code == 503
    assert "Hardware communication failed" in response.json()["detail"]

def test_buzzer_control_on(client, mock_controller):
    """Test turning buzzer on."""
    response = client.post("/api/v1/buzzer", json={"state": "on"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Buzzer turned on" in data["message"]
    mock_controller.control_buzzer.assert_called_once_with("on")

def test_buzzer_control_off(client, mock_controller):
    """Test turning buzzer off."""
    response = client.post("/api/v1/buzzer", json={"state": "off"})
    assert response.status_code == 200
    mock_controller.control_buzzer.assert_called_once_with("off")

def test_buzzer_invalid_state(client, mock_controller):
    """Test buzzer with invalid state."""
    response = client.post("/api/v1/buzzer", json={"state": "maybe"})
    assert response.status_code == 422 # Validation error
    mock_controller.control_buzzer.assert_not_called()

def test_buzzer_hardware_failure(client, mock_controller):
    """Test buzzer when hardware fails."""
    mock_controller.control_buzzer.side_effect = Exception("IO Error")
    
    response = client.post("/api/v1/buzzer", json={"state": "on"})
    assert response.status_code == 503
    assert "Hardware communication failed" in response.json()["detail"]
