from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.main import app, get_controller
from src.controller_service import ControllerService
from src.constants import Protocol

client = TestClient(app)

# Mock Controller
mock_serial = MagicMock()
mock_controller = ControllerService(mock_serial)
mock_controller.send_query = MagicMock(return_value="AA BB CC")

# Override dependency
app.dependency_overrides[get_controller] = lambda: mock_controller

def test_default_protocol():
    # Verify the controller is initialized with HDC202_X24
    assert mock_controller.current_protocol == Protocol.HDC202_X24

def test_run_all_queries_endpoint():
    # Mock run_all_queries to avoid hitting the real method which iterates commands
    # We want to test the API endpoint integration
    
    mock_results = [
        {"command": "test_cmd", "response": "AA BB", "status": "success"},
        {"command": "fail_cmd", "response": "Error", "status": "error"}
    ]
    
    with patch.object(mock_controller, 'run_all_queries', return_value=mock_results):
        response = client.post("/api/v1/test/queries")
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert len(data["logs"]) == 2
        assert data["logs"][0]["action"] == "Query: test_cmd"
        assert data["logs"][0]["status"] == "success"
        assert data["logs"][0]["detail"] == "AA BB"
        assert data["logs"][1]["status"] == "failed"

def test_run_all_queries_logic():
    # Test the actual logic in controller_service
    # We need to mock _get_commands to return a dummy class with QUERY_ attributes
    
    class DummyCommands:
        QUERY_ONE = b'\x01'
        QUERY_TWO = b'\x02'
        OTHER = b'\x03'
        
    with patch.object(mock_controller, '_get_commands', return_value=DummyCommands):
        with patch.object(mock_controller, 'send_query', side_effect=["RESP1", Exception("Fail")]):
            results = mock_controller.run_all_queries()
            
            assert len(results) == 2
            assert results[0]["command"] == "one"
            assert results[0]["response"] == "RESP1"
            assert results[0]["status"] == "success"
            
            assert results[1]["command"] == "two"
            assert results[1]["status"] == "error"
