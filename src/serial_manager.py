import serial
import os
import glob
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class SerialManager:
    """
    Hardware Abstraction Layer (HAL) for serial communication.
    Handles connection management and raw byte transmission.
    """
    def __init__(self, port: Optional[str] = None, baudrate: Optional[int] = None, timeout: float = 1.0):
        self.port = port or os.getenv('SERIAL_PORT', 'AUTO')
        self.baudrate = baudrate or int(os.getenv('BAUD_RATE', 9600))
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None

    @staticmethod
    def list_available_ports() -> List[str]:
        """Lists available serial ports on the system."""
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        return sorted(ports)

    def connect(self) -> bool:
        """
        Opens the serial connection.
        If port is 'AUTO', attempts to find and connect to the first available port.
        Returns True if connected successfully, False otherwise.
        Does not raise exception on failure.
        """
        if self.connection and self.connection.is_open:
            return True

        target_port = self.port

        if target_port == 'AUTO':
            available_ports = self.list_available_ports()
            if not available_ports:
                logger.error("AUTO mode: No serial ports found (ttyUSB* or ttyACM*)")
                return False
            logger.info(f"AUTO mode: Found ports {available_ports}. Trying first one.")
            target_port = available_ports[0]
            # Update self.port so we know which one we connected to
            self.port = target_port

        try:
            self.connection = serial.Serial(
                port=target_port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            logger.info(f"Connected to serial port {self.port} (8-N-1)")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to serial port {self.port}: {e}")
            self.connection = None
            return False

    def disconnect(self) -> None:
        """Closes the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info(f"Disconnected from serial port {self.port}")
        self.connection = None

    def reconnect(self) -> bool:
        """Forces a disconnection and attempts to connect again."""
        self.disconnect()
        return self.connect()

    def write(self, data: bytes) -> None:
        """
        Writes bytes to the serial port.
        Raises serial.SerialException if write fails.
        """
        if not self.connection or not self.connection.is_open:
            # Attempt to reconnect
            if not self.connect():
                 raise serial.SerialException("Serial port is not open")

        try:
            self.connection.write(data)
            self.connection.flush()
            logger.debug(f"Wrote to serial: {data!r}")
        except serial.SerialException as e:
            logger.error(f"Failed to write to serial port: {e}")
            # Invalidate connection on failure
            self.disconnect()
            raise

    def is_connected(self) -> bool:
        """Checks if the serial connection is currently open."""
        return self.connection is not None and self.connection.is_open

    @property
    def bytes_available(self) -> int:
        """Returns the number of bytes currently waiting in the input buffer."""
        if self.connection and self.connection.is_open:
            return self.connection.in_waiting
        return 0

    def read_existing(self) -> bytes:
        """
        Reads all currently available bytes from the serial port.
        Returns empty bytes if no data is available.
        """
        if self.bytes_available > 0:
            return self.read(self.bytes_available)
        return b""

    def reset_input_buffer(self) -> None:
        """Clears the input buffer."""
        if self.connection and self.connection.is_open:
            self.connection.reset_input_buffer()

    def read(self, size: int = 64) -> bytes:
        """
        Reads up to size bytes from serial port.
        Uses the configured timeout.
        """
        if not self.connection or not self.connection.is_open:
             raise serial.SerialException("Serial port is not open")
        
        try:
            data = self.connection.read(size)
            if data:
                logger.debug(f"Read from serial: {data.hex(' ').upper()}")
            return data
        except serial.SerialException as e:
            logger.error(f"Failed to read from serial port: {e}")
            self.disconnect()
            raise
