import pytest
from src.constants import HDC202X24Commands

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
    assert HDC202X24Commands.QUERY_MONITOR_COUNT == expected, \
        f"Golden Command mismatch! Expected {expected.hex(' ').upper()}, got {HDC202X24Commands.QUERY_MONITOR_COUNT.hex(' ').upper()}"

def test_blind_commands_match_instructions():
    """
    Verifies the 'Blind Test' commands (Buzzer) match the testing instructions exactly.
    Mute: AA BB 04 00 00 69
    Enable: AA BB 04 00 01 6A
    """
    expected_mute = b'\xAA\xBB\x04\x00\x00\x69'
    assert HDC202X24Commands.BUZZER_OFF == expected_mute, \
        f"Buzzer Mute mismatch! Expected {expected_mute.hex(' ').upper()}, got {HDC202X24Commands.BUZZER_OFF.hex(' ').upper()}"

    expected_enable = b'\xAA\xBB\x04\x00\x01\x6A'
    assert HDC202X24Commands.BUZZER_ON == expected_enable, \
        f"Buzzer Enable mismatch! Expected {expected_enable.hex(' ').upper()}, got {HDC202X24Commands.BUZZER_ON.hex(' ').upper()}"

def test_switch_commands_match_instructions():
    """
    Verifies the Switch commands match the testing instructions exactly.
    Switch to PC1: AA BB 03 00 00 68
    Switch to PC2: AA BB 03 00 01 69
    Switch to Next: AA BB 03 FF 00 67
    """
    expected_pc1 = b'\xAA\xBB\x03\x00\x00\x68'
    assert HDC202X24Commands.SWITCH_PORT_1 == expected_pc1, \
        f"Switch PC1 mismatch! Expected {expected_pc1.hex(' ').upper()}, got {HDC202X24Commands.SWITCH_PORT_1.hex(' ').upper()}"

    expected_pc2 = b'\xAA\xBB\x03\x00\x01\x69'
    assert HDC202X24Commands.SWITCH_PORT_2 == expected_pc2, \
        f"Switch PC2 mismatch! Expected {expected_pc2.hex(' ').upper()}, got {HDC202X24Commands.SWITCH_PORT_2.hex(' ').upper()}"

    expected_next = b'\xAA\xBB\x03\xFF\x00\x67'
    assert HDC202X24Commands.SWITCH_ALL_NEXT == expected_next, \
        f"Switch Next mismatch! Expected {expected_next.hex(' ').upper()}, got {HDC202X24Commands.SWITCH_ALL_NEXT.hex(' ').upper()}"

def test_light_commands_match_instructions():
    """
    Verifies the Light Effect commands match the testing instructions exactly.
    Off: AA BB 05 02 00 6C
    Basic: AA BB 05 02 01 6D
    Flow: AA BB 05 02 02 6E
    Breathing: AA BB 05 02 03 6F
    """
    expected_off = b'\xAA\xBB\x05\x02\x00\x6C'
    assert HDC202X24Commands.LIGHT_OFF == expected_off, \
        f"Light Off mismatch! Expected {expected_off.hex(' ').upper()}, got {HDC202X24Commands.LIGHT_OFF.hex(' ').upper()}"

    expected_basic = b'\xAA\xBB\x05\x02\x01\x6D'
    assert HDC202X24Commands.LIGHT_BASIC == expected_basic, \
        f"Light Basic mismatch! Expected {expected_basic.hex(' ').upper()}, got {HDC202X24Commands.LIGHT_BASIC.hex(' ').upper()}"

    expected_flow = b'\xAA\xBB\x05\x02\x02\x6E'
    assert HDC202X24Commands.LIGHT_FLOW == expected_flow, \
        f"Light Flow mismatch! Expected {expected_flow.hex(' ').upper()}, got {HDC202X24Commands.LIGHT_FLOW.hex(' ').upper()}"

    expected_breathing = b'\xAA\xBB\x05\x02\x03\x6F'
    assert HDC202X24Commands.LIGHT_BREATHING == expected_breathing, \
        f"Light Breathing mismatch! Expected {expected_breathing.hex(' ').upper()}, got {HDC202X24Commands.LIGHT_BREATHING.hex(' ').upper()}"

def test_checksum_validity_all_commands():
    """
    Iterates through all commands in HDC202X24Commands and verifies their checksums are mathematically correct.
    This ensures no typos in the hardcoded constants.
    """
    # Get all attributes of the class
    for attr_name in dir(HDC202X24Commands):
        # Skip internal attributes
        if attr_name.startswith("__"):
            continue
        
        value = getattr(HDC202X24Commands, attr_name)
        
        # We only care about bytes that look like protocol commands (start with AA BB)
        if isinstance(value, bytes) and value.startswith(b'\xAA\xBB'):
            # Calculate expected checksum
            expected_checksum = calculate_checksum(value)
            actual_checksum = value[-1]
            
            assert actual_checksum == expected_checksum, \
                f"Checksum mismatch in {attr_name}! Cmd: {value.hex(' ').upper()}. Calculated: {hex(expected_checksum)}, Found: {hex(actual_checksum)}"
