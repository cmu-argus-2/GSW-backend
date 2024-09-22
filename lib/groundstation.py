import datetime

from lib.radio_utils import *
from lib.telemetry.unpacking import TelemetryUnpacker

class GS:
    # Radio abstraction for GS
    radiohead = initialize_radio()

    # RX message parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    # RQ message parameters
    rq_msg_id = 0x01
    rq_msg_sq = 0

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

        if(self.rx_msg_id == 0x01):
            # Message is a heartbeat with TM frame, unpack
            TelemetryUnpacker.unpack_tm_frame(self.rx_message)
            self.rq_msg_id = 0x01
            self.rq_msg_sq = 0

        else:
            # Unknown message ID, RQ heartbeat as a default 
            self.rq_msg_id = 0x01
            self.rq_msg_sq = 0

    @classmethod 
    def receive(self):
        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()
        
        if rx_obj is not None:
            # Message from SAT
            print("Message received with RSSI:", rx_obj.rssi)

            self.rx_message = rx_obj.message
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
