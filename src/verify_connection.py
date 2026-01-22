import time
import logging
import sys
from src.serial_manager import SerialManager
from src.constants import HDC202X24Commands

# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def verify_connection():
    print("=== KVM Connection Verification ===")
    print("Verifying commands from .debug/testing-instructions.md")
    
    # 1. Connection Setup
    # Note: Using /dev/ttyUSB0 as default, matching common Linux setups
    port = '/dev/ttyUSB0'
    baud = 9600
    
    print(f"Connecting to {port} at {baud} baud...")
    mgr = SerialManager(port=port, baudrate=baud, timeout=1.0)
    
    if not mgr.connect():
        print(f"❌ Failed to connect to {port}. Make sure:")
        print("   1. The device is plugged in.")
        print("   2. You have permission (try sudo).")
        print("   3. The KVM service is STOPPED (to free the port).")
        sys.exit(1)

    print("✅ Connected.")

    try:
        # ---------------------------------------------------------
        # Test 1: The "Golden Test" (Query Monitor Status)
        # ---------------------------------------------------------
        print("\n[Test 1] The 'Golden Test' (RX Check)")
        print("Purpose: Verifies the KVM can talk back to us.")
        
        cmd = HDC202X24Commands.QUERY_MONITOR_COUNT
        print(f"Sending:  {cmd.hex(' ').upper()}")
        
        mgr.reset_input_buffer()
        mgr.write(cmd)
        
        # Wait for response
        time.sleep(0.5)
        response = mgr.read(128)
        
        if response:
            print(f"Received: {response.hex(' ').upper()}")
            
            # Validation
            if response.startswith(b'\xAA\xBB'):
                print("Result:   ✅ VALID HEADER (AA BB)")
                
                # Checksum check
                payload = response[:-1]
                calc_sum = sum(payload) % 256
                recv_sum = response[-1]
                
                if calc_sum == recv_sum:
                    print(f"Checksum: ✅ VALID ({hex(recv_sum)})")
                else:
                    print(f"Checksum: ❌ INVALID (Expected {hex(calc_sum)}, Got {hex(recv_sum)})")
            else:
                print("Result:   ⚠️ INVALID HEADER")
        else:
            print("Received: [NO RESPONSE]")
            print("Result:   ❌ FAILURE (Check RX wire)")

        # ---------------------------------------------------------
        # Test 2: The "Blind Test" (Buzzer)
        # ---------------------------------------------------------
        print("\n[Test 2] The 'Blind Test' (TX Check)")
        print("Purpose: Verifies we can talk to the KVM (even if RX is broken).")
        
        print("\n> Muting Buzzer...")
        print(f"Sending: {HDC202X24Commands.BUZZER_OFF.hex(' ').upper()}")
        mgr.write(HDC202X24Commands.BUZZER_OFF)
        print("(Listen for silence)")
        
        time.sleep(1.5)
        
        print("\n> Enabling Buzzer...")
        print(f"Sending: {HDC202X24Commands.BUZZER_ON.hex(' ').upper()}")
        mgr.write(HDC202X24Commands.BUZZER_ON)
        print("(Listen for beep)")
        
        print("\n✅ Sequence complete.")

    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        mgr.disconnect()
        print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_connection()
