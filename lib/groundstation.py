import datetime

from lib.radio_utils import *
from lib.telemetry.unpacking import TelemetryUnpacker

class GS:
    radiohead = initialize_radio()
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0

    rx_message = []

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

    @classmethod 
    def receive(self):
        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()
        
        if rx_obj is not None:
            # Message from SAT
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
        tx_header = [0x08, 0x00, 0x01, 0x04]
        tx_payload = [self.rx_msg_id, 0x01, 0x00, 0x01]

        tx_message = bytes(tx_header + tx_payload)

        # header_from and header_to set to 255
        self.radiohead.send_message(tx_message, 255, 1)


        

