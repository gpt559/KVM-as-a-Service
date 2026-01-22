import time
import logging
import serial
from src.serial_manager import SerialManager
from src.constants import (
    Protocol,
    EnterpriseCommands,
    ConsumerACommands,
    ConsumerBCommands,
    MatrixCommands,
    DualMonitorHexCommands,
    HDC202X24Commands
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("diagnose_protocols")

def get_protocol_commands(protocol_name, command_class):
    """Helper to extract commands safely"""
    cmds = {}
    
    # Try to get Switch Port 1
    if hasattr(command_class, 'SWITCH_PORT_1'):
        cmds['SWITCH_1'] = getattr(command_class, 'SWITCH_PORT_1')
    elif hasattr(command_class, 'SWITCH_ALL_NEXT'): # Fallback for some
         cmds['SWITCH_NEXT'] = getattr(command_class, 'SWITCH_ALL_NEXT')

    # Try to get Buzzer
    if hasattr(command_class, 'BUZZER_ON'):
        cmds['BUZZER'] = getattr(command_class, 'BUZZER_ON')
        
    return cmds

def test_protocol(serial_mgr, protocol_name, command_class):
    logger.info(f"--- Testing Protocol: {protocol_name} ---")
    
    commands = get_protocol_commands(protocol_name, command_class)
    
    if not commands:
        logger.warning(f"No suitable test commands found for {protocol_name}")
        return

    for cmd_name, cmd_data in commands.items():
        logger.info(f"Sending {cmd_name}: {cmd_data}")
        
        try:
            # Clear input buffer before sending
            serial_mgr.reset_input_buffer()
            
            # Send command
            serial_mgr.write(cmd_data)
            
            # Wait for potential response
            time.sleep(1.0) 
            
            # Read response
            try:
                response = serial_mgr.read(size=64)
                if response:
                    hex_resp = response.hex(' ').upper()
                    try:
                        ascii_resp = response.decode('ascii', errors='ignore')
                    except:
                        ascii_resp = "<non-ascii>"
                    logger.info(f"RESPONSE RECEIVED [{protocol_name}]: HEX={hex_resp} | ASCII={ascii_resp}")
                else:
                    logger.info(f"No response received for {protocol_name} {cmd_name}")
            except Exception as e:
                logger.debug(f"Read timed out or failed: {e}")

        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            
    time.sleep(1) # Gap between protocols

def run_diagnostics():
    baud_rates = [9600, 19200, 38400, 57600, 115200]
    
    # List of protocols to test
    protocols = [
        ("Enterprise (Original)", EnterpriseCommands),
        ("Consumer A (Keypad)", ConsumerACommands),
        ("Consumer B (Routing)", ConsumerBCommands),
        ("Matrix (ASCII)", MatrixCommands),
        ("Dual Monitor (Hex)", DualMonitorHexCommands),
        ("HDC202-X24 (Target)", HDC202X24Commands),
    ]

    for baud in baud_rates:
        logger.info(f"========== Testing Baud Rate: {baud} ==========")
        serial_mgr = SerialManager(baudrate=baud)
        
        if not serial_mgr.connect():
            logger.error(f"Could not connect to serial port at {baud}. Ensure KVM service is stopped.")
            continue

        logger.info(f"Connected to {serial_mgr.port} at {baud} baud")

        try:
            for name, cls in protocols:
                test_protocol(serial_mgr, name, cls)
                
        except KeyboardInterrupt:
            logger.info("Diagnostics interrupted by user")
            serial_mgr.disconnect()
            return
        finally:
            serial_mgr.disconnect()
            
    logger.info("Diagnostics complete")

if __name__ == "__main__":
    run_diagnostics()
