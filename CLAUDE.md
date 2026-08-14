# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

KVM-as-a-Service exposes an **SV04 4-port USB peripheral switch** over a REST API + web UI; the backend also retains six TESmart KVM protocols. A Python FastAPI service communicates with the switch over serial (`pyserial`), packaged as a Docker container.

See `AGENTS.md` for hardware safety rules, concurrency patterns, error handling conventions, and testing philosophy. Those rules are mandatory — follow them without exception.

## Commands

```bash
pytest                   # run all unit tests (no hardware required)
ruff check .             # lint
ty check                 # type-check
docker compose up --build  # build and run the full stack (port 8000)
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

**Protocol support:** Seven protocols (`hdc202_x24`, `enterprise`, `consumer_a`, `consumer_b`, `matrix`, `dual_monitor_hex`, `sv04`). `hdc202_x24` builds packets dynamically with a 1-byte checksum (sum of all preceding bytes mod 256, format `AA BB [CMD] [DATA1] [DATA2] [CS]`).

`sv04` targets a **different device class** — a 4-port USB peripheral switch, not a KVM. Only input selection exists (no buzzer/EDID/audio/queries). Format `AA [Input-1] [CS]` where all three bytes sum to `0x100`, at **115200** baud. Selecting the protocol auto-defaults the baud rate, and terminators are never appended (they would corrupt the 3-byte frame). Built via `ProtocolHandler.build_sv04_packet()`.

The other five protocols are static byte-string lookup tables.

The SV04 **echoes each command back verbatim** within ~40-95ms — undocumented by the vendor, but it is a genuine hardware confirmation. `_consume_sv04_frames` in `ControllerService` parses these echoes and updates `active_port`. Note the generic `try_parse_packet` cannot handle them: SV04 frames are 3 bytes with no `AA BB` header, so they are dispatched separately in `_monitor_serial`.

**Hardware verification:** `src/probe_switch.py` verifies switching with two independent signals — the echo, and a sysfs USB topology diff (when the Pi is on one of the switch's host ports, selecting that input attaches the switch's shared hub). Run `python -m src.probe_switch --confirm`. Also `--baud-sweep`, `--loopback`, and `--hold-tx` (meter DB9 pin 3 to pin 5 to detect a TTL adapter on an RS-232 port). Stop the service container first: it holds `/dev/ttyUSB0`.

⚠️ Any shared keyboard/mouse rides on this switch, so switching away from the Pi's own input **removes the Pi's input devices**. `probe_switch.py` always returns to the Pi's input before exiting; preserve that behaviour.

**Concurrency model:** `ControllerService` bridges async FastAPI with synchronous serial hardware. A daemon `_monitor_thread` owns all `serial.read` calls. Fire-and-forget commands write under `_lock` and return immediately. Query commands register a `concurrent.futures.Future` in `_pending_query`, write the packet, and `future.result(timeout=2.0)` — the monitor thread resolves it when a matching response arrives. See `AGENTS.md` for details.

**Environment variables:**
- `SERIAL_PORT` — device path or `AUTO` (default: `AUTO`)
- `BAUD_RATE` — default `9600`; set to `115200` for sv04. Sending sv04 commands at any other rate latches up its RS232 controller until power-cycled.
- `PROTOCOL` — applied at startup by `main.py` lifespan; set to `sv04` for the SV04 switch

**Web UI:** `static/index.html` + `static/app.js`, served via `StaticFiles` at `/`. Pico.css dark theme. The UI is SV04-specific: four input buttons (1–4), hardware-confirmed switching (the active-port indicator updates only after the SV04 echo is received), and no configuration controls — no protocol, baud rate, or terminator picker. Swagger docs at `http://localhost:8000/docs`. Full external API reference at `docs/API.md`.

## Testing conventions

- All unit tests mock `serial.Serial` via `unittest.mock.MagicMock` — never open a real port.
- Verify generated packets pass `ProtocolHandler.validate_packet()`.
- Hardware integration tests must be marked `@pytest.mark.integration` (none exist yet; they are skipped in CI by default).
- `tests/test_protocol_compliance.py` does byte-exact golden-packet verification with no mocks — good reference for adding new protocols.
