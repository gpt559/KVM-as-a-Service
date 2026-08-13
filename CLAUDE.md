# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

KVM-as-a-Service exposes TESmart KVM switches over a REST API + web UI. A Python FastAPI service communicates with the switch over UART/USB (`pyserial`), packaged as a Docker container.

See `AGENTS.md` for hardware safety rules, concurrency patterns, error handling conventions, and testing philosophy. Those rules are mandatory — follow them without exception.

## Commands

```bash
pytest                   # run all unit tests (no hardware required)
ruff check .             # lint
ty check                 # type-check
docker-compose up --build  # build and run the full stack (port 8000)
```

Run a single test file:
```bash
pytest tests/test_protocol_compliance.py
```

CI runs `ruff check .`, `ty check`, and `pytest` in sequence — all three must pass.

## Architecture

**Request path:** `HTTP → main.py (FastAPI routes) → ControllerService → SerialManager → /dev/ttyUSB*`

**Key source files:**

| File | Role |
|---|---|
| `src/main.py` | FastAPI app, all `/api/v1/*` routes, lifespan startup/shutdown |
| `src/controller_service.py` | Singleton business logic; owns `_lock`, `_monitor_thread`, `_pending_query` |
| `src/serial_manager.py` | pyserial HAL; AUTO port discovery (`/dev/ttyUSB*`, `/dev/ttyACM*`) |
| `src/protocol_handler.py` | `build_packet`, `validate_packet`, `try_parse_packet` |
| `src/constants.py` | `Protocol` enum, 6 command classes, `PROTOCOL_MAP`, `HDC202X24Commands` |
| `src/models.py` | Pydantic v2 request/response models |

**Protocol support:** Six protocols (`hdc202_x24`, `enterprise`, `consumer_a`, `consumer_b`, `matrix`, `dual_monitor_hex`). `hdc202_x24` builds packets dynamically with a 1-byte checksum (sum of all preceding bytes mod 256, format `AA BB [CMD] [DATA1] [DATA2] [CS]`). The other five are static byte-string lookup tables.

**Concurrency model:** `ControllerService` bridges async FastAPI with synchronous serial hardware. A daemon `_monitor_thread` owns all `serial.read` calls. Fire-and-forget commands write under `_lock` and return immediately. Query commands register a `concurrent.futures.Future` in `_pending_query`, write the packet, and `future.result(timeout=2.0)` — the monitor thread resolves it when a matching response arrives. See `AGENTS.md` for details.

**Environment variables:**
- `SERIAL_PORT` — device path or `AUTO` (default: `AUTO`)
- `BAUD_RATE` — default `9600`; controller enforces 9600 on init

**Web UI:** `static/index.html` + `static/app.js`, served via `StaticFiles` at `/`. Pico.css dark theme. Swagger docs at `http://localhost:8000/docs`.

## Testing conventions

- All unit tests mock `serial.Serial` via `unittest.mock.MagicMock` — never open a real port.
- Verify generated packets pass `ProtocolHandler.validate_packet()`.
- Hardware integration tests must be marked `@pytest.mark.integration` (none exist yet; they are skipped in CI by default).
- `tests/test_protocol_compliance.py` does byte-exact golden-packet verification with no mocks — good reference for adding new protocols.
