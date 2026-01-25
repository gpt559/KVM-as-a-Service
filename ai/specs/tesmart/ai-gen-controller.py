import serial
import time

# ==========================================
# CONFIGURATION
# ==========================================
# Linux port - usually /dev/ttyUSB0 or /dev/ttyACM0
# If you made the udev rule, use '/dev/ttyKVM'
SERIAL_PORT = '/dev/ttyUSB0' 

# TESmart HKS/HDC Series Standard Baud Rate
# Try 9600 first. If no response, change to 115200.
BAUD_RATE = 9600 

# ==========================================
# COMMAND DICTIONARY (From your CSV)
# ==========================================
COMMANDS = {
    "switch_pc1": "AA BB 03 01 01 69",  # Switch Output 1 to PC1
    "switch_pc2": "AA BB 03 01 02 6A",  # Switch Output 1 to PC2
    "buzzer_on":  "AA BB 04 00 01 6A",  # Enable Buzzer
    "buzzer_off": "AA BB 04 00 00 69",  # Disable Buzzer
    "mute_all":   "AA BB 0B 00 00 70",  # Fan Off (Quiet mode example)
    "query_info": "AA BB 81 00 00 E6",  # Query Monitor Count (Has Response)
}

def send_command(ser, hex_cmd, label="Command"):
    """
    Sends a hex string to the KVM and prints the response.
    """
    try:
        # 1. Convert Hex String to Bytes
        cmd_bytes = bytes.fromhex(hex_cmd)
        
        # 2. Clear buffers to remove old junk data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # 3. Send
        print(f"[{label}] Sending: {cmd_bytes.hex().upper()}")
        ser.write(cmd_bytes)
        ser.flush()  # Ensure data leaves the Pi immediately
        
        # 4. Wait & Read Response
        # KVMs are slow; give it 100-200ms to process
        time.sleep(0.2)
        
        # Read whatever is waiting in the buffer
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"   └── Response: {response.hex().upper()}")
            return response
        else:
            print("   └── [No Response - Check Wiring/Baud]")
            return None

    except Exception as e:
        print(f"Error sending {label}: {e}")
        return None

def calculate_checksum(payload_hex):
    """
    Helper: If you want to create commands dynamically.
    Formula: Sum of bytes % 256
    Example Input: "AA BB 03 01 01" (No checksum at end)
    """
    data = bytes.fromhex(payload_hex)
    checksum = sum(data) % 256
    return checksum

def main():
    print("--- TESmart KVM Controller ---")
    print(f"Target: {SERIAL_PORT} @ {BAUD_RATE} baud")
    
    try:
        # Open Serial Connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            
            # TEST 1: The "Audible" Test
            # We toggle the buzzer because you can HEAR it even if RX is broken.
            print("\n--- Test 1: Audio Check ---")
            send_command(ser, COMMANDS["buzzer_on"], "Buzzer ON")
            time.sleep(1)
            send_command(ser, COMMANDS["buzzer_off"], "Buzzer OFF")
            
            # TEST 2: The "Data" Test (The Query)
            # This verifies the RX line (KVM -> Pi) is working.
            print("\n--- Test 2: RX Wiring Check ---")
            resp = send_command(ser, COMMANDS["query_info"], "Query Info")
            
            if resp:
                print("\nSUCCESS: Hardware is fully bidirectional!")
            else:
                print("\nWARNING: No data received.")
                print("1. Check if OUDA Adapter is firmly plugged in.")
                print("2. Try changing BAUD_RATE to 115200.")
                
    except serial.SerialException as e:
        print(f"\nCRITICAL ERROR: Could not open port {SERIAL_PORT}")
        print(f"Details: {e}")
        print("Tip: Did you run 'sudo usermod -a -G dialout $USER'?")

if __name__ == "__main__":
    main()