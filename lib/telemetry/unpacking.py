"""
GS Telemetry Unpacker
"""
import struct
import datetime
import time
import binascii

from lib.telemetry.constants import *
from lib.telemetry.helpers import *

# Const IDX numbers
CDH_NUM = 8
EPS_NUM = 43
ADCS_NUM = 31
GPS_NUM = 21
STORAGE_NUM = 19

# TM frame sizes as defined in message database
# TODO: TM HAL
# TODO: TM PAYLOAD
_TM_NOMINAL_SIZE    = 227
_TM_HAL_SIZE        = 46
_TM_STORAGE_SIZE    = 74
_TM_PAYLOAD_SIZE    = 0


class RECEIVE:
    _msg_id = 0
    _seq_cnt = 0
    _size = 0

    # Source header parameters
    rx_src_id = 0x00
    rx_dst_id = 0x00

    # RX message parameters
    # received msg parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    # File metadata parameters
    file_id = 0x0A  # IMG
    file_time = 1738351687
    file_size = 0x00
    file_target_sq = 0x00  # maximum sq count (240 bytes) --> error checking
    flag_rq_file = False  # testing in the lab - once the image is received
    filename = ""

    # File TX parameters
    gs_msg_sq = 0  # if file is multiple packets - number of packets received
    file_array = []

    @classmethod
    def unpack_frame(self, msg_id, msg):
        """
        Parses messages received from SC and dynamically unpacks it into a JSON format
        to store into database.

        Arguments:
            msg_id: the id of the message
            msg: the list of bits received

        Returns:
        Parsed data in the form of a dictionary (JSON)
        """


        # Get the format and data types for that message
        data_format = DATA_FORMATS[msg_id]

        # TODO: Header check for all incoming packets
        if msg_id == MSG_ID.SAT_HEARTBEAT or msg_id == MSG_ID.SAT_TM_NOMINAL:
            if self.rx_msg_size != _TM_NOMINAL_SIZE:
                print("\033[31m[COMMS ERROR] Message length incorrect\033[0m")
        
        elif msg_id == MSG_ID.SAT_TM_HAL:
            if self.rx_msg_size != _TM_HAL_SIZE:
                print("\033[31m[COMMS ERROR] Message length incorrect\033[0m")

        elif msg_id == MSG_ID.SAT_TM_STORAGE:
            if self.rx_msg_size != _TM_STORAGE_SIZE:
                print("\033[31m[COMMS ERROR] Message length incorrect\033[0m")
        
        else:
            pass

        msg = msg[4:]

        parsed_data = {}
        offset = 0  # This is where we start reading from the first byte
        for subsystem, fields in data_format.items():
            parsed_data[subsystem] = {}

            # Create struct format string dynamically by computing size and getting the format strings
            format_string = ">"+"".join([field[1] for field in fields])
            size = struct.calcsize(format_string)
            try: 
                unpacked_values = struct.unpack(format_string, msg[offset : offset + size])

                # Map unpacked values to field names for each subsystem
                for i, (field_name, _) in enumerate(fields):
                    parsed_data[subsystem][field_name] = unpacked_values[i]

                offset += size  # Move offset forward
            
            except struct.error: 
                # print(struct.error)
                print (f"\u001b[31m[COMMS ERROR] Unsuccessful unpacking - struct error. Msg size received: {self.rx_msg_size} \u001b[0m")


        print("Unpacking parsed data: ", parsed_data)
        return parsed_data


    @classmethod
    def unpack_message_header(self):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode("utf-8")

        # Unpack RX message header
        self.rx_src_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_dst_id = int.from_bytes((self.rx_message[1:2]), byteorder="big")
        self.rx_message = self.rx_message[2:]

        # TODO: Error checking based on source header
        print("Source Header:", self.rx_src_id, self.rx_dst_id)
        
        # Unpack message header
        self.rx_msg_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_msg_sq = int.from_bytes(self.rx_message[1:3], byteorder="big")
        self.rx_msg_size = int.from_bytes(self.rx_message[3:4], byteorder="big")
