import threading
import logging
from typing import Literal, Optional
from src.serial_manager import SerialManager
from src.constants import Protocol, PROTOCOL_MAP

logger = logging.getLogger(__name__)

class ControllerService:
    """
    Business logic controller for the KVM service.
    Manages serial connection and ensures thread-safe access to hardware.
    """
    def __init__(self, serial_manager: SerialManager):
        self.serial_manager = serial_manager
        self._lock = threading.Lock()
        self.current_protocol = Protocol.HDC202_X24
        self.current_terminator: Literal["none", "cr", "lf", "crlf"] = "none"
        # Initialize serial with correct baudrate
        if self.serial_manager.baudrate != 115200:
             self.serial_manager.baudrate = 115200
             if self.serial_manager.is_connected():
                 self.serial_manager.reconnect()

    def update_config(self, protocol: Optional[str] = None, baudrate: Optional[int] = None, terminator: Optional[str] = None) -> None:
        """
        Updates the controller configuration.
        """
        if protocol:
            try:
                self.current_protocol = Protocol(protocol)
                logger.info(f"Protocol updated to: {self.current_protocol}")
            except ValueError:
                raise ValueError(f"Invalid protocol: {protocol}")

        if terminator:
            if terminator not in ["none", "cr", "lf", "crlf"]:
                raise ValueError(f"Invalid terminator: {terminator}")
            self.current_terminator = terminator
            logger.info(f"Terminator updated to: {self.current_terminator}")

        if baudrate:
            if baudrate not in [9600, 38400, 115200]:
                raise ValueError(f"Invalid baudrate: {baudrate}")
            
            with self._lock:
                # Only reconnect if baudrate actually changes
                if self.serial_manager.baudrate != baudrate:
                    self.serial_manager.baudrate = baudrate
                    if self.serial_manager.is_connected():
                        logger.info(f"Updating baudrate to {baudrate}, reconnecting...")
                        if not self.serial_manager.reconnect():
                            raise Exception("Failed to reconnect after baudrate change")
                    else:
                        logger.info(f"Baudrate updated to {baudrate} (not currently connected)")

    def _get_commands(self):
        return PROTOCOL_MAP[self.current_protocol]

    def _apply_terminator(self, command: bytes) -> bytes:
        """Appends the configured terminator to the command bytes."""
        if self.current_terminator == "cr":
            return command + b'\r'
        elif self.current_terminator == "lf":
            return command + b'\n'
        elif self.current_terminator == "crlf":
            return command + b'\r\n'
        return command

    def switch_port(self, port_id: int) -> None:
        """
        Switches the KVM to the specified port.
        
        Args:
            port_id: The target port number (1-8).
            
        Raises:
            ValueError: If port_id is invalid.
            Exception: If hardware communication fails.
        """
        if not (1 <= port_id <= 8):
            raise ValueError(f"Invalid port ID: {port_id}. Must be between 1 and 8.")

        commands = self._get_commands()
        command_name = f"SWITCH_PORT_{port_id}"
        
        if not hasattr(commands, command_name):
            raise NotImplementedError(f"Port {port_id} not supported by protocol {self.current_protocol}")

        command_bytes = getattr(commands, command_name)

        with self._lock:
            final_command = self._apply_terminator(command_bytes)
            logger.info(f"Switching to port {port_id} using {self.current_protocol} (Terminator: {self.current_terminator})")
            self.serial_manager.write(final_command)

    def control_buzzer(self, state: Literal["on", "off"]) -> None:
        """
        Controls the KVM buzzer.
        
        Args:
            state: "on" or "off".
        """
        commands = self._get_commands()
        
        if state == "on":
            if not hasattr(commands, 'BUZZER_ON'):
                 raise NotImplementedError(f"Buzzer control not supported by protocol {self.current_protocol}")
            command_bytes = commands.BUZZER_ON
        elif state == "off":
            if not hasattr(commands, 'BUZZER_OFF'):
                 raise NotImplementedError(f"Buzzer control not supported by protocol {self.current_protocol}")
            command_bytes = commands.BUZZER_OFF
        else:
             raise ValueError("Invalid buzzer state. Must be 'on' or 'off'.")

        with self._lock:
            final_command = self._apply_terminator(command_bytes)
            logger.info(f"Turning buzzer {state} using {self.current_protocol} (Terminator: {self.current_terminator})")
            self.serial_manager.write(final_command)

    def _execute_simple_command(self, command_key: str, description: str) -> None:
        """Helper to look up and execute a command by key."""
        commands = self._get_commands()
        if not hasattr(commands, command_key):
             raise NotImplementedError(f"{description} not supported by protocol {self.current_protocol}")
        
        command_bytes = getattr(commands, command_key)
        with self._lock:
            final_command = self._apply_terminator(command_bytes)
            logger.info(f"Executing {description} ({command_key}) using {self.current_protocol}")
            self.serial_manager.write(final_command)

    def set_light_mode(self, mode: str) -> None:
        key = f"LIGHT_{mode.upper()}"
        self._execute_simple_command(key, f"Light Mode {mode}")

    def set_fan_mode(self, mode: str) -> None:
        key = f"FAN_{mode.upper()}"
        self._execute_simple_command(key, f"Fan Mode {mode}")

    def set_audio_source(self, port: int) -> None:
        key = f"AUDIO_PC{port}"
        self._execute_simple_command(key, f"Audio Source PC{port}")

    def set_audio_follow(self, enabled: bool) -> None:
        key = "AUDIO_FOLLOW_ON" if enabled else "AUDIO_FOLLOW_OFF"
        self._execute_simple_command(key, f"Audio Follow {'On' if enabled else 'Off'}")

    def set_network_power(self, port: int, enabled: bool) -> None:
        # Note: Current constants: NET_PCx_ON, NET_PCx_OFF
        state = "ON" if enabled else "OFF"
        key = f"NET_PC{port}_{state}"
        self._execute_simple_command(key, f"Network PC{port} {state}")

    def set_usb_focus(self, target: str) -> None:
        # target: pc1, pc2, next
        key = f"USB_FOCUS_{target.upper()}"
        self._execute_simple_command(key, f"USB Focus {target}")

    def set_feature_state(self, feature_prefix: str, enabled: bool, description: str) -> None:
        # Generic for toggle features like USB_COMPAT, MOUSE_MIDDLE, AUTODETECT, AUTOSCAN
        suffix = "ON" if enabled else "OFF"
        key = f"{feature_prefix}_{suffix}"
        self._execute_simple_command(key, f"{description} {'On' if enabled else 'Off'}")

    def send_query(self, query_name: str) -> str:
        """
        Sends a query command and returns the response as a hex string.
        """
        key = f"QUERY_{query_name.upper()}"
        commands = self._get_commands()
        
        if not hasattr(commands, key):
             raise NotImplementedError(f"Query {query_name} not supported by protocol {self.current_protocol}")
        
        command_bytes = getattr(commands, key)
        
        with self._lock:
            # Flush input buffer before sending to avoid reading stale data
            self.serial_manager.reset_input_buffer()
                
            final_command = self._apply_terminator(command_bytes)
            logger.info(f"Sending query {query_name} using {self.current_protocol}")
            self.serial_manager.write(final_command)
            
            # Read response
            response = self.serial_manager.read(128) # Read up to 128 bytes
            return response.hex(' ').upper()

    def run_all_queries(self) -> list[dict]:
        """
        Runs all available query commands for the current protocol.
        
        Returns:
            list[dict]: List of results with command name and response.
        """
        commands = self._get_commands()
        query_results = []
        
        # Find all attributes starting with QUERY_
        query_keys = [attr for attr in dir(commands) if attr.startswith("QUERY_")]
        
        for key in query_keys:
            query_name = key.replace("QUERY_", "").lower()
            try:
                response = self.send_query(query_name)
                query_results.append({
                    "command": query_name,
                    "response": response,
                    "status": "success"
                })
            except Exception as e:
                query_results.append({
                    "command": query_name,
                    "response": str(e),
                    "status": "error"
                })
                
        return query_results

    def check_status(self) -> dict:
        """
        Checks the service health and connection status.
        
        Returns:
            dict: Status information.
        """
        is_connected = self.serial_manager.is_connected()
        status = "healthy" if is_connected else "degraded"
        
        # If not connected, try to connect (self-healing)
        if not is_connected:
            if self.serial_manager.connect():
                is_connected = True
                status = "healthy"
            else:
                status = "unhealthy"

        return {
            "status": status,
            "connected": is_connected,
            "port": self.serial_manager.port,
            "baudrate": self.serial_manager.baudrate,
            "protocol": self.current_protocol,
            "terminator": self.current_terminator
        }
