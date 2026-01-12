# AGENTS.md

## 🤖 Project Context for AI Agents

**Project Name:** KVM-as-a-Service  
**Description:** A FastAPI-based microservice that exposes a REST API and Web UI to control TESmart KVM switches via a serial connection (USB/DB9). It is optimized for deployment on Linux environments, specifically Raspberry Pi, allowing for switching input ports and controlling buzzer settings remotely.

---

## 🏗️ Architecture Overview

The system follows a layered architecture:
1.  **Hardware**: TESmart KVM Switch (connected via Serial).
2.  **HAL (Hardware Abstraction Layer)**: `src/serial_manager.py` handles raw serial bytes.
3.  **Controller Layer**: `src/controller_service.py` manages business logic, locking, and state.
4.  **API Layer**: `src/main.py` (FastAPI) exposes HTTP endpoints.
5.  **Frontend**: `static/` contains a simple HTML/JS interface.

---

## 📂 Key File Structure

- **`src/`**: Application source code.
    - `main.py`: FastAPI entry point and route definitions.
    - `controller_service.py`: Main logic for handling KVM commands.
    - `serial_manager.py`: Low-level serial communication handling.
    - `models.py`: Pydantic models for API request/response.
    - `constants.py`: Hex codes and configuration constants.
- **`ai/specs/`**: Detailed project specifications.
    - `MVP/`: Specs for the Minimum Viable Product. **READ THESE BEFORE ARCHITECTURAL CHANGES.**
    - `UI/`: Specs for the frontend interface.
- **`tests/`**: Pytest test suite.
- **`static/`**: Web assets (index.html, app.js).
- **`docker-compose.yml`**: Definition for containerized deployment.

---

## 💻 Development Guidelines

### Coding Standards
- **Language**: Python 3.12+
- **Style**: PEP 8.
- **Type Hinting**: **Mandatory** for all function arguments and return values.
- **Documentation**: All modules and functions must have docstrings.
- **Async**: Use `async`/`await` for all FastAPI route handlers.

### Key Libraries
- **FastAPI**: Web framework.
- **Pydantic**: Data validation.
- **PySerial**: Serial port communication.

### Error Handling
- Use `HTTPException` in API routes.
- Low-level serial errors should be caught in `serial_manager.py` and propagated as custom exceptions or boolean failures to the controller.
- Ensure the serial port is properly locked (`threading.Lock` in `ControllerService`) to prevent concurrent access issues.

---

## 🧪 Testing & Verification

- **Framework**: `pytest`
- **Mocking**: Serial connections **must** be mocked for unit tests. Do not attempt to open real serial ports during `pytest` execution.
- **Running Tests**:
  ```bash
  pytest
  ```

---

## 🚀 Deployment

- **Docker**: The primary deployment method. Supports `linux/amd64` and `linux/arm64` (Raspberry Pi).
- **Build**: `docker-compose build`
- **Run**: `docker-compose up -d`
- **Serial Port**: The serial port path (e.g., `/dev/ttyUSB0`) is passed via `docker-compose.yml` environment variables. When running on Raspberry Pi, ensure the correct USB or GPIO serial device is targeted.

---

## 🧠 AI Agent Workflow

1.  **Context**: Always check `ai/specs/MVP/tasks.md` to see the current progress of the project.
2.  **Modification**: When modifying the HAL or Controller, ensure backward compatibility with the TESmart Hex protocol defined in `src/constants.py`.
3.  **Frontend**: If modifying `static/`, ensure it calls the API endpoints defined in `src/main.py`.
4.  **Documentation**: Update `README.md` or `DEPLOYMENT.md` if you change environment variables or deployment steps.
