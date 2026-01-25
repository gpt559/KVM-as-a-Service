# AGENTS.md

> **This file defines the strict operational parameters for AI Agents and Developers working on the KVM-as-a-Service project.**
> *Last Updated: 2026-01-25*

## 🤖 Project Identity & Stack

**Role:** Senior Embedded Systems Engineer  
**Core Objective:** Reliable control of TESmart KVM switches via UART/USB for data centers and home labs.

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.12+ |
| **API Framework** | FastAPI |
| **UI Framework** | Vanilla HTML5 / JavaScript (ES6+) / Pico.css |
| **Hardware IO** | `pyserial` (3.3V TTL Logic) |
| **Container** | Docker / Docker Compose |
| **Testing** | `pytest` |

---

## 🛑 Hardware Safety Rules (Strict 'Never' List)

1.  **Never send raw hex strings without validation.**
    *   *Rule:* All outgoing packets must be constructed via `ProtocolHandler.build_packet()` which ensures correct headers (`AA BB`) and checksums.
    *   *Why:* Malformed packets can hang the KVM's internal microcontroller.

2.  **Never access the serial port without a Lock.**
    *   *Rule:* All `serial.write` operations must be wrapped in `with self._lock:` context managers.
    *   *Why:* Concurrent writes (e.g., from an async API request and a background status check) will interleave bytes and corrupt the protocol.

3.  **Never reset the serial port while a command is in-flight.**
    *   *Rule:* Check `self._pending_query` before attempting a reconnection or port reset.
    *   *Why:* Resetting during a read/write cycle leaves the hardware in an undefined state.

4.  **Never block the main thread for hardware IO.**
    *   *Rule:* Serial reads must happen in the dedicated `_monitor_thread`. API routes must `await` results or return immediately; they must never call blocking `serial.read()`.

5.  **Never assume the device is on `/dev/ttyUSB0`.**
    *   *Rule:* Always support `AUTO` discovery or environment variable configuration (`SERIAL_PORT`).

---

## 🔄 Concurrency Patterns

The system bridges asynchronous Web API calls with synchronous serial hardware.

1.  **Singleton Controller:**
    *   `ControllerService` acts as the singleton gatekeeper. It is initialized once during FastAPI startup (`lifespan`).

2.  **The "Command-Query" Split:**
    *   **Commands (Fire-and-Forget):** Operations like switching ports (`switch_port`) are sent immediately under a lock. We do not wait for hardware confirmation to return HTTP 200, unless the protocol explicitly requires it.
    *   **Queries (Request-Response):** Operations requiring data (e.g., `send_query`) use a `Future` pattern.
        *   The API thread creates a `concurrent.futures.Future`.
        *   The request is registered in `self._pending_query`.
        *   The background `_monitor_thread` parses incoming bytes. If a packet matches the pending query, it completes the `Future`.
        *   The API thread awaits the `Future` (with a timeout).

3.  **Background Monitoring:**
    *   A daemon thread (`_monitor_thread`) continuously reads from the serial port using `serial.read_existing()`. It parses full packets and dispatches them (e.g., resolving queries or updating internal state).

---

## 🛠️ Standard Commands

### 🧪 Testing
Run the full test suite. **Crucial:** Ensure no physical hardware is required.
```bash
pytest
```

### 🧹 Linting & Formatting
Enforce PEP 8 and project standards.
```bash
ruff check .
```

### 🔍 Type Checking
Ensure type safety.
```bash
ty check
```

### 🚀 Launching Hardware Simulator / Service
Start the full stack (API + UI). In development, this runs the service. To simulate hardware without a device, ensure `SerialManager` is mocked or the environment is configured to use a virtual port (e.g., `socat`).
```bash
docker-compose up --build
```

### 🔌 Manual Hardware Verification
To test physical connectivity without the API overhead:
```bash
python3 ai/specs/tesmart/ai-gen-controller.py
```

---

## ⚠️ Error Handling Style

1.  **Hardware vs. Logic Errors:**
    *   **Logic Errors** (e.g., invalid port number) -> Raise `HTTPException(400)`.
    *   **Hardware Errors** (e.g., Serial timeout, Disconnected) -> Raise `HTTPException(503 Service Unavailable)`.

2.  **Propagation Strategy:**
    *   Low-level `serial.SerialException` in `SerialManager` should be caught and logged.
    *   The `ControllerService` should check `serial_manager.is_connected()` and attempt reconnection if needed.
    *   If reconnection fails during a user request, the API must return `503` with a clear message: `"Hardware communication failed: [Detail]"`.

3.  **Timeouts:**
    *   Queries must have a strict timeout (default: 2.0s). If the hardware does not reply, the `Future` times out, and the API returns `503`. We do *not* hang the web request indefinitely.

---

## 🧪 Testing Philosophy

1.  **Mock First:**
    *   Unit tests (`tests/`) must **NEVER** attempt to open a real serial port.
    *   Use `unittest.mock.MagicMock` to mock `serial.Serial`.
    *   Test logic by asserting `mock_serial.write` was called with the correct bytes.
    *   Simulate responses by side-effecting `mock_serial.read` to return prepared byte strings.

2.  **Packet Validation:**
    *   Tests must verify that generated packets pass `ProtocolHandler.validate_packet()`.

3.  **Integration Testing:**
    *   Integration tests (requiring real hardware) should be marked clearly (e.g., `@pytest.mark.integration`) and skipped by default in CI/CD environments.
