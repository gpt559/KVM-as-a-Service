# KVM Serial Protocol Specification

## Connection Settings
*   **Baud Rate:** 9600 bps
*   **Data Bits:** 8
*   **Stop Bits:** 1
*   **Parity:** None
*   **Flow Control:** None

## Protocol Format (HDC202-X24)
This protocol uses a dynamic checksum.
**Format:** `0xAA 0xBB [CMD] [PAYLOAD...] [CS]`

*   **Header:** `0xAA 0xBB`
*   **CMD:** Command Identifier (1 byte)
*   **Payload:** Variable length data (usually 2 bytes for requests)
*   **Checksum (CS):** Sum of all preceding bytes (including Header, CMD, Payload) modulo 256 (`Sum & 0xFF`).

## Key Commands

### Switching
| Action | CMD | Payload | Example (Calculated CS) |
| :--- | :--- | :--- | :--- |
| Switch to PC1 | `0x03` | `0x00 0x00` | `AA BB 03 00 00 68` |
| Switch to PC2 | `0x03` | `0x00 0x01` | `AA BB 03 00 01 69` |
| Next PC | `0x03` | `0xFF 0x00` | `AA BB 03 FF 00 67` |

### Buzzer
| Action | CMD | Payload | Example |
| :--- | :--- | :--- | :--- |
| Buzzer OFF | `0x04` | `0x00 0x00` | `AA BB 04 00 00 69` |
| Buzzer ON | `0x04` | `0x00 0x01` | `AA BB 04 00 01 6A` |

### Queries
Queries send a command and expect a response packet.
| Query | CMD | Payload | Response CMD |
| :--- | :--- | :--- | :--- |
| Monitor Count | `0x81` | `0x00 0x00` | `0x81` |
| Mapping Info | `0x83` | `0x00 0xFF` | `0x83` |
| Buzzer Status | `0x84` | `0x00 0xFF` | `0x84` |

## Legacy Protocol (Enterprise)
*Supported for backward compatibility via configuration.*
Format: `0xAA 0xBB 0x03 0x01 [PortID] 0xEE`
