# Raspberry Pi 5 Deployment Plan

This guide outlines the steps to deploy the **KVM-as-a-Service** application on your Raspberry Pi 5 (`pimon`).

## 1. Hardware Setup
1. Connect the **TESmart KVM Switch** to one of the Raspberry Pi 5's USB ports using a **USB Type-A to Type-B cable** (or RS232-to-USB adapter).
2. Ensure the KVM is powered on.

## 2. Identify the Serial Port
The system needs to know which device path the KVM is using.
1. Open a terminal on the Pi (or inside your VSCode terminal connected to the Pi).
2. Run the following command to list USB TTY devices:
   ```bash
   ls -l /dev/ttyUSB*
   ```
   *   If you see `/dev/ttyUSB0`, that is likely your device.
   *   If you see multiple, try unplugging and replugging the KVM to see which one appears/disappears.
   *   *Note: If you are using the GPIO pins for serial, it might be `/dev/ttyAMA0` or `/dev/serial0`, but USB is recommended.*

## 3. Configure Docker Compose
We need to map the physical serial port into the Docker container.

1. Open `docker-compose.yml`.
2. Locate the `services.kvm-service` section.
3. **Uncomment** the `devices` section and ensure the mapping matches your identified port.
4. Ensure the `SERIAL_PORT` environment variable also matches.

**Example Configuration:**
```yaml
    privileged: true  # Recommended for hardware access
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # <Host Path>:<Container Path>
    environment:
      - SERIAL_PORT=/dev/ttyUSB0
      - BAUD_RATE=9600  # Verify this matches your specific TESmart model (commonly 9600 or 115200)
```

## 4. Baud Rate Verification
TESmart KVMs typically operate at **9600** or **115200** baud.
*   **Default in code:** 9600 (checked in `src/serial_manager.py` if not overridden).
*   **Default in docker-compose:** 115200.
*   **Action:** If connection fails, try changing `BAUD_RATE` in `docker-compose.yml` to `9600` and restart.

## 5. Deployment
Since you are already in a devcontainer on the Pi, you can run the production container side-by-side or exit the devcontainer to run it on the host OS.

**To run via Docker Compose (Standard Production Mode):**

1. Build the ARM64 image:
   ```bash
   docker-compose build
   ```
2. Start the service in the background:
   ```bash
   docker-compose up -d
   ```
3. Check the logs to verify the serial connection:
   ```bash
   docker-compose logs -f
   ```
   *Look for: "Connected to serial port /dev/ttyUSB0"*

## 6. Accessing the Service
Once running, the service will be available on your local network.

*   **Web UI:** `http://pimon.local:8000` (or use the Pi's IP address: `http://<IP>:8000`)
*   **API Docs:** `http://pimon.local:8000/docs`

## 7. Troubleshooting
*   **Permission Denied:** If you see permission errors accessing `/dev/ttyUSB0`, you may need to add the `pi` user to the `dialout` group on the host (though Docker's `privileged: true` usually handles this):
    ```bash
    sudo usermod -a -G dialout $USER
    ```
    *Reboot after adding the group.*
*   **Device Not Found:** Ensure the KVM is plugged in *before* starting the container. Docker often requires the device to exist at startup.
