from enum import Enum

class Protocol(str, Enum):
    ENTERPRISE = "enterprise"
    CONSUMER_A = "consumer_a"
    CONSUMER_B = "consumer_b"
    MATRIX = "matrix"
    DUAL_MONITOR_HEX = "dual_monitor_hex"
    HDC202_X24 = "hdc202_x24"

class EnterpriseCommands:
    """
    Original Enterprise Protocol (4-Port models)
    Format: 0xAA 0xBB 0x03 0x01 <PortID> 0xEE
    """
    SWITCH_PORT_1 = b'\xAA\xBB\x03\x01\x01\xEE'
    SWITCH_PORT_2 = b'\xAA\xBB\x03\x01\x02\xEE'
    SWITCH_PORT_3 = b'\xAA\xBB\x03\x01\x03\xEE'
    SWITCH_PORT_4 = b'\xAA\xBB\x03\x01\x04\xEE'
    SWITCH_PORT_5 = b'\xAA\xBB\x03\x01\x05\xEE'
    SWITCH_PORT_6 = b'\xAA\xBB\x03\x01\x06\xEE'
    SWITCH_PORT_7 = b'\xAA\xBB\x03\x01\x07\xEE'
    SWITCH_PORT_8 = b'\xAA\xBB\x03\x01\x08\xEE'

    BUZZER_ON     = b'\xAA\xBB\x03\x02\x01\xEE'
    BUZZER_OFF    = b'\xAA\xBB\x03\x02\x00\xEE'

class ConsumerACommands:
    """
    Alternative Protocol A (Keypad Emulation)
    Format: 0x55 0x01 <PortID> 0x00
    """
    SWITCH_PORT_1 = b'\x55\x01\x01\x00'
    SWITCH_PORT_2 = b'\x55\x01\x02\x00'
    SWITCH_PORT_3 = b'\x55\x01\x03\x00'
    SWITCH_PORT_4 = b'\x55\x01\x04\x00'
    
class ConsumerBCommands:
    """
    Alternative Protocol B (Routing Command)
    Format: 0xAA 0xBB 0x03 0x01 0x1<PortID> 0xEE (assuming Output A is fixed at 1)
    """
    SWITCH_PORT_1 = b'\xAA\xBB\x03\x01\x11\xEE'
    SWITCH_PORT_2 = b'\xAA\xBB\x03\x01\x12\xEE'
    SWITCH_PORT_3 = b'\xAA\xBB\x03\x01\x13\xEE'
    SWITCH_PORT_4 = b'\xAA\xBB\x03\x01\x14\xEE'

    BUZZER_ON     = b'\xAA\xBB\x03\x02\x01\xEE'
    BUZZER_OFF    = b'\xAA\xBB\x03\x02\x00\xEE'

class MatrixCommands:
    """
    Matrix ASCII Protocol
    Format: MT00SW[Input][Output]NT
    Output: 00 (All Monitors), 01 (Monitor A), 02 (Monitor B)
    """
    # Assuming switching ALL monitors (00) for standard behavior
    SWITCH_PORT_1 = b'MT00SW0100NT'
    SWITCH_PORT_2 = b'MT00SW0200NT'
    # Adding more if needed, assuming PC1=01, PC2=02. 
    # Spec only mentions PC1/PC2 but 8-port switch would follow pattern
    SWITCH_PORT_3 = b'MT00SW0300NT'
    SWITCH_PORT_4 = b'MT00SW0400NT'
    SWITCH_PORT_5 = b'MT00SW0500NT'
    SWITCH_PORT_6 = b'MT00SW0600NT'
    SWITCH_PORT_7 = b'MT00SW0700NT'
    SWITCH_PORT_8 = b'MT00SW0800NT'

    BUZZER_ON     = b'MT00BZM01NT'
    BUZZER_OFF    = b'MT00BZM00NT'

class DualMonitorHexCommands:
    """
    Dual-Monitor Hex Protocol (Variant)
    Format: 0xAA 0xBB 0x03 0x1<Output> 0x0<Input> 0xEE
    """
    # Switching Output A (0x10) - assuming primary display
    SWITCH_PORT_1 = b'\xAA\xBB\x03\x10\x01\xEE'
    SWITCH_PORT_2 = b'\xAA\xBB\x03\x10\x02\xEE'
    SWITCH_PORT_3 = b'\xAA\xBB\x03\x10\x03\xEE'
    SWITCH_PORT_4 = b'\xAA\xBB\x03\x10\x04\xEE'
    # ... continuing pattern for 8 ports
    SWITCH_PORT_5 = b'\xAA\xBB\x03\x10\x05\xEE'
    SWITCH_PORT_6 = b'\xAA\xBB\x03\x10\x06\xEE'
    SWITCH_PORT_7 = b'\xAA\xBB\x03\x10\x07\xEE'
    SWITCH_PORT_8 = b'\xAA\xBB\x03\x10\x08\xEE'

    BUZZER_ON     = b'\xAA\xBB\x03\x02\x01\xEE'
    BUZZER_OFF    = b'\xAA\xBB\x03\x02\x00\xEE'

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

# Map protocols to their command classes
PROTOCOL_MAP = {
    Protocol.ENTERPRISE: EnterpriseCommands,
    Protocol.CONSUMER_A: ConsumerACommands,
    Protocol.CONSUMER_B: ConsumerBCommands,
    Protocol.MATRIX: MatrixCommands,
    Protocol.DUAL_MONITOR_HEX: DualMonitorHexCommands,
    Protocol.HDC202_X24: HDC202X24Commands,
}
