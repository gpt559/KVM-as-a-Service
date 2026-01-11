# KVM-as-a-Service

A modern, web-based controller for TESmart KVM Switches. This project exposes a REST API and a web interface to control input switching and buzzer settings over a serial connection.

## 🚀 Getting Started

### Prerequisites

*   **Docker & Docker Compose** (Recommended)
*   OR Python 3.12+
*   A TESmart KVM Switch connected via Serial (USB or DB9)

### Hardware Setup

Refer to [SETUP_USB.md](SETUP_USB.md) for detailed instructions on identifying and configuring your serial device.

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

    The service will be available at `http://localhost:8000`.

## 📱 Network Access (Control from Phone/Tablet)

Want to control your KVM from your phone?

👉 **[Read the Network Access Guide](EXPOSE_NETWORK.md)**

If you are running on **Windows (WSL 2)**, we provide a 1-click script to expose the service to your local network.

## 🔌 API Usage

The service provides a Swagger UI for interactive documentation and testing.

*   **Docs:** `http://localhost:8000/docs`
*   **Switch Port:** `POST /api/v1/switch` -> `{"port": 1}`
*   **Buzzer:** `POST /api/v1/buzzer` -> `{"state": "off"}`

## 📁 Project Structure

*   `src/`: Application source code (FastAPI).
*   `static/`: Frontend web interface.
*   `scripts/`: Helper scripts for deployment/networking.
*   `ai/specs/`: Project specifications and design documents.
