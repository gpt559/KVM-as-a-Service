import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class ProtocolHandler:
    """
    Handles packet construction and validation for TESmart KVM protocols.
    Currently optimized for HDC202-X24 protocol.
    """
    
    HEADER = b'\xAA\xBB'

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """
        Calculates the checksum for the given data bytes.
        Checksum is the sum of all bytes modulo 256.
        """
        return sum(data) & 0xFF

    @staticmethod
    def build_packet(cmd: int, data: List[int]) -> bytes:
        """
        Constructs a full command packet including header and checksum.
        
        Args:
            cmd: The command byte (e.g., 0x03 for switch).
            data: List of data bytes.
            
        Returns:
            bytes: The complete packet.
        """
        # Structure: Header (2) + Cmd (1) + Data (N) + Checksum (1)
        # Note: The CSV shows structure as AA BB [CMD] [DATA...] [CS]
        # Checksum covers AA BB + CMD + DATA
        
        payload = bytes([cmd] + data)
        raw_packet = ProtocolHandler.HEADER + payload
        checksum = ProtocolHandler.calculate_checksum(raw_packet)
        return raw_packet + bytes([checksum])

    @staticmethod
    def validate_packet(packet: bytes) -> bool:
        """
        Validates the checksum of a received packet.
        """
        if len(packet) < 4: # Min: AA BB CMD CS
            return False
            
        if not packet.startswith(ProtocolHandler.HEADER):
            return False
            
        data_part = packet[:-1]
        received_checksum = packet[-1]
        calculated_checksum = ProtocolHandler.calculate_checksum(data_part)
        
        if calculated_checksum != received_checksum:
            logger.warning(f"Checksum mismatch! Calc: {calculated_checksum:02X}, Recv: {received_checksum:02X}")
            return False
            
        return True

    @staticmethod
    def extract_payload(packet: bytes) -> Optional[bytes]:
        """
        Extracts the payload (Cmd + Data) from a validated packet.
        Removes Header and Checksum.
        """
        if not ProtocolHandler.validate_packet(packet):
            return None
            
        # Remove Header (2 bytes) and Checksum (1 byte)
        return packet[2:-1]

    @staticmethod
    def try_parse_packet(buffer: bytes) -> tuple[Optional[bytes], bytes]:
        """
        Attempts to parse a single valid packet from the beginning of the buffer.
        
        Returns:
            (packet, remaining_buffer)
            If no full packet is found, packet is None.
            If invalid data is at the start, it is discarded.
        """
        # 1. Find Header
        header_idx = buffer.find(ProtocolHandler.HEADER)
        if header_idx == -1:
            # Keep the last byte just in case it's the start of a header (0xAA)
            if len(buffer) > 0 and buffer[-1] == 0xAA:
                return None, buffer[-1:]
            return None, b""
        
        # Discard garbage before header
        if header_idx > 0:
            logger.debug(f"Discarding {header_idx} bytes of garbage: {buffer[:header_idx].hex()}")
            buffer = buffer[header_idx:]

        # Minimum length check (Header + Cmd + Len + CS = 5 bytes?)
        # Let's assume min packet is 6 bytes just to be safe based on CSV (AA BB CMD LEN DATA CS)
        if len(buffer) < 5:
            return None, buffer
            
        # Parse Length
        # Assumption for Responses: Byte 3 (index 3) is Data Length.
        # Packet structure: AA BB [CMD] [LEN] [DATA...] [CS]
        # Total Length = 2 + 1 + 1 + LEN + 1 = 5 + LEN
        
        data_len = buffer[3]
        expected_total_len = 5 + data_len
        
        # Sanity check on length to avoid huge allocation or error
        if data_len > 64:
            # Likely invalid length byte, skip header
            return None, buffer[2:]

        if len(buffer) >= expected_total_len:
            candidate = buffer[:expected_total_len]
            if ProtocolHandler.validate_packet(candidate):
                return candidate, buffer[expected_total_len:]
            else:
                # Validation failed. Corrupt packet or wrong structure.
                # Advance past Header to search again
                return None, buffer[2:]
             
        # Not enough bytes yet
        return None, buffer
