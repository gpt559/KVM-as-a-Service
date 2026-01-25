from src.constants import HDC202X24Commands
from src.protocol_handler import ProtocolHandler

def calculate_checksum(command_bytes: bytes) -> int:
    """
    Calculates the checksum for a command.
    Formula: Sum of all previous bytes, keeping only the lower 8 bits (modulo 256).
    """
    # Exclude the last byte (which is the checksum itself)
    payload = command_bytes[:-1]
    return sum(payload) % 256

def test_golden_command_matches_instructions():
    """
    Verifies the 'Golden Test' command (Query Monitor Status) matches the testing instructions exactly.
    Expected: AA BB 81 00 00 E6
    """
    expected = b'\xAA\xBB\x81\x00\x00\xE6'
    # CMD 0x81, Payload 00 00
    actual = ProtocolHandler.build_packet(HDC202X24Commands.CMD_QUERY_MONITOR_COUNT, [0x00, 0x00])
    
    assert actual == expected, \
        f"Golden Command mismatch! Expected {expected.hex(' ').upper()}, got {actual.hex(' ').upper()}"

def test_blind_commands_match_instructions():
    """
    Verifies the 'Blind Test' commands (Buzzer) match the testing instructions exactly.
    Mute: AA BB 04 00 00 69
    Enable: AA BB 04 00 01 6A
    """
    expected_mute = b'\xAA\xBB\x04\x00\x00\x69'
    actual_mute = ProtocolHandler.build_packet(HDC202X24Commands.CMD_BUZZER, [0x00, 0x00])
    
    assert actual_mute == expected_mute, \
        f"Buzzer Mute mismatch! Expected {expected_mute.hex(' ').upper()}, got {actual_mute.hex(' ').upper()}"

    expected_enable = b'\xAA\xBB\x04\x00\x01\x6A'
    actual_enable = ProtocolHandler.build_packet(HDC202X24Commands.CMD_BUZZER, [0x00, 0x01])

    assert actual_enable == expected_enable, \
        f"Buzzer Enable mismatch! Expected {expected_enable.hex(' ').upper()}, got {actual_enable.hex(' ').upper()}"

def test_switch_commands_match_instructions():
    """
    Verifies the Switch commands match the testing instructions exactly.
    Switch to PC1: AA BB 03 00 00 68
    Switch to PC2: AA BB 03 00 01 69
    Switch to Next: AA BB 03 FF 00 67
    """
    expected_pc1 = b'\xAA\xBB\x03\x00\x00\x68'
    actual_pc1 = ProtocolHandler.build_packet(HDC202X24Commands.CMD_SWITCH_PORT, [0x00, 0x00])
    assert actual_pc1 == expected_pc1, \
        f"Switch PC1 mismatch! Expected {expected_pc1.hex(' ').upper()}, got {actual_pc1.hex(' ').upper()}"

    expected_pc2 = b'\xAA\xBB\x03\x00\x01\x69'
    actual_pc2 = ProtocolHandler.build_packet(HDC202X24Commands.CMD_SWITCH_PORT, [0x00, 0x01])
    assert actual_pc2 == expected_pc2, \
        f"Switch PC2 mismatch! Expected {expected_pc2.hex(' ').upper()}, got {actual_pc2.hex(' ').upper()}"

    expected_next = b'\xAA\xBB\x03\xFF\x00\x67'
    actual_next = ProtocolHandler.build_packet(HDC202X24Commands.CMD_SWITCH_PORT, [0xFF, 0x00])
    assert actual_next == expected_next, \
        f"Switch Next mismatch! Expected {expected_next.hex(' ').upper()}, got {actual_next.hex(' ').upper()}"

def test_light_commands_match_instructions():
    """
    Verifies the Light Effect commands match the testing instructions exactly.
    Off: AA BB 05 02 00 6C
    Basic: AA BB 05 02 01 6D
    Flow: AA BB 05 02 02 6E
    Breathing: AA BB 05 02 03 6F
    """
    expected_off = b'\xAA\xBB\x05\x02\x00\x6C'
    actual_off = ProtocolHandler.build_packet(HDC202X24Commands.CMD_LIGHT, [0x02, 0x00])
    assert actual_off == expected_off, \
        f"Light Off mismatch! Expected {expected_off.hex(' ').upper()}, got {actual_off.hex(' ').upper()}"

    expected_basic = b'\xAA\xBB\x05\x02\x01\x6D'
    actual_basic = ProtocolHandler.build_packet(HDC202X24Commands.CMD_LIGHT, [0x02, 0x01])
    assert actual_basic == expected_basic, \
        f"Light Basic mismatch! Expected {expected_basic.hex(' ').upper()}, got {actual_basic.hex(' ').upper()}"

    expected_flow = b'\xAA\xBB\x05\x02\x02\x6E'
    actual_flow = ProtocolHandler.build_packet(HDC202X24Commands.CMD_LIGHT, [0x02, 0x02])
    assert actual_flow == expected_flow, \
        f"Light Flow mismatch! Expected {expected_flow.hex(' ').upper()}, got {actual_flow.hex(' ').upper()}"

    expected_breathing = b'\xAA\xBB\x05\x02\x03\x6F'
    actual_breathing = ProtocolHandler.build_packet(HDC202X24Commands.CMD_LIGHT, [0x02, 0x03])
    assert actual_breathing == expected_breathing, \
        f"Light Breathing mismatch! Expected {expected_breathing.hex(' ').upper()}, got {actual_breathing.hex(' ').upper()}"
