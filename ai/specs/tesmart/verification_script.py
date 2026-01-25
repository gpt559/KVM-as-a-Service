import serial
import time
import sys

# ==========================================
# CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATES = [9600, 115200, 38400]

# ==========================================
# CORRECTED COMMANDS (Based on CSV)
# ==========================================
COMMANDS = {
    # Row 3: Switch ALL outputs to PC1
    "switch_all_pc1": bytes.fromhex("AA BB 03 00 00 68"),
    
    # Row 12: Enable Buzzer
    "buzzer_on":  bytes.fromhex("AA BB 04 00 01 6A"),
    # Row 13: Disable Buzzer
    "buzzer_off": bytes.fromhex("AA BB 04 00 00 69"),

    # Row 51: Query Monitor Count (Response expected)
    "query_info": bytes.fromhex("AA BB 81 00 00 E6"),
}

def send_command(ser, cmd_bytes, label="Command", wait_time=0.5):
    try:
        # Clear buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        print(f"[{label}] Sending: {cmd_bytes.hex(' ').upper()}")
        ser.write(cmd_bytes)
        ser.flush()
        
        # Wait for processing
        time.sleep(wait_time)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"   └── Response: {response.hex(' ').upper()}")
            return response
        else:
            print("   └── [No Response]")
            return None

    except Exception as e:
        print(f"Error sending {label}: {e}")
        return None

def test_baud(baud):
    print(f"\n========================================")
    print(f"Testing Baud Rate: {baud}")
    print(f"========================================")
    
    try:
        with serial.Serial(SERIAL_PORT, baud, timeout=1) as ser:
            # Try Query First - it MUST respond
            print("\n--- Test 1: Query Info (Expect Response) ---")
            resp = send_command(ser, COMMANDS["query_info"], "Query Info", wait_time=1.0)
            
            if resp:
                print(f"*** SUCCESS: Device responded at {baud} baud! ***")
                
                print("\n--- Test 2: Buzzer (Audible Check) ---")
                send_command(ser, COMMANDS["buzzer_on"], "Buzzer ON")
                time.sleep(0.5)
                send_command(ser, COMMANDS["buzzer_off"], "Buzzer OFF")
                return True
            else:
                print(f"No response at {baud} baud.")
                return False
            
    except serial.SerialException as e:
        print(f"\nCRITICAL ERROR: Could not open port {SERIAL_PORT} at {baud}")
        print(f"Details: {e}")
        return False

def main():
    print(f"--- TESmart KVM Verification Script ---")
    print(f"Target: {SERIAL_PORT}")
    
    success = False
    for baud in BAUD_RATES:
        if test_baud(baud):
            success = True
            break
            
    if not success:
        print("\n\nFAILURE: Device did not respond to queries on any tested baud rate.")
        print("Check:")
        print("1. Is the serial cable plugged into the correct KVM port (Service Port)?")
        print("2. Is the pinout correct? (TX->RX, RX->TX, GND->GND)")
        print("3. Is the KVM powered on?")

if __name__ == "__main__":
    main()
