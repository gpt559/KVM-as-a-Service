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
    # --- Switching ---
    # Switch all outputs to specific PC
    SWITCH_PORT_1 = b'\xAA\xBB\x03\x00\x00\x68'
    SWITCH_PORT_2 = b'\xAA\xBB\x03\x00\x01\x69'
    SWITCH_PORT_3 = b'\xAA\xBB\x03\x00\x02\x6A'
    SWITCH_PORT_4 = b'\xAA\xBB\x03\x00\x03\x6B'
    SWITCH_ALL_NEXT = b'\xAA\xBB\x03\xFF\x00\x67'

    # Switch Specific Outputs (Output 1)
    SWITCH_OUT1_PC1 = b'\xAA\xBB\x03\x01\x00\x69'
    SWITCH_OUT1_PC2 = b'\xAA\xBB\x03\x01\x01\x6A'
    # Switch Specific Outputs (Output 2)
    SWITCH_OUT2_PC1 = b'\xAA\xBB\x03\x02\x00\x6A'
    SWITCH_OUT2_PC2 = b'\xAA\xBB\x03\x02\x01\x6B'

    # --- Audio/Video ---
    BUZZER_ON     = b'\xAA\xBB\x04\x00\x01\x6A'
    BUZZER_OFF    = b'\xAA\xBB\x04\x00\x00\x69'

    LIGHT_OFF       = b'\xAA\xBB\x05\x02\x00\x6C'
    LIGHT_BASIC     = b'\xAA\xBB\x05\x02\x01\x6D'
    LIGHT_FLOW      = b'\xAA\xBB\x05\x02\x02\x6E'
    LIGHT_BREATHING = b'\xAA\xBB\x05\x02\x03\x6F'

    AUDIO_FOLLOW_ON  = b'\xAA\xBB\x0C\x00\x01\x72'
    AUDIO_FOLLOW_OFF = b'\xAA\xBB\x0C\x00\x00\x71'
    
    AUDIO_PC1  = b'\xAA\xBB\x0D\x00\x00\x72'
    AUDIO_PC2  = b'\xAA\xBB\x0D\x00\x01\x73'
    AUDIO_PC3  = b'\xAA\xBB\x0D\x00\x02\x74'
    AUDIO_PC4  = b'\xAA\xBB\x0D\x00\x03\x75'
    AUDIO_NEXT = b'\xAA\xBB\x0D\xFF\x00\x71'

    # --- System & Hardware ---
    FAN_OFF  = b'\xAA\xBB\x0B\x00\x00\x70'
    FAN_AUTO = b'\xAA\xBB\x0B\x00\x01\x71'
    FAN_LOW  = b'\xAA\xBB\x0B\x00\x02\x72'
    FAN_HIGH = b'\xAA\xBB\x0B\x00\x03\x73'

    AUTODETECT_ON  = b'\xAA\xBB\x0E\x00\x01\x74'
    AUTODETECT_OFF = b'\xAA\xBB\x0E\x00\x00\x73'
    
    AUTOSCAN_ON  = b'\xAA\xBB\x0F\x00\x01\x75'
    AUTOSCAN_OFF = b'\xAA\xBB\x0F\x00\x00\x74'

    # --- USB & Input ---
    USB_FOCUS_PC1  = b'\xAA\xBB\x07\x00\x00\x6C'
    USB_FOCUS_PC2  = b'\xAA\xBB\x07\x00\x01\x6D'
    USB_FOCUS_NEXT = b'\xAA\xBB\x07\xFF\x00\x6B'

    USB_COMPAT_ON  = b'\xAA\xBB\x08\x00\x01\x6E'
    USB_COMPAT_OFF = b'\xAA\xBB\x08\x00\x00\x6D'

    MOUSE_MIDDLE_ON  = b'\xAA\xBB\x0A\x00\x01\x70'
    MOUSE_MIDDLE_OFF = b'\xAA\xBB\x0A\x00\x00\x6F'

    # --- Network Control ---
    # Note: ON commands seem to be shared (0F) for all PCs in CSV, likely "All On"
    # OFF commands are distinct.
    NET_PC1_ON  = b'\xAA\xBB\x09\x00\x0F\x7D'
    NET_PC1_OFF = b'\xAA\xBB\x09\x00\x0E\x7C'
    NET_PC2_ON  = b'\xAA\xBB\x09\x00\x0F\x7D'
    NET_PC2_OFF = b'\xAA\xBB\x09\x00\x0D\x7B'
    NET_PC3_ON  = b'\xAA\xBB\x09\x00\x0F\x7D'
    NET_PC3_OFF = b'\xAA\xBB\x09\x00\x0B\x79'
    NET_PC4_ON  = b'\xAA\xBB\x09\x00\x0F\x7D'
    NET_PC4_OFF = b'\xAA\xBB\x09\x00\x07\x75'

    # --- Queries ---
    QUERY_MONITOR_COUNT = b'\xAA\xBB\x81\x00\x00\xE6'
    QUERY_KM_FOCUS      = b'\xAA\xBB\x82\x00\xFF\xE6'
    QUERY_MAPPING       = b'\xAA\xBB\x83\x00\xFF\xE7'
    QUERY_BUZZER        = b'\xAA\xBB\x84\x00\xFF\xE8'
    QUERY_LIGHT         = b'\xAA\xBB\x85\x00\xFF\xE9'
    QUERY_USB_FOCUS     = b'\xAA\xBB\x87\x00\xFF\xEB'
    QUERY_USB_COMPAT    = b'\xAA\xBB\x88\x00\xFF\xEC'
    QUERY_NETWORK       = b'\xAA\xBB\x89\x00\xFF\xED'
    QUERY_MOUSE_MIDDLE  = b'\xAA\xBB\x8A\x00\xFF\xEE'
    QUERY_FAN           = b'\xAA\xBB\x8B\x00\xFF\xEF'
    QUERY_AUDIO_FOLLOW  = b'\xAA\xBB\x8C\x00\xFF\xF0'
    QUERY_AUDIO_CHANNEL = b'\xAA\xBB\x8D\x00\xFF\xF1'
    QUERY_AUTODETECT    = b'\xAA\xBB\x8E\x00\xFF\xF2'
    QUERY_AUTOSCAN      = b'\xAA\xBB\x8F\x00\xFF\xF3'

# Map protocols to their command classes
PROTOCOL_MAP = {
    Protocol.ENTERPRISE: EnterpriseCommands,
    Protocol.CONSUMER_A: ConsumerACommands,
    Protocol.CONSUMER_B: ConsumerBCommands,
    Protocol.MATRIX: MatrixCommands,
    Protocol.DUAL_MONITOR_HEX: DualMonitorHexCommands,
    Protocol.HDC202_X24: HDC202X24Commands,
}
