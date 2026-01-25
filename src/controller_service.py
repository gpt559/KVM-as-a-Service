import threading
import logging
import time
from concurrent.futures import Future, TimeoutError
from typing import Literal, Optional, Dict, Any, cast

from src.serial_manager import SerialManager
from src.protocol_handler import ProtocolHandler
from src.constants import Protocol, PROTOCOL_MAP, HDC202X24Commands

logger = logging.getLogger(__name__)

class ControllerService:
    """
    Business logic controller for the KVM service.
    Manages serial connection and ensures thread-safe access to hardware.
    """
    def __init__(self, serial_manager: SerialManager):
        self.serial_manager = serial_manager
        self._lock = threading.Lock() # Guards serial writes
        self.current_protocol = Protocol.HDC202_X24
        self.current_terminator: Literal["none", "cr", "lf", "crlf"] = "none"
        self.active_port: Optional[int] = None
        
        # Async Query Management
        self._query_lock = threading.Lock() # Guards _pending_query
        self._pending_query: Optional[Dict[str, Any]] = None # {'cmd_id': int, 'future': Future}
        self._shutdown_event = threading.Event()

        # Initialize serial with correct baudrate
        if self.serial_manager.baudrate != 9600:
             self.serial_manager.baudrate = 9600
             if self.serial_manager.is_connected():
                 self.serial_manager.reconnect()

        # Start background monitor thread
        self._monitor_thread = threading.Thread(target=self._monitor_serial, daemon=True)
        self._monitor_thread.start()

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
            self.current_terminator = cast(Literal["none", "cr", "lf", "crlf"], terminator)
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

    def _log_serial_event(self, direction: str, data: bytes):
        """
        Logs detailed interaction info.
        """
        msg = [
            f"\n--- Serial Interaction ({direction}) ---",
            f"Baud: {self.serial_manager.baudrate}",
            f"Protocol: {self.current_protocol}",
            f"Message (Bytes): {data}",
            f"Hex Output: {data.hex(' ').upper()}",
            "---------------------------------------"
        ]
        log_block = "\n".join(msg)
        logger.info(log_block)
        print(log_block)

    def _monitor_serial(self):
        """
        Background thread to monitor serial port for incoming data.
        Parses async feedback from KVM and handles query responses.
        """
        buffer = b""
        
        while not self._shutdown_event.is_set():
            try:
                # 1. Read available data (Non-blocking)
                new_data = self.serial_manager.read_existing()
                if new_data:
                    self._log_serial_event("RECEIVED (Raw)", new_data)
                    buffer += new_data

                # 2. Parse Loop
                while True:
                    # Only attempt parsing if we have enough data
                    if len(buffer) < 4:
                        break

                    packet, remaining_buffer = ProtocolHandler.try_parse_packet(buffer)
                    
                    if packet:
                        # Valid packet found!
                        self._log_serial_event("PACKET PARSED", packet)
                        self._handle_incoming_packet(packet)
                        buffer = remaining_buffer
                    else:
                        # No valid packet found yet, or waiting for more data
                        # ProtocolHandler.try_parse_packet handles garbage collection (skips until header)
                        # So we just update buffer and break to wait for more data
                        buffer = remaining_buffer
                        break
                
                # Sleep to prevent CPU spin
                time.sleep(0.05)
                                        
            except Exception as e:
                logger.error(f"Error in serial monitor: {e}")
                time.sleep(1) # Backoff on error

    def _handle_incoming_packet(self, packet: bytes):
        """
        Dispatches a parsed packet to either a pending query or an async event handler.
        """
        cmd_id = packet[2] if len(packet) > 2 else None
        
        # 1. Check Pending Queries
        with self._query_lock:
            if self._pending_query:
                # Check if this packet matches the expected response
                # For HDC202, Query Response often echoes the Query CMD
                if self._pending_query['cmd_id'] == cmd_id:
                    self._pending_query['future'].set_result(packet)
                    self._pending_query = None
                    return

        # 2. Handle Async Events
        # HDC202 Async Status Report is usually CMD 0x82 (Keyboard/Mouse Focus)
        # Packet: AA BB 82 [LEN] [DATA] [CS]
        if cmd_id == 0x82: 
            # Example: AA BB 82 01 01 E9 (Port 2 selected)
            # Payload is byte 4 (index 4)
            if len(packet) >= 5:
                port_idx = packet[4]
                new_port = port_idx + 1
                if self.active_port != new_port:
                    self.active_port = new_port
                    logger.info(f"KVM Feedback: Switched to Port {self.active_port}")

    def _send_command_bytes(self, command_bytes: bytes):
        with self._lock:
            final_command = self._apply_terminator(command_bytes)
            self._log_serial_event("SENT", final_command)
            self.serial_manager.write(final_command)

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
        if not (1 <= port_id <= 8):
            raise ValueError(f"Invalid port ID: {port_id}. Must be between 1 and 8.")

        if self.current_protocol == Protocol.HDC202_X24:
            # HDC202: AA BB 03 00 [Port-1] CS
            cmd_id = HDC202X24Commands.CMD_SWITCH_PORT
            payload = [0x00, port_id - 1]
            packet = ProtocolHandler.build_packet(cmd_id, payload)
            self._send_command_bytes(packet)
        else:
            # Legacy Fallback
            commands = self._get_commands()
            command_name = f"SWITCH_PORT_{port_id}"
            if not hasattr(commands, command_name):
                raise NotImplementedError(f"Port {port_id} not supported")
            self._send_command_bytes(getattr(commands, command_name))

    def control_buzzer(self, state: Literal["on", "off"]) -> None:
        if state not in ["on", "off"]:
             raise ValueError("Invalid buzzer state. Must be 'on' or 'off'.")

        if self.current_protocol == Protocol.HDC202_X24:
            cmd_id = HDC202X24Commands.CMD_BUZZER
            # On: 00 01, Off: 00 00
            payload = [0x00, 0x01] if state == "on" else [0x00, 0x00]
            packet = ProtocolHandler.build_packet(cmd_id, payload)
            self._send_command_bytes(packet)
        else:
            commands = self._get_commands()
            cmd_name = f"BUZZER_{state.upper()}"
            if not hasattr(commands, cmd_name):
                raise NotImplementedError("Buzzer control not supported")
            self._send_command_bytes(getattr(commands, cmd_name))

    def _execute_simple_command(self, command_key: str, description: str) -> None:
        """Legacy helper for simple byte commands."""
        commands = self._get_commands()
        if not hasattr(commands, command_key):
             raise NotImplementedError(f"{description} not supported")
        
        command_bytes = getattr(commands, command_key)
        self._send_command_bytes(command_bytes)

    # Note: For methods below, I am leaving legacy implementation for non-HDC202 protocols
    # but strictly speaking, I should refactor all to use the dynamic builder if I want "Best".
    # For now, I will update the ones clearly mapped in HDC202 constants.

    def set_light_mode(self, mode: str) -> None:
        # Modes: OFF, BASIC, FLOW, BREATHING
        # HDC202: CMD 05, Payload 02 [Mode]
        if self.current_protocol == Protocol.HDC202_X24:
            mode_map = {"OFF": 0x00, "BASIC": 0x01, "FLOW": 0x02, "BREATHING": 0x03}
            val = mode_map.get(mode.upper())
            if val is not None:
                packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_LIGHT, [0x02, val])
                self._send_command_bytes(packet)
                return
        
        # Legacy
        self._execute_simple_command(f"LIGHT_{mode.upper()}", f"Light Mode {mode}")

    def set_fan_mode(self, mode: str) -> None:
        # Modes: OFF, AUTO, LOW, HIGH
        if self.current_protocol == Protocol.HDC202_X24:
            mode_map = {"OFF": 0x00, "AUTO": 0x01, "LOW": 0x02, "HIGH": 0x03}
            val = mode_map.get(mode.upper())
            if val is not None:
                packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_FAN, [0x00, val])
                self._send_command_bytes(packet)
                return

        self._execute_simple_command(f"FAN_{mode.upper()}", f"Fan Mode {mode}")

    def set_audio_source(self, port: int) -> None:
        if self.current_protocol == Protocol.HDC202_X24:
            # CMD 0D, Payload 00 [Port-1]
            packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_AUDIO_CHANNEL, [0x00, port - 1])
            self._send_command_bytes(packet)
            return

        key = f"AUDIO_PC{port}"
        self._execute_simple_command(key, f"Audio Source PC{port}")

    def set_audio_follow(self, enabled: bool) -> None:
        if self.current_protocol == Protocol.HDC202_X24:
            # CMD 0C, Payload 00 [1/0]
            val = 0x01 if enabled else 0x00
            packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_AUDIO_FOLLOW, [0x00, val])
            self._send_command_bytes(packet)
            return

        key = "AUDIO_FOLLOW_ON" if enabled else "AUDIO_FOLLOW_OFF"
        self._execute_simple_command(key, f"Audio Follow {'On' if enabled else 'Off'}")

    def set_network_power(self, port: int, enabled: bool) -> None:
        if self.current_protocol == Protocol.HDC202_X24:
             # CMD 09. Payload [00] [val]. 
             # CSV: PC1 ON: 00 0F. PC1 OFF: 00 0E.
             # PC2 ON: 00 0F. PC2 OFF: 00 0D.
             # This is weird. The values are unique per port?
             # I'll stick to legacy lookup for this one as logic is complex/undocumented fully.
             pass
             
        # Legacy
        state = "ON" if enabled else "OFF"
        key = f"NET_PC{port}_{state}"
        self._execute_simple_command(key, f"Network PC{port} {state}")

    def set_usb_focus(self, target: str) -> None:
        if self.current_protocol == Protocol.HDC202_X24:
             # CMD 07. Payload 00 [Port-1] or FF for Next?
             # CSV: PC1: 00 00. PC2: 00 01. Next: FF 00.
             if target.upper() == "NEXT":
                 packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_USB_FOCUS, [0xFF, 0x00])
             else:
                 # assume pcX
                 try:
                     port = int(target.replace("pc", ""))
                     packet = ProtocolHandler.build_packet(HDC202X24Commands.CMD_USB_FOCUS, [0x00, port - 1])
                 except Exception:
                     logger.error(f"Invalid USB focus target: {target}")
                     return
             self._send_command_bytes(packet)
             return

        key = f"USB_FOCUS_{target.upper()}"
        self._execute_simple_command(key, f"USB Focus {target}")

    def set_feature_state(self, feature_prefix: str, enabled: bool, description: str) -> None:
        # Mapping generic features to HDC202 commands
        if self.current_protocol == Protocol.HDC202_X24:
            cmd_map = {
                "USB_COMPAT": HDC202X24Commands.CMD_USB_COMPAT,
                "MOUSE_MIDDLE": HDC202X24Commands.CMD_MOUSE_MIDDLE,
                # "AUTODETECT": ...
            }
            if feature_prefix in cmd_map:
                cmd_id = cmd_map[feature_prefix]
                val = 0x01 if enabled else 0x00
                packet = ProtocolHandler.build_packet(cmd_id, [0x00, val])
                self._send_command_bytes(packet)
                return

        suffix = "ON" if enabled else "OFF"
        key = f"{feature_prefix}_{suffix}"
        self._execute_simple_command(key, f"{description} {'On' if enabled else 'Off'}")

    def send_query(self, query_name: str) -> str:
        """
        Sends a query command and returns the response as a hex string.
        Thread-safe and async-aware.
        """
        if self.current_protocol == Protocol.HDC202_X24:
             # Look up Command ID
             key = f"CMD_QUERY_{query_name.upper()}"
             if not hasattr(HDC202X24Commands, key):
                 raise NotImplementedError(f"Query {query_name} not supported")
             
             cmd_id = getattr(HDC202X24Commands, key)
             
             # Determine Payload
             # Most queries use 00 FF, but some 00 00?
             # CSV: Monitor Count (81) -> 00 00. Others -> 00 FF.
             payload = [0x00, 0xFF]
             if cmd_id == HDC202X24Commands.CMD_QUERY_MONITOR_COUNT:
                 payload = [0x00, 0x00]
                 
             packet = ProtocolHandler.build_packet(cmd_id, payload)
             
             future = Future()
             with self._query_lock:
                 self._pending_query = {'cmd_id': cmd_id, 'future': future}
             
             try:
                 self._send_command_bytes(packet)
                 # Wait for response (non-blocking to other threads, but blocking this caller)
                 result_packet = future.result(timeout=2.0)
                 return result_packet.hex(' ').upper()
             except TimeoutError:
                 logger.error(f"Query {query_name} timed out")
                 with self._query_lock:
                     # Clear pending if it's still us
                     if self._pending_query and self._pending_query['cmd_id'] == cmd_id:
                         self._pending_query = None
                 raise
             except Exception as e:
                 logger.error(f"Query {query_name} failed: {e}")
                 raise

        else:
             # Legacy (Blocking)
             return self._legacy_send_query(query_name)

    def _legacy_send_query(self, query_name: str) -> str:
        key = f"QUERY_{query_name.upper()}"
        commands = self._get_commands()
        if not hasattr(commands, key):
             raise NotImplementedError(f"Query {query_name} not supported")
        command_bytes = getattr(commands, key)
        with self._lock:
            self.serial_manager.reset_input_buffer()
            final_command = self._apply_terminator(command_bytes)
            self._log_serial_event("SENT", final_command)
            self.serial_manager.write(final_command)
            response = self.serial_manager.read(128)
            self._log_serial_event("RECEIVED", response)
            return response.hex(' ').upper()

    def run_all_queries(self) -> list[dict]:
        commands = self._get_commands()
        query_results = []
        
        # Use introspection to find queries
        # For HDC202, we look at CMD_QUERY_...
        if self.current_protocol == Protocol.HDC202_X24:
            query_keys = [attr for attr in dir(HDC202X24Commands) if attr.startswith("CMD_QUERY_")]
            for key in query_keys:
                query_name = key.replace("CMD_QUERY_", "").lower()
                try:
                    response = self.send_query(query_name)
                    query_results.append({"command": query_name, "response": response, "status": "success"})
                except Exception as e:
                    query_results.append({"command": query_name, "response": str(e), "status": "error"})
        else:
            # Legacy
            query_keys = [attr for attr in dir(commands) if attr.startswith("QUERY_")]
            for key in query_keys:
                query_name = key.replace("QUERY_", "").lower()
                try:
                    response = self.send_query(query_name)
                    query_results.append({"command": query_name, "response": response, "status": "success"})
                except Exception as e:
                     query_results.append({"command": query_name, "response": str(e), "status": "error"})
                     
        return query_results

    def check_status(self) -> dict:
        is_connected = self.serial_manager.is_connected()
        status = "healthy" if is_connected else "degraded"
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
            "terminator": self.current_terminator,
            "active_port": self.active_port,
            "available_ports": self.serial_manager.list_available_ports()
        }
