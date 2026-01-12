# Update Plan: Integrate HDC202-X24 Protocol

## Objective
Incorporate the new KVM control codes provided in `External_Button_Board_Command_Test_EN_CSV.csv` into the application. This will allow the `KVM-as-a-Service` application to control the specific switch model (likely HDC202-X24) using the correct hex commands.

## Analysis
The provided CSV introduces a new hex protocol structure starting with header `AA BB`.
- **Switching**: Supports switching "All Outputs" to a specific PC (1-4).
- **Buzzer**: Supports enabling/disabling the buzzer.
- **Verification**: The checksum logic appears to be `Sum(Cmd, Data1, Data2) + 0x65` (approximate), but exact hex codes are provided and will be used directly.

### Mapping
| Action | CSV Description | Hex Code | Constant Name |
| :--- | :--- | :--- | :--- |
| Switch to Port 1 | Switch all outputs to PC1 | `AA BB 03 00 00 68` | `SWITCH_PORT_1` |
| Switch to Port 2 | Switch all outputs to PC2 | `AA BB 03 00 01 69` | `SWITCH_PORT_2` |
| Switch to Port 3 | Switch all outputs to PC3 | `AA BB 03 00 02 6A` | `SWITCH_PORT_3` |
| Switch to Port 4 | Switch all outputs to PC4 | `AA BB 03 00 03 6B` | `SWITCH_PORT_4` |
| Buzzer On | Enable buzzer | `AA BB 04 00 01 6A` | `BUZZER_ON` |
| Buzzer Off | Disable buzzer | `AA BB 04 00 00 69` | `BUZZER_OFF` |

## Changes Required

### 1. Modify `src/constants.py`

1.  **Update `Protocol` Enum**:
    Add `HDC202_X24 = "hdc202_x24"` to the `Protocol` class.

2.  **Add `HDC202X24Commands` Class**:
    Create a new class to hold the byte sequences.
    ```python
    class HDC202X24Commands:
        """
        Protocol for HDC202-X24 and compatible models.
        Source: External_Button_Board_Command_Test_EN_CSV.csv
        Format: 0xAA 0xBB [CMD] [DATA1] [DATA2] [CHECKSUM]
        """
        # Switch all outputs to specific PC
        SWITCH_PORT_1 = b'\xAA\xBB\x03\x00\x00\x68'
        SWITCH_PORT_2 = b'\xAA\xBB\x03\x00\x01\x69'
        SWITCH_PORT_3 = b'\xAA\xBB\x03\x00\x02\x6A'
        SWITCH_PORT_4 = b'\xAA\xBB\x03\x00\x03\x6B'

        BUZZER_ON     = b'\xAA\xBB\x04\x00\x01\x6A'
        BUZZER_OFF    = b'\xAA\xBB\x04\x00\x00\x69'
    ```

3.  **Update `PROTOCOL_MAP`**:
    Register the new class in the mapping dictionary.
    ```python
    PROTOCOL_MAP = {
        # ... existing ...
        Protocol.HDC202_X24: HDC202X24Commands,
    }
    ```

## Verification
1.  Restart the service (or auto-reload).
2.  Use the API to update the configuration to the new protocol:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/config" -H "Content-Type: application/json" -d '{"protocol": "hdc202_x24"}'
    ```
3.  Test switching ports:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/switch" -H "Content-Type: application/json" -d '{"port": 1}'
    ```
