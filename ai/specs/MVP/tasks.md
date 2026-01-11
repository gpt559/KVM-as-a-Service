# Implementation Plan: KVM-as-a-Service

This document outlines the step-by-step implementation plan for the KVM-as-a-Service system, based on `requirements.md` and `design.md`.

## Legend for Requirement References
*   **Req 1.x**: User Stories (1.1 Switch, 1.2 Audio, 1.3 Availability)
*   **Req 2.x**: Functional Requirements (2.1 Ubiquitous, 2.2 Event-Driven, 2.3 State-Driven, 2.4 Unwanted Behavior)
*   **Req 3.x**: Acceptance Criteria (3.1 Switch Scenario, 3.2 Invalid Input, 3.3 Buzzer, 3.4 Persistence)

---

## Phase 1: Project Initialization & Environment
*Focus: Setting up the repository structure and dependencies.*

- [x] Initialize Python project structure (`src/`, `tests/`, `config/`) and virtual environment. (Refs Req 2.1)
- [x] Create `requirements.txt` including `fastapi`, `uvicorn`, `pyserial`, `pydantic`. (Refs Design 1.0)
- [x] Create basic `.gitignore` for Python and VS Code. (Refs Design 1.0)

## Phase 2: Core Domain & Hardware Abstraction Layer (HAL)
*Focus: Low-level serial communication and business logic controller.*

- [x] Implement `HexCommands` Enum mapping high-level actions to byte strings. (Refs Design 2.0)
- [x] Implement `SerialManager` (HAL) class to handle `pyserial` connection, including opening/closing and error handling. (Refs Req 2.1, Req 2.4)
- [x] Implement `ControllerService` class structure with Thread Locking (`threading.Lock`) for exclusive access. (Refs Req 2.3, Design 2.0)
- [x] Implement `switch_port(port_id)` method in `ControllerService` that sends the correct hex command. (Refs Req 1.1, Req 2.2)
- [x] Implement `control_buzzer(state)` method in `ControllerService`. (Refs Req 1.2, Req 2.2)
- [x] Implement `check_status()` method in `ControllerService` to verify serial connection health. (Refs Req 1.3, Req 2.2, Req 2.4)
- [x] **Unit Test**: Write tests for `ControllerService` mocking the `SerialManager` to verify locking and logic flow. (Refs Req 3.1, Req 3.3)
- [x] **Unit Test**: Write specific test case for "Invalid Port" rejection at the internal method level (if applicable) or verify exception handling. (Refs Req 2.4)

## Phase 3: API Layer Implementation (FastAPI)
*Focus: Exposing the core logic via HTTP.*

- [x] Define Pydantic models: `SwitchRequest`, `BuzzerRequest`, `SuccessResponse`, `ErrorResponse`. (Refs Design 3.1, Req 2.4)
- [x] Initialize FastAPI application with `on_event("startup")` to initialize the `ControllerService` serial connection. (Refs Req 2.2, Req 3.4)
- [x] Implement endpoint `POST /api/v1/switch`: Validates input and calls controller. (Refs Req 1.1, Req 3.1)
- [x] Implement error handling for `POST /api/v1/switch` to return 400 Bad Request for invalid ports (1-8). (Refs Req 3.2, Req 2.4)
- [x] Implement endpoint `POST /api/v1/buzzer`: Parses "on"/"off" and calls controller. (Refs Req 1.2, Req 3.3)
- [x] Implement endpoint `GET /api/v1/status`: Returns service health and connection status. (Refs Req 1.3, Req 2.2)
- [x] **Unit Test**: Write `TestClient` tests for all API endpoints to ensure correct HTTP status codes and JSON bodies. (Refs Req 3.1, 3.2, 3.3)

## Phase 4: Containerization & Deployment
*Focus: Dockerizing the application and ensuring system integration.*

- [ ] Create `Dockerfile` using a slim Python base image. (Refs Design 4.0, Req 2.1)
- [ ] Create `.dockerignore` to exclude unnecessary files (virtualenv, tests, git).
- [ ] Create `docker-compose.yml` (optional but recommended) to define the service and device mapping configuration. (Refs Design 4.0)
- [ ] Create a deployment script or README instructions for building and running the container with `--device` flags and restart policies. (Refs Req 3.4, Design 4.0)
- [ ] **Verification**: Build the Docker image and confirm it starts successfully.
- [ ] **Verification**: Run the container with serial device mapped and verify full functionality (Switching/Buzzer). (Refs Req 3.5)

## Phase 5: Verification & Acceptance
*Focus: Manual validation against Acceptance Criteria.*

- [ ] **Manual Verify**: Test Scenario 1 - Send valid switch request (Port 1), observe hardware response and 200 OK. (Refs Req 3.1)
- [ ] **Manual Verify**: Test Scenario 2 - Send invalid switch request (Port 99), verify 400 Bad Request and no hardware action. (Refs Req 3.2)
- [ ] **Manual Verify**: Test Scenario 3 - Mute buzzer, verify hardware silence and success response. (Refs Req 3.3)
- [ ] **Manual Verify**: Test Scenario 4 - Reboot host, verify API is available immediately after boot without user login (via Docker restart policy). (Refs Req 3.4)
- [ ] **Manual Verify**: Test Scenario 5 - Verify containerized execution and device access. (Refs Req 3.5)
- [ ] **Manual Verify**: Unplug Serial Cable, verify `GET /status` or next command reports generic system error (503). (Refs Req 2.4)
