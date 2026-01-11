# Deployment Instructions

## Prerequisites

*   Docker installed on the host machine.
*   Docker Compose installed on the host machine.
*   The KVM hardware connected via serial (USB-to-Serial or direct DB9).

## Configuration

1.  **Identify Serial Port**:
    Run `ls /dev/tty*` to find your serial device (e.g., `/dev/ttyUSB0`, `/dev/ttyACM0`, or `/dev/ttyS0`).

2.  **Update `docker-compose.yml`**:
    Edit the `devices` and `environment` sections in `docker-compose.yml` to match your hardware path.

    ```yaml
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # Host Path : Container Path
    environment:
      - SERIAL_PORT=/dev/ttyUSB0   # Must match Container Path
    ```

## Build and Run

1.  **Build the Image**:
    ```bash
    docker-compose build
    ```

2.  **Run the Container**:
    ```bash
    docker-compose up -d
    ```
    The `-d` flag runs the container in detached mode (background).

3.  **Verify Status**:
    Check if the container is running:
    ```bash
    docker ps
    ```
    View logs:
    ```bash
    docker-compose logs -f
    ```

## Usage

Once running, the API will be available at `http://localhost:8000`.

*   **Check Status**: `GET /api/v1/status`
*   **Switch Port**: `POST /api/v1/switch` (JSON: `{"port": 1}`)
*   **Control Buzzer**: `POST /api/v1/buzzer` (JSON: `{"action": "on"}`)

## Updates

To deploy a new version:

1.  Pull the latest code.
2.  Rebuild: `docker-compose build`
3.  Restart: `docker-compose up -d`
