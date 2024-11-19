import datetime
import time

from lib.radio_utils import *
from lib.telemetry.unpacking import TelemetryUnpacker

# Ground station state
class GS_COMMS_STATE:
    RQ_HEARTBEAT = 0X00
    RX = 0X01
    RQ_METADATA = 0X02
    RQ_FILE_PKT = 0X03

class MSG_ID:
    SAT_HEARTBEAT = 0x01
    GS_ACK = 0x08
    SAT_ACK = 0x09
    SAT_FILE_METADATA = 0x10
    SAT_FILE_PKT = 0x20


class GS:
    # Radio abstraction for GS
    radiohead = initialize_radio()
    
    #State ground station
    state = GS_COMMS_STATE.RX

    # RX message parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    # RQ message parameters
    rq_msg_id = 0x01
    rq_msg_sq = 0

    # File metadata parameters
    file_id = 0x00
    file_size = 0x00
    file_target_sq = 0x00
    flag_rq_file = True

    # File TX parameters
    gs_msg_sq = 0
    file_array = []

    # For packet timing tests
    rx_time = time.monotonic()

    @classmethod
    def unpack_header(self):
        self.rx_msg_id = int.from_bytes((self.rx_message[0:1]), byteorder='big')
        self.rx_msg_sq = int.from_bytes(self.rx_message[1:3], byteorder='big')
        self.rx_msg_size = int.from_bytes(self.rx_message[3:4], byteorder='big')

    @classmethod
    def unpack_message(self):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode('utf-8')

        # Unpack RX message header
        self.unpack_header()

        # TODO: GS state machine for downlinking a file
        if(self.rx_msg_id == MSG_ID.SAT_HEARTBEAT):
            # Message is a heartbeat with TM frame, unpack
            TelemetryUnpacker.unpack_tm_frame(self.rx_message)

            if(self.flag_rq_file == True):
                # Set RQ message parameters
                self.rq_msg_id = MSG_ID.SAT_FILE_METADATA
                self.rq_msg_sq = 0
            
            else:
                # Set RQ message parameters
                self.rq_msg_id = MSG_ID.SAT_HEARTBEAT
                self.rq_msg_sq = 0

        elif(self.rx_msg_id == MSG_ID.SAT_FILE_METADATA):
            # Message is file metadata
            print("Received file metadata")

            # Unpack file parameters
            self.file_id = int.from_bytes((self.rx_message[4:5]), byteorder='big')
            self.file_size = int.from_bytes((self.rx_message[5:9]), byteorder='big')
            self.file_target_sq = int.from_bytes((self.rx_message[9:11]), byteorder='big')

            print(f"File parameters: ID: {self.file_id}, Size: {self.file_size}, Message Count: {self.file_target_sq}")

            if(self.file_id == 0x00 or self.file_size == 0 or self.file_target_sq == 0):
                # No file on satellite
                self.flag_rq_file = False
                self.rq_msg_id = MSG_ID.SAT_HEARTBEAT
                self.rq_msg_sq = 0

            else:
                # Set RQ message parameters
                self.rq_msg_id = MSG_ID.SAT_FILE_PKT
                self.rq_msg_sq = 0

        elif(self.rx_msg_id == MSG_ID.SAT_FILE_PKT):
            # Message is file packet
            print(f"Received file packet {self.gs_msg_sq}")
            print(self.rx_message[4:self.rx_msg_size + 4])

            # Check internal gs_msg_sq against rx_msg_sq
            if(self.gs_msg_sq != self.rx_msg_sq):
                # Sequence count mismatch
                print("ERROR: Sequence count mismatch")

                # If rx_msg_sq > gs_msg_sq, missed packet
                self.rq_msg_id = MSG_ID.SAT_FILE_PKT
                self.rq_msg_sq = self.gs_msg_sq

                return

            # Append packet to file_array
            self.file_array.append(self.rx_message[4:self.rx_msg_size + 4])

            # Increment sequence counter
            self.gs_msg_sq += 1

            # Compare gs_msg_sq to file_target_sq
            if(self.gs_msg_sq == self.file_target_sq):
                # Write file to memory
                filename = 'test_image.jpg'
                write_bytes = open(filename, 'wb')

                for i in range(self.file_target_sq):
                    write_bytes.write(self.file_array[i])
                
                self.flag_rq_file = False
                write_bytes.close()

                # Set RQ message parameters
                self.rq_msg_id = MSG_ID.SAT_HEARTBEAT
                self.rq_msg_sq = 0
            
            else:
                # Set RQ message parameters
                self.rq_msg_id = MSG_ID.SAT_FILE_PKT
                self.rq_msg_sq = self.gs_msg_sq
            
        else:
            # Unknown message ID, RQ heartbeat as a default 
            self.rq_msg_id = MSG_ID.SAT_HEARTBEAT
            self.rq_msg_sq = 0


    @classmethod 
    def receive(self):
        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()

        if rx_obj is not None:
            # Message from SAT
            self.rx_message = rx_obj.message
            print(f"Message received with RSSI: {rx_obj.rssi} at time {time.monotonic() - self.rx_time}")
            self.rx_time = time.monotonic()

            self.unpack_message()

            return True

        else:
            # No message from SAT
            return False
    
    @classmethod 
    def transmit(self):
        # Transmit message through radiohead
        # TODO - Add class for message ID definitions 
        tx_header = bytes([0x08, 0x00, 0x00, 0x04])
        tx_payload = (self.rx_msg_id.to_bytes(1, 'big') +
                    self.rq_msg_id.to_bytes(1, 'big') +
                    self.rq_msg_sq.to_bytes(2, 'big'))

        tx_message = tx_header + tx_payload

        # header_from and header_to set to 255
        self.radiohead.send_message(tx_message, 255, 1)
