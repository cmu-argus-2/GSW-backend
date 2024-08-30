from lib.radio_utils import *

class GS:
    radiohead = initialize_radio()
    rx_msg_id = 0x00

    @classmethod 
    def receive(self):
        # Receive message from radiohead
        rx_message = self.radiohead.receive_message()
        
        # Unpack message 
        if rx_message is not None:
            self.rx_msg_id = unpack_message(rx_message)
            return True
        else:
            return False
    
    @classmethod 
    def transmit(self):
        # Transmit message through radiohead
        # TODO - Add class for message ID definitions 
        tx_header = [0x08, 0x00, 0x01, 0x04]
        tx_payload = [0x01, 0x01, 0x00, 0x01]

        tx_message = bytes(tx_header + tx_payload)

        # header_from and header_to set to 255
        self.radiohead.send_message(tx_message, 255, 1)


        

