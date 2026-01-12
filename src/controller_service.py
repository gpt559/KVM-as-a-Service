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
        self.current_protocol = Protocol.CONSUMER_A
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
