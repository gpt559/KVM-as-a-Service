import time
import logging
from src.serial_manager import SerialManager
from src.constants import HDC202X24Commands

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_commands")

def test_commands():
    # Initialize Serial Manager
    # Note: Ensure the main service is STOPPED before running this to avoid port conflict
    serial = SerialManager()
    
    if not serial.connect():
        logger.error("Could not connect to serial port. Make sure the KVM service is stopped.")
        return

    # Try asserting DTR/RTS in case the interface needs it
    if serial.connection:
        serial.connection.dtr = True
        serial.connection.rts = True
        logger.info("Asserted DTR/RTS lines")

    try:
        logger.info("--- TEST STARTED ---")
        
        # Test 1: Switch ALL to PC1 (Current implementation)
        logger.info("1. Sending SWITCH_ALL_PC1 (0x03 0x00 0x00)")
        cmd = HDC202X24Commands.SWITCH_PORT_1
        serial.write(cmd)
        time.sleep(3) # Wait for user to observe
        
        # Test 2: Switch ALL to PC2
        logger.info("2. Sending SWITCH_ALL_PC2 (0x03 0x00 0x01)")
        cmd = HDC202X24Commands.SWITCH_PORT_2
        serial.write(cmd)
        time.sleep(3)

        # Test 3: Switch OUTPUT 1 to PC1 (Alternative)
        logger.info("3. Sending SWITCH_OUT1_PC1 (0x03 0x01 0x00)")
        cmd = HDC202X24Commands.SWITCH_OUT1_PC1
        serial.write(cmd)
        time.sleep(3)

        # Test 4: Switch OUTPUT 1 to PC2 (Alternative)
        logger.info("4. Sending SWITCH_OUT1_PC2 (0x03 0x01 0x01)")
        cmd = HDC202X24Commands.SWITCH_OUT1_PC2
        serial.write(cmd)
        time.sleep(3)
        
        logger.info("--- TEST COMPLETE ---")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        serial.disconnect()

if __name__ == "__main__":
    test_commands()
