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

    HARDWARE NOTE: Two device families are supported; their electrical
    requirements are incompatible — use the wrong adapter and you risk
    damaging the hardware.

    TESmart KVM switches — 3.5mm service port, 3.3 V TTL logic.
      Do NOT connect RS-232 (+/-12 V) hardware to these ports; the
      over-voltage will damage the KVM. Use a TTL-level serial adapter.
      Pinout: Pin 3 (TX), Pin 2 (RX), Pin 1 (GND).

    SV04 USB peripheral switch — DB9, standard RS-232 levels, 115200 baud.
      An RS-232 adapter (e.g. an FT232R-based board with MAX3232 level
      conversion) is the correct and verified cable for this device.
      A bare TTL adapter will not produce valid RS-232 voltage swings.
    """
    def __init__(self, port: Optional[str] = None, baudrate: Optional[int] = None, timeout: float = 1.0):
        # _port_spec is the immutable configured value ('AUTO' or an explicit
        # device path).  connect() consults it to decide whether to re-run
        # discovery on each call.
        self._port_spec: str = port or os.getenv('SERIAL_PORT', 'AUTO')
        # self.port is the resolved device path reported by check_status() and
        # logged at startup.  It is updated to the real path only after a
        # successful open, so the API never reports the literal string 'AUTO'
        # for a connected port.
        self.port: str = self._port_spec
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
        If _port_spec is 'AUTO', runs port discovery on every call so that a
        device that re-enumerates at a different node (e.g. after a USB glitch)
        is found without requiring a container restart.
        Returns True if connected successfully, False otherwise.
        Does not raise exception on failure.
        """
        if self.connection and self.connection.is_open:
            return True

        if self._port_spec == 'AUTO':
            available_ports = self.list_available_ports()
            if not available_ports:
                logger.error("AUTO mode: No serial ports found (ttyUSB* or ttyACM*)")
                return False
            logger.info(f"AUTO mode: Found ports {available_ports}. Trying first one.")
            target_port = available_ports[0]
        else:
            target_port = self._port_spec

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
            # Update self.port only after a successful open so that
            # check_status() always reports the device actually in use and
            # never the literal string 'AUTO'.  A failed attempt leaves
            # self.port unchanged, and _port_spec stays 'AUTO' so the next
            # call re-runs discovery rather than retrying a stale path.
            self.port = target_port
            logger.info(f"Connected to serial port {self.port} (8-N-1)")
            return True
        except (serial.SerialException, OSError) as e:
            logger.error(f"Failed to connect to serial port {target_port}: {e}")
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

        assert self.connection is not None
        try:
            self.connection.write(data)
            self.connection.flush()
            logger.debug(f"Wrote to serial: {data!r}")
        except (serial.SerialException, OSError) as e:
            logger.error(f"Failed to write to serial port: {e}")
            # Invalidate connection on failure
            self.disconnect()
            raise serial.SerialException(str(e))

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
        except (serial.SerialException, OSError) as e:
            logger.error(f"Failed to read from serial port: {e}")
            self.disconnect()
            raise serial.SerialException(str(e))
