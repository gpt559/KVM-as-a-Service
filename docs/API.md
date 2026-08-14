# KVM-as-a-Service API Reference

API reference for the KVM-as-a-Service REST service when controlling an **SV04 4-port USB peripheral switch**.

> **Device note:** The SV04 is a USB peripheral switch, not a KVM. It routes shared USB devices (keyboard, mouse, etc.) between up to four host computers. It has no video, audio, buzzer, EDID, or fan capabilities. The only supported operation is selecting which input owns the shared peripherals.

---

## Base URL

```
http://<host>:8000
```

Replace `<host>` with the hostname or IP address of the machine running the service (typically a Raspberry Pi on the local network).

Interactive API documentation is auto-generated at **`/docs`** (Swagger UI). The raw OpenAPI schema is at **`/openapi.json`**.

---

## Authentication

**There is no authentication.** All endpoints are publicly accessible to anyone who can reach the host. Keep the service on a trusted network (e.g., isolated LAN or VPN). Do not expose port 8000 to the internet.

---

## Endpoints

### `POST /api/v1/switch`

Switch the shared USB peripherals to a specific input.

**This is the primary—and for SV04, only meaningful—endpoint.**

#### Hardware-confirmation guarantee

Unlike fire-and-forget serial commands, this endpoint is **synchronous and hardware-confirmed**. The SV04 echoes each command back verbatim over RS232 within approximately 40–95 ms. The service waits for that echo before returning `200`. A `200` response means the switch hardware has genuinely acted, not merely that bytes were transmitted. Typical end-to-end latency is well under 100 ms; the internal echo timeout is 0.5 s.

#### Request body

```json
{
  "port": 2
}
```

| Field | Type    | Required | Constraints | Description                       |
|-------|---------|----------|-------------|-----------------------------------|
| `port`| integer | yes      | 1–4         | Target input (1-indexed)          |

> **Note on schema validation:** The underlying schema accepts values 1–8 (to support larger switches in other configurations). For the SV04, only 1–4 correspond to real hardware inputs. Sending 5–8 will be accepted by schema validation but will fail at the protocol layer.

#### Success response — `200 OK`

```json
{
  "status": "success",
  "message": "Switched to Port 2",
  "timestamp": "2025-06-01T12:00:00.123456+00:00"
}
```

| Field       | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| `status`    | string | Always `"success"` on 200                     |
| `message`   | string | Human-readable confirmation                    |
| `timestamp` | string | UTC ISO 8601 timestamp of the response         |

#### Error responses

See the [Error Handling](#error-handling) section for full details.

| Status | Condition                                                    |
|--------|--------------------------------------------------------------|
| `400`  | Port out of range, or baud rate mismatch (no bytes written)  |
| `422`  | Malformed request body (Pydantic validation failure)         |
| `503`  | Switch did not acknowledge — hardware needs attention        |

#### `curl` example

```bash
curl -X POST http://<host>:8000/api/v1/switch \
  -H "Content-Type: application/json" \
  -d '{"port": 2}'
```

---

### `GET /api/v1/status`

Returns the health status of the service and the current serial connection state.

**Always returns `200 OK`.** Check the `status` field in the body to determine whether the service is healthy.

#### Response — `200 OK`

```json
{
  "status": "healthy",
  "connected": true,
  "port": "/dev/ttyUSB0",
  "baudrate": 115200,
  "protocol": "sv04",
  "terminator": "none",
  "active_port": null,
  "available_ports": ["/dev/ttyUSB0"]
}
```

| Field             | Type           | Description                                                                                     |
|-------------------|----------------|-------------------------------------------------------------------------------------------------|
| `status`          | string         | `"healthy"` (connected), `"degraded"` (reconnect attempted), or `"unhealthy"` (cannot connect) |
| `connected`       | boolean        | Whether the serial port is open                                                                 |
| `port`            | string         | Serial device path, e.g. `/dev/ttyUSB0`                                                        |
| `baudrate`        | integer        | Current baud rate; must be `115200` for SV04                                                   |
| `protocol`        | string         | Active protocol; must be `"sv04"` for this device                                              |
| `terminator`      | string         | Active line terminator; must be `"none"` for SV04                                              |
| `active_port`     | integer\|null  | Last confirmed active input (1–4); `null` until the first successful switch after startup      |
| `available_ports` | array[string]  | List of detected serial devices on the host                                                    |

> **Handling `active_port: null`:** The service does not query the switch for its current state at startup. `active_port` remains `null` until a `POST /api/v1/switch` completes successfully and the echo is received. Integrators must handle `null` and must not assume any particular input is active on a fresh service start.

#### `curl` example

```bash
curl http://<host>:8000/api/v1/status
```

---

### `POST /api/v1/config`

> **Advanced — strongly discouraged for SV04 deployments.** Read this section carefully before using.

Updates the service's serial configuration at runtime (protocol, baud rate, or line terminator).

For SV04 deployments, configuration should be set once via environment variables at service startup:

```
PROTOCOL=sv04
BAUD_RATE=115200
```

The service automatically defaults to 115200 baud when the `sv04` protocol is selected.

**Why this endpoint is dangerous for the SV04:**

Changing the baud rate to anything other than 115200 will cause all subsequent switch commands to be sent at the wrong baud rate. The SV04's RS232 controller interprets framing garbage and latches up, stopping all further communication until the switch is **physically power-cycled**. The service has a pre-flight guard that refuses to transmit at the wrong baud (returns `400` without writing any bytes), but the config change itself still takes effect — leaving the service configuration in a broken state even though no bytes were written to the switch.

If you do use this endpoint, always pair a protocol change with an explicit `"baudrate": 115200`.

#### Request body

All fields are optional. Omit any field to leave it unchanged.

```json
{
  "protocol": "sv04",
  "baudrate": 115200,
  "terminator": "none"
}
```

| Field        | Type    | Allowed values                                                              |
|--------------|---------|-----------------------------------------------------------------------------|
| `protocol`   | string  | `"sv04"`, `"enterprise"`, `"consumer_a"`, `"consumer_b"`, `"matrix"`, `"dual_monitor_hex"`, `"hdc202_x24"` |
| `baudrate`   | integer | `9600`, `19200`, `38400`, `57600`, `115200`                                 |
| `terminator` | string  | `"none"`, `"cr"`, `"lf"`, `"crlf"`                                         |

#### Success response — `200 OK`

```json
{
  "status": "success",
  "message": "Protocol set to sv04, Baudrate set to 115200",
  "timestamp": "2025-06-01T12:00:00.123456+00:00"
}
```

Same `SuccessResponse` shape as `/api/v1/switch`.

#### Error responses

| Status | Condition                                      |
|--------|------------------------------------------------|
| `400`  | Invalid protocol, baudrate, or terminator value |
| `503`  | Serial reconnection after baud rate change failed |

---

## Endpoints not applicable to the SV04

The following endpoints exist in this service to support other switch families. They all return **`501 Not Implemented`** when the active protocol is `sv04`. Do not call them for SV04 deployments.

| Endpoint                     | Purpose for other devices          |
|------------------------------|------------------------------------|
| `POST /api/v1/buzzer`        | Toggle audible buzzer              |
| `POST /api/v1/light`         | LED lighting mode                  |
| `POST /api/v1/fan`           | Fan speed mode                     |
| `POST /api/v1/audio/source`  | Select audio input                 |
| `POST /api/v1/audio/follow`  | Toggle audio-follow-video          |
| `POST /api/v1/network`       | Per-port network power             |
| `POST /api/v1/usb/focus`     | USB keyboard/mouse focus           |
| `POST /api/v1/usb/compatibility` | USB compatibility mode         |
| `POST /api/v1/usb/mouse-middle`  | Mouse middle-button switching  |
| `POST /api/v1/system/autodetect` | Auto-detect computer presence  |
| `POST /api/v1/system/autoscan`   | Auto-scan inputs                |
| `POST /api/v1/query`         | Send a device query command        |

---

## Error Handling

### Response body shapes

There are two distinct error body shapes depending on what raised the error:

**Shape A — application errors (4xx and 5xx from route logic):**

These are raised internally via FastAPI's `HTTPException` and serialized by FastAPI as:

```json
{
  "detail": "Human-readable description of what went wrong."
}
```

**Shape B — unhandled exceptions (500 only):**

Caught by the global exception handler and serialized as:

```json
{
  "status": "error",
  "code": "INTERNAL_ERROR",
  "detail": "Exception message"
}
```

**Shape C — Pydantic validation errors (422 only):**

Serialized by FastAPI as a structured object with a `detail` array:

```json
{
  "detail": [
    {
      "type": "...",
      "loc": ["body", "port"],
      "msg": "...",
      "input": ...
    }
  ]
}
```

For `400`, `501`, and `503` errors, parse `response.detail` as a plain string (Shape A). For `422`, parse `response.detail` as an array (Shape C).

---

### Status codes

#### `400 Bad Request`

Invalid input that was rejected before any bytes were written to the switch.

**Port out of range:**

```json
{ "detail": "Invalid port ID: 5. Must be between 1 and 4." }
```

**Wrong baud rate — hardware protection guard:**

```json
{
  "detail": "SV04 requires 115200 baud but the port is at 9600. Refusing to send: traffic at the wrong baud rate latches up the switch's RS232 controller and it then needs a power cycle."
}
```

This guard fires when the service's configured baud rate does not match the SV04's required 115200. **No bytes are written to the serial port.** The switch is unaffected. To recover: call `POST /api/v1/config` with `{"baudrate": 115200}`, then retry the switch command.

---

#### `422 Unprocessable Entity`

FastAPI/Pydantic validation failed before the request reached application logic. Common causes: wrong field type, missing required field, or value outside the schema's allowed range.

```json
{
  "detail": [
    {
      "type": "int_parsing_error",
      "loc": ["body", "port"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "two"
    }
  ]
}
```

Unlike `400`, a `422` means the request body was structurally invalid. Fix the request before retrying.

---

#### `501 Not Implemented`

The requested command is not supported by the active protocol. For the SV04, this is returned by all non-switch endpoints (buzzer, audio, queries, etc.).

```json
{ "detail": "Buzzer control not supported" }
```

Do not retry. The command is not applicable to this device.

---

#### `503 Service Unavailable`

Hardware communication failed. For the SV04, the most common cause is that the switch's echo was not received within the 0.5 s timeout — which typically means the RS232 controller has latched up.

```json
{
  "detail": "Hardware communication failed: SV04 did not acknowledge the switch to input 1. The switch's RS232 controller may have latched up - power-cycle the switch. Check the DB9 is seated and no other process holds the serial port."
}
```

**Recovery:** Power-cycle the physical SV04 switch. Retrying the API call without doing so will not help — the switch will not respond until it is power-cycled. Treat `503` as "needs human intervention", not as a transient network error.

A `503` can also appear if the controller service failed to initialize (e.g., the USB-to-serial adapter is unplugged):

```json
{ "detail": "Controller service not initialized (Hardware offline?)" }
```

In this case, check that the RS232 adapter is connected and restart the service.

---

## Code Examples

### Python (`requests`)

```python
import requests

BASE_URL = "http://<host>:8000"

def switch_input(port: int) -> dict:
    """
    Switch the SV04 to the given input (1-4).
    Returns the parsed response body.
    Raises RuntimeError on any error.
    """
    resp = requests.post(f"{BASE_URL}/api/v1/switch", json={"port": port}, timeout=5)

    if resp.status_code == 200:
        return resp.json()

    # All application errors (400, 501, 503) use {"detail": "..."}
    # 422 uses {"detail": [...]}, but str() on the list is still useful.
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text

    raise RuntimeError(f"Switch to port {port} failed [{resp.status_code}]: {detail}")


# Example usage
try:
    result = switch_input(2)
    print(f"Success: {result['message']}")
except RuntimeError as e:
    print(f"Error: {e}")
```

---

### JavaScript (`fetch`)

```javascript
const BASE_URL = "http://<host>:8000";

async function switchInput(port) {
  // Switch the SV04 to the given input (1-4).
  // Returns the parsed response body on success.
  // Throws an Error with a descriptive message on failure.

  const response = await fetch(`${BASE_URL}/api/v1/switch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ port }),
  });

  const body = await response.json().catch(() => ({ detail: response.statusText }));

  if (!response.ok) {
    // Application errors use body.detail (string or array).
    const detail = Array.isArray(body.detail)
      ? JSON.stringify(body.detail)
      : body.detail ?? response.statusText;
    throw new Error(`Switch to port ${port} failed [${response.status}]: ${detail}`);
  }

  return body;
}

// Example usage
switchInput(2)
  .then((result) => console.log("Success:", result.message))
  .catch((err) => console.error("Error:", err.message));
```

---

## Operational Caveats

**Switching away from your own host will disconnect your input devices.**

Any keyboard and mouse connected to the SV04's shared USB hub will follow the active input. If the machine making API calls is connected to one of the switch's inputs, switching to a different input will physically detach that machine's keyboard and mouse from the USB bus. If that machine is accessed only locally (not over SSH or another network connection), you will lose the ability to type or click until you switch back.

If you automate input switching, ensure you have an independent path to recover control (e.g., SSH access from another machine, or logic that always switches back to a known safe input before exiting).

---

## Environment Variables

The service reads these at startup. Restart the service after changing them.

| Variable      | Default  | Description                                      |
|---------------|----------|--------------------------------------------------|
| `PROTOCOL`    | —        | Set to `sv04` for this device                    |
| `BAUD_RATE`   | `9600`   | Set to `115200` for this device                  |
| `SERIAL_PORT` | `AUTO`   | Device path (e.g. `/dev/ttyUSB0`) or `AUTO` to auto-discover |

For SV04, always set both `PROTOCOL=sv04` and `BAUD_RATE=115200`. Omitting either will cause the first switch command to be sent with the wrong framing, which latches up the SV04's RS232 controller and requires a power cycle to recover.
