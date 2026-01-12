import serial
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SerialManager:
    """
    Hardware Abstraction Layer (HAL) for serial communication.
    Handles connection management and raw byte transmission.
    """
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None

    def connect(self) -> bool:
        """
        Opens the serial connection.
        Returns True if connected successfully, False otherwise.
        Does not raise exception on failure.
        """
        if self.connection and self.connection.is_open:
            return True

        try:
            self.connection = serial.Serial(
                port=self.port,
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
            logger.debug(f"Wrote to serial: {data!r}")
        except serial.SerialException as e:
            logger.error(f"Failed to write to serial port: {e}")
            # Invalidate connection on failure
            self.disconnect()
            raise

    def is_connected(self) -> bool:
        """Checks if the serial connection is currently open."""
        return self.connection is not None and self.connection.is_open

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
