import pytest
from unittest.mock import MagicMock
from src.controller_service import ControllerService
from src.serial_manager import SerialManager
from src.constants import EnterpriseCommands, ConsumerACommands, ConsumerBCommands, Protocol, HDC202X24Commands
from src.protocol_handler import ProtocolHandler

@pytest.fixture
def mock_serial_manager():
    """Fixture to create a mocked SerialManager."""
    manager = MagicMock(spec=SerialManager)
    manager.is_connected.return_value = True
    manager.port = "/dev/ttyUSB0" # Mock the port attribute
    manager.baudrate = 9600
    # Mock new methods
    manager.read_existing.return_value = b''
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
    c = ControllerService(mock_serial_manager)
    yield c
    # Cleanup
    c._shutdown_event.set()
    c._monitor_thread.join(timeout=1.0)

def test_switch_port_valid(controller, mock_serial_manager):
    """Test switching to a valid port (1-8)."""
    # Default is HDC202
    controller.switch_port(1)
    
    # Expected packet: AA BB 03 00 00 CS
    expected_packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_SWITCH_PORT, [0x00, 0x00])
    mock_serial_manager.write.assert_called_with(expected_packet)

    controller.update_config(protocol="enterprise")
    controller.switch_port(8)
    mock_serial_manager.write.assert_called_with(EnterpriseCommands.SWITCH_PORT_8)

def test_switch_port_invalid(controller, mock_serial_manager):
    """Test switching to an invalid port raises ValueError."""
    with pytest.raises(ValueError, match="Invalid port ID"):
        controller.switch_port(0)
    
    with pytest.raises(ValueError, match="Invalid port ID"):
        controller.switch_port(9)

    mock_serial_manager.reset_mock()
    
    with pytest.raises(ValueError):
        controller.switch_port(99)
    mock_serial_manager.write.assert_not_called()

def test_control_buzzer_valid(controller, mock_serial_manager):
    """Test controlling the buzzer with valid states."""
    # Test HDC202 (Default)
    controller.control_buzzer("on")
    expected_on = ProtocolHandler.build_packet(HDC202X24Commands.CMD_BUZZER, [0x00, 0x01])
    mock_serial_manager.write.assert_called_with(expected_on)

    controller.update_config(protocol="enterprise")
    controller.control_buzzer("on")
    mock_serial_manager.write.assert_called_with(EnterpriseCommands.BUZZER_ON)

def test_control_buzzer_invalid(controller, mock_serial_manager):
    """Test controlling the buzzer with invalid state."""
    with pytest.raises(ValueError):
        controller.control_buzzer("invalid_state")
    
    mock_serial_manager.reset_mock()
    with pytest.raises(ValueError):
        controller.control_buzzer("INVALID_STATE")
    mock_serial_manager.write.assert_not_called()

def test_check_status_healthy(controller, mock_serial_manager):
    """Test check_status when connection is healthy."""
    mock_serial_manager.is_connected.return_value = True
    status = controller.check_status()
    
    assert status["status"] == "healthy"
    assert status["connected"] is True
    
    mock_serial_manager.connect.assert_not_called()

def test_check_status_reconnect_success(controller, mock_serial_manager):
    """Test check_status attempts reconnect when disconnected."""
    mock_serial_manager.is_connected.return_value = False
    mock_serial_manager.connect.return_value = True
    
    status = controller.check_status()
    
    mock_serial_manager.connect.assert_called_once()
    assert status["status"] == "healthy"
    assert status["connected"] is True

def test_check_status_reconnect_failure(controller, mock_serial_manager):
    """Test check_status when reconnect fails."""
    mock_serial_manager.is_connected.return_value = False
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

def test_protocol_consumer_b(controller, mock_serial_manager):
    """Test switching ports using Consumer B protocol."""
    controller.update_config(protocol="consumer_b")
    
    controller.switch_port(1)
    mock_serial_manager.write.assert_called_with(ConsumerBCommands.SWITCH_PORT_1)

def test_terminator_lf(controller, mock_serial_manager):
    """Test using LF terminator."""
    controller.update_config(terminator="lf")
    assert controller.current_terminator == "lf"
    
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
    # Verify dynamic packet construction
    expected = ProtocolHandler.build_packet(HDC202X24Commands.CMD_SWITCH_PORT, [0x00, 0x00])
    mock_serial_manager.write.assert_called_with(expected)
    
    controller.control_buzzer("on")
    expected_bz = ProtocolHandler.build_packet(HDC202X24Commands.CMD_BUZZER, [0x00, 0x01])
    mock_serial_manager.write.assert_called_with(expected_bz)

def test_send_query(controller, mock_serial_manager):
    """Test sending a query and reading a response via async monitor."""
    controller.update_config(protocol="hdc202_x24")
    
    # Packet: AA BB 84 01 00 EA (Buzzer query response)
    # CMD 84, LEN 01, DATA 00.
    # Note: Our parser uses byte 3 as Len if valid.
    # AA BB 84 01 00 EA -> Valid.
    response_packet = b'\xAA\xBB\x84\x01\x00\xEA'
    
    # Mock read_existing to return nothing first, then the packet
    # This simulates data arriving after a short delay
    mock_serial_manager.read_existing.side_effect = [b'', response_packet, b'', b'']
    
    # We call send_query. It will loop waiting for future.
    # The monitor thread running in background will call read_existing, get the packet, and complete future.
    response = controller.send_query("buzzer")
    
    assert response == "AA BB 84 01 00 EA"
    
    # Check write called with correct query command
    expected_query = ProtocolHandler.build_packet(HDC202X24Commands.CMD_QUERY_BUZZER, [0x00, 0xFF]) # Payload 00 FF
    # Or whatever logic I put in send_query. I put 00 FF for buzzer.
    mock_serial_manager.write.assert_called_with(expected_query)

def test_send_query_unsupported(controller):
    """Test sending an unsupported query."""
    controller.update_config(protocol="enterprise")
    
    with pytest.raises(NotImplementedError):
        controller.send_query("buzzer")

def test_init_enforces_9600_baud(mock_serial_manager):
    """Test that initializing ControllerService forces baudrate to 9600."""
    mock_serial_manager.baudrate = 115200
    mock_serial_manager.is_connected.return_value = True
    
    # Initialize controller
    c = ControllerService(mock_serial_manager)
    c._shutdown_event.set() # Cleanup
    
    assert mock_serial_manager.baudrate == 9600
    mock_serial_manager.reconnect.assert_called_once()
