This is a classic "headless hardware control" project. Since you are technical (CTO/Dev), I will frame this as a microservice deployment.The architecture is simple: KVM Hardware $\leftrightarrow$ Python Serial Manager $\leftrightarrow$ FastAPI Wrapper $\leftrightarrow$ Network.Here is the step-by-step guide to building your "KVM-as-a-Service" controller.PrerequisitesHardware: USB-to-TTL Serial Cable (3.5mm jack).Note: Ensure the PC you connect this to is always on. If this PC is one of the KVM inputs, verify it doesn't sleep, or the API will go down when you switch away (if the PC sleeps).OS: Linux (Raspberry Pi/Ubuntu) or Windows. (Linux is assumed for the service commands below, but code works on Windows).Python Libraries: pyserial, fastapi, uvicorn.Step 1: Identify the Serial DeviceConnect the USB cable to your PC and the 3.5mm jack to Port 11 on the KVM.Linux: Run ls /dev/ttyUSB*. It will likely be /dev/ttyUSB0.Windows: Check Device Manager for the "COM" port number (e.g., COM3).Step 2: The Application Code (kvm_server.py)We will use FastAPI because it is lightweight, async, and auto-generates Swagger documentation (useful for testing your new endpoints).Create a file named kvm_server.py:Pythonimport serial
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0'  # Change to 'COM3' for Windows
BAUD_RATE = 9600

# Standard TESmart Hex Codes
# Format: Header (AA BB 03) + Cmd + Data + Footer (EE)
COMMANDS = {
    "1": "AA BB 03 01 01 EE",  # Switch to PC 1
    "2": "AA BB 03 01 02 EE",  # Switch to PC 2
    "mute": "AA BB 03 02 00 EE", # Mute Buzzer
    "unmute": "AA BB 03 02 01 EE" # Unmute Buzzer
}

app = FastAPI(title="KVM Control API")

class CommandRequest(BaseModel):
    action: str

def send_serial_hex(hex_str: str):
    """Opens serial connection, sends hex, closes connection."""
    try:
        payload = bytes.fromhex(hex_str)
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(payload)
            time.sleep(0.1) # Brief pause for stability
    except serial.SerialException as e:
        raise HTTPException(status_code=500, detail=f"Serial Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System Error: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "online", "device": "TESmart KVM"}

@app.post("/switch/{port_id}")
def switch_input(port_id: str):
    """Switch KVM input to Port 1 or 2."""
    if port_id not in ["1", "2"]:
        raise HTTPException(status_code=400, detail="Invalid Port. Use 1 or 2.")
    
    cmd = COMMANDS[port_id]
    send_serial_hex(cmd)
    return {"message": f"Switched to PC {port_id}"}

@app.post("/control/buzzer/{state}")
def control_buzzer(state: str):
    """Turn buzzer 'on' or 'off'."""
    if state.lower() == "off":
        send_serial_hex(COMMANDS["mute"])
        return {"message": "Buzzer muted"}
    elif state.lower() == "on":
        send_serial_hex(COMMANDS["unmute"])
        return {"message": "Buzzer enabled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid state. Use 'on' or 'off'.")

if __name__ == "__main__":
    import uvicorn
    # Host 0.0.0.0 exposes it to the LAN
    uvicorn.run(app, host="0.0.0.0", port=8000)
Step 3: Install DependenciesRun the following in your terminal:Bashpip install fastapi uvicorn pyserial
Step 4: Test the APIRun the server manually to verify:Bashpython kvm_server.py
Open a browser on any device in your network.Navigate to: http://<YOUR-PC-IP>:8000/docsYou will see the Swagger UI. Click on POST /switch/{port_id}, enter 1 or 2, and hit Execute.Verification: You should hear the KVM click or beep (unless muted) and switch inputs.Step 5: Make it Persistent (Linux/Systemd)To ensure this runs automatically if the PC reboots, create a system service.Create the service file:sudo nano /etc/systemd/system/kvm-api.servicePaste the following:Ini, TOML[Unit]
Description=TESmart KVM REST API
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/your/script
ExecStart=/usr/bin/python3 /path/to/your/script/kvm_server.py
Restart=always

[Install]
WantedBy=multi-user.target
Enable and Start:Bashsudo systemctl daemon-reload
sudo systemctl enable kvm-api.service
sudo systemctl start kvm-api.service
Step 6: IntegrationNow that you have a REST API running at http://192.168.1.X:8000, you can control it from anywhere:iOS Shortcuts: Create a "Get Contents of URL" shortcut to POST to the switch endpoint. Add it to your Home Screen.Stream Deck: Use the "Website" button action to trigger the switch.Browser Bookmark: Save the URL (for GET requests, though you'd need to modify the code slightly to allow GET for switching if you want purely bookmark-based control).Troubleshooting NoteIf you plug the USB cable in and out, Linux might change the device from ttyUSB0 to ttyUSB1.Fix: Create a udev rule to lock the name.Run lsusb to find your adapter's Vendor/Product ID.Create /etc/udev/rules.d/99-kvm-serial.rules:SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", SYMLINK+="ttyKVM"Update your Python script to use /dev/ttyKVM.