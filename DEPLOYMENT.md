# Deployment Instructions

## Prerequisites

*   **Hardware**: Raspberry Pi (3B, 4, or 5 recommended) or any Linux server.
*   **Software**: Docker and Docker Compose installed.
    *   *Raspberry Pi OS*: `curl -sSL https://get.docker.com | sh`
*   **Connection**: USB-to-Serial adapter connected to the KVM.
    *   **WARNING**: Must be **3.3V TTL** logic level. Do NOT use standard RS-232 cables.
    *   **Pinout**: Tip/Ring/Sleeve must match manufacturer spec (Pin 3=TX, Pin 2=RX, Pin 1=GND).

## Configuration

1.  **Identify Serial Port**:
    On your Raspberry Pi or Linux host, run:
    ```bash
    ls /dev/ttyUSB*
    ```
    Common results: `/dev/ttyUSB0` or `/dev/ttyACM0`.

2.  **Update `docker-compose.yml`**:
    Edit the `environment` section in `docker-compose.yml` to match your hardware path.

    *Note: The default configuration uses `privileged: true` to access hardware. For better security, uncomment the `devices` section and map the specific port.*

    ```yaml
    # devices:
    #   - /dev/ttyUSB0:/dev/ttyUSB0  # Host Path : Container Path
    environment:
      - SERIAL_PORT=/dev/ttyUSB0     # Must match the device path
    ```

## Build and Run

1.  **Build the Image**:
    ```bash
    docker compose build
    ```

2.  **Run the Container**:
    ```bash
    docker compose up -d
    ```
    The `-d` flag runs the container in detached mode (background).

3.  **Verify Status**:
    Check if the container is running:
    ```bash
    docker ps
    ```
    View logs:
    ```bash
    docker compose logs -f
    ```

## Usage

Once running, the API will be available at `http://localhost:8000`.

*   **Check Status**: `GET /api/v1/status`
*   **Switch Port**: `POST /api/v1/switch` (JSON: `{"port": 1}`)
*   **Control Buzzer**: `POST /api/v1/buzzer` (JSON: `{"action": "on"}`)

## Updates

To deploy a new version:

1.  Pull the latest code.
2.  Rebuild: `docker compose build`
3.  Restart: `docker compose up -d`
