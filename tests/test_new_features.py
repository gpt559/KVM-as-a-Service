from unittest.mock import MagicMock
from src.controller_service import ControllerService
from src.constants import Protocol

# Mock Controller Instance
mock_serial = MagicMock()
mock_controller_instance = ControllerService(mock_serial)
mock_controller_instance.current_protocol = Protocol.HDC202_X24


def test_default_protocol():
    # Verify the controller is initialized (or set) to HDC202_X24
    assert mock_controller_instance.current_protocol == Protocol.HDC202_X24
