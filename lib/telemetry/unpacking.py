"""
Telemetry Unpacker for Ground Station (Standard Python)

Unpacks telemetry data according to telemetry_config.py definitions
"""

import struct
import datetime

# Import telemetry configuration and helpers
from lib.telemetry.telemetry_config import (
    HEARTBEAT_NOMINAL_FORMAT,
    TM_STORAGE_FORMAT,
    TM_HAL_FORMAT,
    FORMAT_FIXED_POINT_HP,
    FORMAT_FIXED_POINT_LP,
    MSG_ID_SAT_HEARTBEAT,
    MSG_ID_SAT_TM_HAL,
    MSG_ID_SAT_TM_STORAGE,
    MSG_ID_SAT_TM_NOMINAL,
    get_format_size,
    # Conversion helpers
    convert_fixed_point_to_float_hp,
    convert_fixed_point_to_float_lp,
)

TM_NOMINAL_SIZE = 211
TM_HAL_SIZE = 46
TM_STORAGE_SIZE = 74
TM_PAYLOAD_SIZE = 0



class TelemetryUnpacker:
    """
    Unpacks telemetry data from satellite using format definitions from telemetry_config.py
    """

    # Message ID to format mapping
    _FORMAT_MAP = {
        MSG_ID_SAT_HEARTBEAT: HEARTBEAT_NOMINAL_FORMAT,
        MSG_ID_SAT_TM_NOMINAL: HEARTBEAT_NOMINAL_FORMAT,
        MSG_ID_SAT_TM_HAL: TM_HAL_FORMAT,
        MSG_ID_SAT_TM_STORAGE: TM_STORAGE_FORMAT,
    }

    # Message ID to expected size mapping
    _SIZE_MAP = {
        MSG_ID_SAT_HEARTBEAT: TM_NOMINAL_SIZE,
        MSG_ID_SAT_TM_NOMINAL: TM_NOMINAL_SIZE,
        MSG_ID_SAT_TM_HAL: TM_HAL_SIZE,
        MSG_ID_SAT_TM_STORAGE: TM_STORAGE_SIZE,
    }

    # Source header parameters
    rx_src_id = 0x00
    rx_dst_id = 0x00

    # RX message parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    # File metadata parameters
    file_id = 0x0A
    file_time = 0
    file_size = 0x00
    file_target_sq = 0x00
    flag_rq_file = False
    filename = ""

    # File TX parameters
    gs_msg_sq = 0
    file_array = []

    @classmethod
    def _unpack_field(cls, msg, offset, field_format):
        """
        Unpack a single field from message bytes
        
        Args:
            msg: Message byte array
            offset: Current offset in message
            field_format: Format character ('B', 'h', 'I', 'X', etc.)
        
        Returns:
            tuple: (value, new_offset)
        """
        if field_format == FORMAT_FIXED_POINT_HP:
            byte_slice = msg[offset:offset + 4]
            value = convert_fixed_point_to_float_hp(byte_slice)
            return value, offset + 4
            
        elif field_format == FORMAT_FIXED_POINT_LP:
            byte_slice = msg[offset:offset + 4]
            value = convert_fixed_point_to_float_lp(byte_slice)
            return value, offset + 4
            
        else:
            # Standard struct format
            format_string = ">" + field_format
            size = struct.calcsize(format_string)
            value = struct.unpack(format_string, msg[offset:offset + size])[0]
            return value, offset + size

    @classmethod
    def unpack_frame(cls, msg_id, msg):
        """
        Parse message from satellite and unpack into dictionary format
        
        Args:
            msg_id: Message ID
            msg: Raw message bytes (including 4-byte header)
        
        Returns:
            dict: Parsed telemetry data organized by subsystem
        """
        # Get the format definition for this message
        data_format = cls._FORMAT_MAP.get(msg_id)
        if not data_format:
            print(f"\033[31m[COMMS ERROR] Unknown message ID: {msg_id}\033[0m")
            return {}

        # Verify message size
        expected_size = cls._SIZE_MAP.get(msg_id)
        if expected_size and cls.rx_msg_size != expected_size:
            print(f"\033[31m[COMMS ERROR] Message length incorrect. Expected {expected_size}, got {cls.rx_msg_size}\033[0m")

        # Skip 4-byte header (msg_id, seq_count, packet_length)
        msg = msg[4:]
        
        parsed_data = {}
        offset = 0

        # Unpack each subsystem
        for subsystem, fields in data_format.items():
            parsed_data[subsystem] = {}

            # Unpack each field
            for field_name, field_format in fields:
                try:
                    value, offset = cls._unpack_field(msg, offset, field_format)
                    parsed_data[subsystem][field_name] = value
                    
                    # Optional: Print unpacked values for debugging
                    # print(f"Unpacked {subsystem}.{field_name} ({field_format}): {value}")

                except Exception as e:
                    print(f"\u001b[31m[COMMS ERROR] Failed to unpack {subsystem}.{field_name}: {e}\u001b[0m")
                    parsed_data[subsystem][field_name] = None
                    # Skip this field's bytes
                    offset += get_format_size(field_format)

        print(f"Successfully unpacked {cls.get_message_name(msg_id)} telemetry")
        return parsed_data

    @classmethod
    def unpack_message_header(cls):
        """
        Unpack message header from received message
        
        Message structure:
        - Bytes 0-1: Source and destination IDs
        - Byte 2: Message ID
        - Bytes 3-4: Sequence count
        - Byte 5: Message size
        """
        # Get current timestamp
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode("utf-8")

        # Unpack source header
        cls.rx_src_id = int.from_bytes(cls.rx_message[0:1], byteorder="big")
        cls.rx_dst_id = int.from_bytes(cls.rx_message[1:2], byteorder="big")
        cls.rx_message = cls.rx_message[2:]

        print(f"Source Header: SRC={cls.rx_src_id}, DST={cls.rx_dst_id}")
        
        # Unpack message header
        cls.rx_msg_id = int.from_bytes(cls.rx_message[0:1], byteorder="big")
        cls.rx_msg_sq = int.from_bytes(cls.rx_message[1:3], byteorder="big")
        cls.rx_msg_size = int.from_bytes(cls.rx_message[3:4], byteorder="big")
        
        print(f"Message Header: ID=0x{cls.rx_msg_id:02X}, SEQ={cls.rx_msg_sq}, SIZE={cls.rx_msg_size}")

    @classmethod
    def get_message_name(cls, msg_id):
        """Get human-readable name for message ID"""
        names = {
            MSG_ID_SAT_HEARTBEAT: "SAT_HEARTBEAT",
            MSG_ID_SAT_TM_NOMINAL: "SAT_TM_NOMINAL",
            MSG_ID_SAT_TM_HAL: "SAT_TM_HAL",
            MSG_ID_SAT_TM_STORAGE: "SAT_TM_STORAGE",
        }
        return names.get(msg_id, f"UNKNOWN (0x{msg_id:02X})")


# Backward compatibility - maintain RECEIVE class name if needed
class RECEIVE(TelemetryUnpacker):
    """Alias for backward compatibility"""
    pass