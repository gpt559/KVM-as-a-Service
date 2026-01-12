# KVM-as-a-Service

A modern, web-based controller for TESmart KVM Switches, designed to run on a **Raspberry Pi**. This project exposes a REST API and a web interface to control input switching and buzzer settings over a serial connection.

## 🚀 Getting Started

### Prerequisites

*   **Hardware**: Raspberry Pi (running Raspberry Pi OS) or Linux Desktop/Server.
*   **Software**: Docker & Docker Compose.
*   **KVM**: A TESmart KVM Switch connected via Serial (USB-to-Serial adapter recommended).

### Hardware Setup

1.  Connect your USB-to-Serial adapter to the Raspberry Pi.
2.  Connect the DB9 end to the RS232 port on the KVM.
3.  Identify the port (usually `/dev/ttyUSB0`).

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd KVM-as-a-Service
    ```

2.  **Configure Serial Port:**
    Edit `docker-compose.yml` to match your device path (e.g., `/dev/ttyUSB0`).

3.  **Run with Docker:**
    ```bash
    docker-compose up -d --build
    ```

    The service will be available at `http://<your-pi-ip-address>:8000`.

## 📱 Network Access (Control from Phone/Tablet)

Since the service runs in Docker on your Raspberry Pi, it is automatically accessible on your local network.

1.  Find your Pi's IP address: `hostname -I`
2.  Open a browser on your phone/tablet: `http://<pi-ip-address>:8000`

### Windows (WSL 2) Users
If you are developing on Windows using WSL 2, you may need to use our helper script to expose the port to your LAN.
👉 **[Read the Network Access Guide](EXPOSE_NETWORK.md)**

## 🔌 API Usage

The service provides a Swagger UI for interactive documentation and testing.

*   **Docs:** `http://localhost:8000/docs`
*   **Switch Port:** `POST /api/v1/switch` -> `{"port": 1}`
*   **Buzzer:** `POST /api/v1/buzzer` -> `{"state": "off"}`
*   **Light Control:** `POST /api/v1/light` -> `{"mode": "flow"}`
*   **Fan Control:** `POST /api/v1/fan` -> `{"mode": "auto"}`
*   **Audio Source:** `POST /api/v1/audio/source` -> `{"port": 1}`
*   **Network Power:** `POST /api/v1/network` -> `{"port": 1, "enabled": true}`
*   **USB Focus:** `POST /api/v1/usb/focus` -> `{"target": "pc1"}`

## 📁 Project Structure

*   `src/`: Application source code (FastAPI).
*   `static/`: Frontend web interface.
*   `scripts/`: Helper scripts for deployment/networking.
*   `ai/specs/`: Project specifications and design documents.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
