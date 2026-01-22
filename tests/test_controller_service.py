import pytest
from unittest.mock import MagicMock
from src.controller_service import ControllerService
from src.serial_manager import SerialManager
from src.constants import EnterpriseCommands, ConsumerACommands, ConsumerBCommands, Protocol, HDC202X24Commands

@pytest.fixture
def mock_serial_manager():
    """Fixture to create a mocked SerialManager."""
    manager = MagicMock(spec=SerialManager)
    manager.is_connected.return_value = True
    manager.port = "/dev/ttyUSB0" # Mock the port attribute
    manager.baudrate = 9600
    # Mock new methods
    manager.read.return_value = b''
    manager.reset_input_buffer = MagicMock()
    
    # Mock connection object for timeout manipulation
    mock_connection = MagicMock()
    mock_connection.timeout = 1.0
    mock_connection.in_waiting = 0 # Default to no data
    manager.connection = mock_connection
    
    return manager

@pytest.fixture
def controller(mock_serial_manager):
    """Fixture to create a ControllerService with the mocked SerialManager."""
    return ControllerService(mock_serial_manager)

def test_switch_port_valid(controller, mock_serial_manager):
    """Test switching to a valid port (1-8)."""
    controller.switch_port(1)
    mock_serial_manager.write.assert_called_with(HDC202X24Commands.SWITCH_PORT_1) # Defaults to HDC202_X24

    controller.update_config(protocol="enterprise")
    controller.switch_port(8)
    mock_serial_manager.write.assert_called_with(EnterpriseCommands.SWITCH_PORT_8)

def test_switch_port_invalid(controller, mock_serial_manager):
    """Test switching to an invalid port raises ValueError."""
    with pytest.raises(ValueError, match="Invalid port ID"):
        controller.switch_port(0)
    
    with pytest.raises(ValueError, match="Invalid port ID"):
        controller.switch_port(9)

    # Ensure no write happened on invalid input
    # mock_serial_manager.write.assert_called() # Removed incorrect assertion
    
    # Actually, let's reset the mock to be sure
    mock_serial_manager.reset_mock()
    
    with pytest.raises(ValueError):
        controller.switch_port(99)
    mock_serial_manager.write.assert_not_called()

def test_control_buzzer_valid(controller, mock_serial_manager):
    """Test controlling the buzzer with valid states."""
    controller.update_config(protocol="enterprise") # Consumer A doesn't have buzzer? Check constants. 
    # Consumer A keys: SWITCH_PORT_1..4. No buzzer.
    
    controller.control_buzzer("on")
    mock_serial_manager.write.assert_called_with(EnterpriseCommands.BUZZER_ON)

    controller.control_buzzer("off")
    mock_serial_manager.write.assert_called_with(EnterpriseCommands.BUZZER_OFF)

def test_control_buzzer_invalid(controller, mock_serial_manager):
    """Test controlling the buzzer with invalid state."""
    with pytest.raises(ValueError):
        controller.control_buzzer("invalid_state")
    
    mock_serial_manager.reset_mock()
    with pytest.raises(ValueError):
        controller.control_buzzer("INVALID_STATE") # Case sensitive check
    mock_serial_manager.write.assert_not_called()

def test_check_status_healthy(controller, mock_serial_manager):
    """Test check_status when connection is healthy."""
    mock_serial_manager.is_connected.return_value = True
    status = controller.check_status()
    
    assert status["status"] == "healthy"
    assert status["connected"] is True
    
    # Ensure we didn't try to reconnect if already connected
    mock_serial_manager.connect.assert_not_called()

def test_check_status_reconnect_success(controller, mock_serial_manager):
    """Test check_status attempts reconnect when disconnected."""
    mock_serial_manager.is_connected.return_value = False
    # Mock connect to return True (success)
    mock_serial_manager.connect.return_value = True
    
    status = controller.check_status()
    
    mock_serial_manager.connect.assert_called_once()
    assert status["status"] == "healthy" # Assumes connect succeeds (no exception raised)
    assert status["connected"] is True

def test_check_status_reconnect_failure(controller, mock_serial_manager):
    """Test check_status when reconnect fails."""
    mock_serial_manager.is_connected.return_value = False
    # Mock connect to return False (failure)
    mock_serial_manager.connect.return_value = False
    
    status = controller.check_status()
    
    mock_serial_manager.connect.assert_called_once()
    assert status["status"] == "unhealthy"
    assert status["connected"] is False

def test_config_update_protocol(controller):
    """Test updating the protocol configuration."""
    controller.update_config(protocol="consumer_a")
    assert controller.current_protocol == Protocol.CONSUMER_A
    
    controller.update_config(protocol="consumer_b")
    assert controller.current_protocol == Protocol.CONSUMER_B

    controller.update_config(protocol="enterprise")
    assert controller.current_protocol == Protocol.ENTERPRISE

def test_config_update_baudrate(controller, mock_serial_manager):
    """Test updating the baudrate configuration."""
    controller.update_config(baudrate=115200)
    assert mock_serial_manager.baudrate == 115200
    mock_serial_manager.reconnect.assert_called_once()

def test_protocol_consumer_a(controller, mock_serial_manager):
    """Test switching ports using Consumer A protocol."""
    controller.update_config(protocol="consumer_a")
    
    controller.switch_port(1)
    mock_serial_manager.write.assert_called_with(ConsumerACommands.SWITCH_PORT_1)
    
    # Test fallback/not implemented behavior if applicable, 
    # but Consumer A supports ports 1-4. Port 5 might fail if not defined in map, 
    # but let's stick to valid ones first.

def test_protocol_consumer_b(controller, mock_serial_manager):
    """Test switching ports using Consumer B protocol."""
    controller.update_config(protocol="consumer_b")
    
    controller.switch_port(1)
    mock_serial_manager.write.assert_called_with(ConsumerBCommands.SWITCH_PORT_1)

def test_terminator_lf(controller, mock_serial_manager):
    """Test using LF terminator."""
    controller.update_config(terminator="lf")
    assert controller.current_terminator == "lf"
    
    # Send a command and check if \n is appended
    controller.update_config(protocol="enterprise")
    controller.switch_port(1)
    
    expected_command = EnterpriseCommands.SWITCH_PORT_1 + b'\n'
    mock_serial_manager.write.assert_called_with(expected_command)

def test_terminator_crlf(controller, mock_serial_manager):
    """Test using CRLF terminator."""
    controller.update_config(terminator="crlf")
    assert controller.current_terminator == "crlf"
    
    controller.update_config(protocol="enterprise")
    controller.switch_port(1)
    
    expected_command = EnterpriseCommands.SWITCH_PORT_1 + b'\r\n'
    mock_serial_manager.write.assert_called_with(expected_command)

def test_protocol_hdc202_x24(controller, mock_serial_manager):
    """Test switching ports using HDC202-X24 protocol."""
    controller.update_config(protocol="hdc202_x24")
    
    controller.switch_port(1)
    mock_serial_manager.write.assert_called_with(HDC202X24Commands.SWITCH_PORT_1)
    
    controller.control_buzzer("on")
    mock_serial_manager.write.assert_called_with(HDC202X24Commands.BUZZER_ON)

def test_send_query(controller, mock_serial_manager):
    """Test sending a query and reading a response."""
    controller.update_config(protocol="hdc202_x24")
    
    # Mock read response
    mock_serial_manager.read.return_value = b'\xAA\xBB\x84\x01\x00\xEA'
    
    response = controller.send_query("buzzer")
    
    assert response == "AA BB 84 01 00 EA"
    
    # Check that reset_input_buffer was called
    mock_serial_manager.reset_input_buffer.assert_called()
    
    # Check write called with correct query command
    mock_serial_manager.write.assert_called_with(HDC202X24Commands.QUERY_BUZZER)
    
    # Check read called
    mock_serial_manager.read.assert_called()

def test_send_query_unsupported(controller):
    """Test sending an unsupported query."""
    controller.update_config(protocol="enterprise")
    
    with pytest.raises(NotImplementedError):
        controller.send_query("buzzer")

def test_init_enforces_9600_baud(mock_serial_manager):
    """Test that initializing ControllerService forces baudrate to 9600."""
    # Setup mock with wrong baudrate
    mock_serial_manager.baudrate = 115200
    mock_serial_manager.is_connected.return_value = True
    
    # Initialize controller
    ControllerService(mock_serial_manager)
    
    # Verify baudrate was corrected
    assert mock_serial_manager.baudrate == 9600
    # Verify it tried to reconnect
    mock_serial_manager.reconnect.assert_called_once()
