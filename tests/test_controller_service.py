import time
import pytest
from unittest.mock import MagicMock, patch
from concurrent.futures import Future
from src.controller_service import ControllerService
from src.serial_manager import SerialManager
from src.constants import EnterpriseCommands, ConsumerACommands, ConsumerBCommands, Protocol, HDC202X24Commands, SV04Commands
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

def test_init_does_not_override_baudrate(mock_serial_manager):
    """Test that ControllerService preserves whatever baudrate the caller set."""
    mock_serial_manager.baudrate = 115200
    mock_serial_manager.is_connected.return_value = True

    c = ControllerService(mock_serial_manager)
    c._shutdown_event.set()

    # baudrate must not be overridden — the SV04 needs 115200, not 9600
    assert mock_serial_manager.baudrate == 115200
    mock_serial_manager.reconnect.assert_not_called()


# --- SV04 USB switch -------------------------------------------------------

def wire_sv04_echo(mock_serial_manager):
    """
    Makes the mock behave like a real SV04, which echoes every command back.

    Without this the monitor thread never sees an echo and switch_port raises,
    which is the correct behaviour for a dead link but not what most tests want.
    """
    pending: list[bytes] = []

    def _write(data):
        pending.append(bytes(data))
        return len(data)

    def _read_existing():
        return pending.pop(0) if pending else b''

    mock_serial_manager.write.side_effect = _write
    mock_serial_manager.read_existing.side_effect = _read_existing


@pytest.mark.parametrize("port_id,expected", [
    (1, b'\xAA\x00\x56'),
    (2, b'\xAA\x01\x55'),
    (3, b'\xAA\x02\x54'),
    (4, b'\xAA\x03\x53'),
])
def test_sv04_switch_matches_vendor_table(controller, mock_serial_manager, port_id, expected):
    """Generated SV04 packets must match the vendor command table byte-for-byte."""
    wire_sv04_echo(mock_serial_manager)
    controller.update_config(protocol="sv04")
    controller.switch_port(port_id)
    mock_serial_manager.write.assert_called_with(expected)
    assert getattr(SV04Commands, f"SWITCH_PORT_{port_id}") == expected


def test_sv04_switch_confirmed_by_echo(controller, mock_serial_manager):
    """A switch that is echoed back must succeed and set active_port."""
    wire_sv04_echo(mock_serial_manager)
    controller.update_config(protocol="sv04")
    controller.switch_port(3)
    assert controller.active_port == 3


def test_sv04_switch_raises_when_no_echo(controller, mock_serial_manager):
    """
    A silent switch must raise, not report success.

    This is the failure that mattered in practice: the SV04's RS232 controller
    latches up while USB switching keeps working, and the API happily returned
    200 for every command.
    """
    mock_serial_manager.read_existing.return_value = b''   # never echoes
    controller.update_config(protocol="sv04")

    with pytest.raises(ConnectionError, match="did not acknowledge"):
        controller.switch_port(2)

    # The command was still written; it just was not acknowledged.
    mock_serial_manager.write.assert_called_with(b'\xAA\x01\x55')
    assert controller.active_port is None


def test_sv04_refuses_to_send_at_wrong_baud(controller, mock_serial_manager):
    """
    Sending SV04 commands at the wrong baud must be refused, not attempted.

    Wrong-baud traffic arrives as framing garbage and latches up the switch's
    RS232 controller until it is power-cycled, so this guard protects the
    hardware rather than just reporting an error.
    """
    wire_sv04_echo(mock_serial_manager)
    controller.update_config(protocol="sv04", baudrate=9600)

    mock_serial_manager.write.reset_mock()
    with pytest.raises(ValueError, match="requires 115200"):
        controller.switch_port(1)
    mock_serial_manager.write.assert_not_called()


def test_sv04_no_echo_clears_pending_state(controller, mock_serial_manager):
    """A timed-out switch must not leave stale pending state behind."""
    mock_serial_manager.read_existing.return_value = b''
    controller.update_config(protocol="sv04")

    with pytest.raises(ConnectionError):
        controller.switch_port(2)
    assert controller._pending_echo is None

    # A subsequent successful switch must still work.
    wire_sv04_echo(mock_serial_manager)
    controller.switch_port(1)
    assert controller.active_port == 1


def test_sv04_packets_pass_validation():
    """Every SV04 packet must satisfy the sum-to-0x100 checksum rule."""
    for port_id in (1, 2, 3, 4):
        packet = ProtocolHandler.build_sv04_packet(port_id)
        assert ProtocolHandler.validate_sv04_packet(packet)
        assert sum(packet) == 0x100
        assert len(packet) == 3


@pytest.mark.parametrize("bad_port", [0, 5, 8, -1])
def test_sv04_rejects_out_of_range_inputs(controller, bad_port):
    """The SV04 has only 4 inputs; anything else must be rejected, not sent."""
    controller.update_config(protocol="sv04")
    with pytest.raises(ValueError):
        controller.switch_port(bad_port)


def test_sv04_selection_defaults_baudrate_to_115200(controller, mock_serial_manager):
    """Selecting sv04 without a baudrate must move the port to 115200."""
    mock_serial_manager.baudrate = 9600
    controller.update_config(protocol="sv04")
    assert mock_serial_manager.baudrate == SV04Commands.BAUDRATE
    mock_serial_manager.reconnect.assert_called_once()


def test_sv04_respects_explicit_baudrate(controller, mock_serial_manager):
    """An explicit baudrate alongside the protocol must win over the default."""
    mock_serial_manager.baudrate = 9600
    controller.update_config(protocol="sv04", baudrate=38400)
    assert mock_serial_manager.baudrate == 38400


def test_sv04_ignores_terminator(controller, mock_serial_manager):
    """A configured terminator must not be appended to a 3-byte SV04 frame."""
    wire_sv04_echo(mock_serial_manager)
    controller.update_config(protocol="sv04", terminator="crlf")
    controller.switch_port(2)
    sent = mock_serial_manager.write.call_args[0][0]
    assert sent == b'\xAA\x01\x55'
    assert not sent.endswith(b'\r\n')


def test_sv04_echo_updates_active_port(controller):
    """The switch echoes commands verbatim; the echo must set active_port."""
    controller.update_config(protocol="sv04")
    remainder = controller._consume_sv04_frames(b'\xAA\x02\x54')
    assert controller.active_port == 3
    assert remainder == b''


def test_sv04_echo_handles_multiple_frames(controller):
    """Back-to-back echoes must all be consumed, leaving active_port at the last."""
    controller.update_config(protocol="sv04")
    remainder = controller._consume_sv04_frames(b'\xAA\x00\x56\xAA\x03\x53')
    assert controller.active_port == 4
    assert remainder == b''


def test_sv04_echo_buffers_partial_frame(controller):
    """A partial frame must be retained until the rest arrives."""
    controller.update_config(protocol="sv04")
    remainder = controller._consume_sv04_frames(b'\xAA\x01')
    assert remainder == b'\xAA\x01'
    assert controller.active_port is None

    remainder = controller._consume_sv04_frames(remainder + b'\x55')
    assert remainder == b''
    assert controller.active_port == 2


def test_sv04_echo_resyncs_past_garbage(controller):
    """Leading garbage must be skipped to find a valid frame."""
    controller.update_config(protocol="sv04")
    remainder = controller._consume_sv04_frames(b'\xFE\x00\xAA\x01\x55')
    assert controller.active_port == 2
    assert remainder == b''


def test_sv04_echo_discards_bad_checksum(controller):
    """A frame with a wrong checksum must not move active_port."""
    controller.update_config(protocol="sv04")
    controller._consume_sv04_frames(b'\xAA\x01\x99')
    assert controller.active_port is None


def test_sv04_validator_rejects_corrupt_packets():
    """Bad header, bad checksum, or wrong length must all fail validation."""
    assert not ProtocolHandler.validate_sv04_packet(b'\xAB\x00\x56')      # bad header
    assert not ProtocolHandler.validate_sv04_packet(b'\xAA\x00\x57')      # bad checksum
    assert not ProtocolHandler.validate_sv04_packet(b'\xAA\x00')          # too short
    assert not ProtocolHandler.validate_sv04_packet(b'\xAA\x00\x56\x00')  # too long


# ──────────────────────────────────────────────────────────────────────────────
# Bug-1: AUTO port discovery must never permanently pin itself
# ──────────────────────────────────────────────────────────────────────────────

class TestAutoDiscovery:
    """
    SerialManager._port_spec stays 'AUTO' for the life of the process.
    connect() must re-run discovery on every call when _port_spec is 'AUTO',
    and must only update self.port after a successful open.
    """

    def test_auto_reruns_discovery_after_no_ports_found(self):
        """
        When AUTO finds no ports on the first call it must not pin anything;
        a later call that discovers a port must succeed and update self.port.
        """
        manager = SerialManager(port='AUTO')
        assert manager._port_spec == 'AUTO'

        # First attempt: nothing plugged in yet.
        with patch.object(SerialManager, 'list_available_ports', return_value=[]):
            result = manager.connect()

        assert result is False
        assert manager._port_spec == 'AUTO'  # spec not pinned
        assert manager.port == 'AUTO'        # nothing resolved yet

        # Second attempt: device has appeared.
        mock_serial = MagicMock()
        mock_serial.is_open = True
        with patch.object(SerialManager, 'list_available_ports',
                          return_value=['/dev/ttyUSB1']), \
             patch('serial.Serial', return_value=mock_serial):
            result = manager.connect()

        assert result is True
        assert manager.port == '/dev/ttyUSB1'
        assert manager._port_spec == 'AUTO'  # still AUTO — never pinned

    def test_auto_follows_device_after_re_enumeration(self):
        """
        When a device disconnects and re-enumerates at a different node,
        AUTO discovery must find the new path, not retry the stale one.
        """
        manager = SerialManager(port='AUTO')

        mock_usb0 = MagicMock()
        mock_usb0.is_open = True

        # First connect: device at USB0.
        with patch.object(SerialManager, 'list_available_ports',
                          return_value=['/dev/ttyUSB0']), \
             patch('serial.Serial', return_value=mock_usb0):
            assert manager.connect() is True
        assert manager.port == '/dev/ttyUSB0'

        # Device disconnects and re-enumerates at USB1.
        manager.disconnect()

        mock_usb1 = MagicMock()
        mock_usb1.is_open = True

        with patch.object(SerialManager, 'list_available_ports',
                          return_value=['/dev/ttyUSB1']), \
             patch('serial.Serial', return_value=mock_usb1):
            assert manager.connect() is True

        assert manager.port == '/dev/ttyUSB1'
        assert manager._port_spec == 'AUTO'

    def test_explicit_port_is_never_overridden_by_discovery(self):
        """
        An explicit SERIAL_PORT value must be used directly; discovery is
        never consulted and self.port must match the configured path.
        """
        manager = SerialManager(port='/dev/ttyUSB0')
        assert manager._port_spec == '/dev/ttyUSB0'

        mock_serial = MagicMock()
        mock_serial.is_open = True

        # list_available_ports would return a different path — must be ignored.
        with patch.object(SerialManager, 'list_available_ports',
                          return_value=['/dev/ttyUSB99']), \
             patch('serial.Serial', return_value=mock_serial) as mock_cls:
            assert manager.connect() is True

        # serial.Serial must have been called with the explicit path, not USB99.
        call_port = mock_cls.call_args[1].get('port') or mock_cls.call_args[0][0]
        assert call_port == '/dev/ttyUSB0'
        assert manager.port == '/dev/ttyUSB0'
        assert manager._port_spec == '/dev/ttyUSB0'

    def test_check_status_never_reports_auto_once_connected(self):
        """
        check_status() must return a real device path for 'port', not the
        literal string 'AUTO', once the port has been successfully opened.
        """
        manager = SerialManager(port='AUTO')

        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 0

        with patch.object(SerialManager, 'list_available_ports',
                          return_value=['/dev/ttyUSB0']), \
             patch('serial.Serial', return_value=mock_serial):
            manager.connect()

        c = ControllerService(manager)
        try:
            status = c.check_status()
            assert status['port'] != 'AUTO', (
                "check_status() returned 'AUTO' for port — "
                "self.port was not updated on successful connect"
            )
            assert status['port'] == '/dev/ttyUSB0'
        finally:
            c._shutdown_event.set()
            c._monitor_thread.join(timeout=1.0)


# ──────────────────────────────────────────────────────────────────────────────
# Bug-2: background reconnect must not fire while a command is in-flight
# ──────────────────────────────────────────────────────────────────────────────

class TestBackgroundReconnect:
    """
    The _monitor_serial loop must skip reconnect attempts while
    _pending_query or _pending_echo is set (AGENTS.md rule: never reset
    the serial port while a command is in-flight).
    """

    def test_reconnect_skipped_while_pending_query(
        self, controller, mock_serial_manager
    ):
        """connect() must not be called while _pending_query is set."""
        # Disable the 5-second throttle so every iteration would attempt
        # a reconnect if the guard were absent.
        controller._reconnect_interval = 0.0

        future: Future = Future()
        with controller._query_lock:
            controller._pending_query = {'cmd_id': 0x84, 'future': future}

        # Now make the port look disconnected so the reconnect branch is entered.
        mock_serial_manager.is_connected.return_value = False

        # Allow several monitor-thread iterations to run (50 ms each).
        time.sleep(0.25)

        mock_serial_manager.connect.assert_not_called()

        # Cleanup: clear the pending state so the thread can exit cleanly.
        future.cancel()
        with controller._query_lock:
            controller._pending_query = None

    def test_reconnect_skipped_while_pending_echo(
        self, controller, mock_serial_manager
    ):
        """connect() must not be called while _pending_echo is set."""
        controller._reconnect_interval = 0.0

        future: Future = Future()
        with controller._query_lock:
            controller._pending_echo = {'frame': b'\xAA\x00\x56', 'future': future}

        mock_serial_manager.is_connected.return_value = False

        time.sleep(0.25)

        mock_serial_manager.connect.assert_not_called()

        future.cancel()
        with controller._query_lock:
            controller._pending_echo = None
