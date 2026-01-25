# Refactor Serial Protocol Implementation

## Status
**Current State:** Functional but inefficient.
**Issues Identified:**
1.  **Blocking Reads:** `send_query` uses `read(128)` which blocks for the full timeout (default 1.0s) even if data arrives instantly. This makes the UI feel sluggish.
2.  **Concurrency/Race Condition:** `send_query` flushes the input buffer (`reset_input_buffer`), potentially deleting asynchronous events (like manual button presses) that happened just before the call.
3.  **Hardcoded Commands:** `src/constants.py` contains hardcoded byte strings. This is error-prone and hard to maintain. Checksums should be calculated dynamically.
4.  **Rigid Protocol:** The code assumes `HDC202_X24` structure mostly, but the codebase supports multiple protocols.

## Proposed Changes

### 1. Dynamic Command Generation (`src/protocol_handler.py`)
Create a new module to handle byte manipulation.

```python
class ProtocolHandler:
    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        return sum(data) & 0xFF

    @staticmethod
    def build_command(cmd: int, data: list[int]) -> bytes:
        # Header: AA BB
        # Body: [CMD] [DATA...]
        # Checksum
        payload = bytes([cmd] + data)
        checksum = ProtocolHandler.calculate_checksum(b'\xAA\xBB' + payload)
        return b'\xAA\xBB' + payload + bytes([checksum])
```

### 2. Smart Serial Reading (`src/serial_manager.py`)
Refactor `read` to be smarter. Instead of `read(128)`, we should try to read the header, then determine the packet length if possible, or read until a silence timeout.

For `HDC202_X24`, packets seem to be variable length but often small.
A `read_packet` method could:
1.  Read 2 bytes. Check if `AA BB`.
2.  If yes, read the rest.
3.  Since we don't have a perfect length byte in all packets, we might need a short "inter-byte timeout" read.

### 3. Thread-Safe Controller (`src/controller_service.py`)
Switch to a producer-consumer model for queries to avoid race conditions.

**New Flow:**
1.  **Monitor Thread:** constantly reads from serial.
    -   Parses complete packets.
    -   Checks if the packet matches a "pending query".
    -   If yes, puts the result in a thread-safe Queue/Future for the waiting main thread.
    -   If no, processes it as an async status update (Event).
2.  **Send Query:**
    -   Constructs command.
    -   Registers a "pending query" ID (e.g., the command byte).
    -   Sends command.
    -   Waits on the Future (with timeout).
    -   Returns result.

### 4. Constants Cleanup (`src/constants.py`)
Remove `b'\xAA\xBB...'` constants. Replace with:
```python
CMD_SWITCH_PORT = 0x03
CMD_BUZZER = 0x04
...
```

## Benefits
-   **Speed:** Queries will return immediately upon receiving data (10-50ms vs 1000ms).
-   **Reliability:** No lost events due to buffer flushing.
-   **Maintainability:** Easier to add new commands without manual hex math.
