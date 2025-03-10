import datetime
import time
from collections import deque

import RPi.GPIO as GPIO

import lib.config as config

from lib.gs_constants import MSG_ID
from lib.radio_utils import initialize_radio

from lib.telemetry.packing import TRANSMIT
from lib.telemetry.unpacking import RECEIVE
from lib.telemetry.filetransfer import FILETRANSFER


if config.MODE == "DB":
    from lib.database.db_command_queue import get_latest_command, remove_latest_command, commands_available
    from lib.database.db_rx_data import add_downlink_data, add_File_Packet
elif config.MODE == "DBG":
    from lib.database.debug_queue import get_latest_command, remove_latest_command, commands_available


"""
GS state functions:
receive() [RX], transmit() [TX], database_readwrite() [DB_RW]
"""

if config.MODE == "DBG":
    print("Debug Mode: Executing debug-specific code")
elif config.MODE == "DB":
    print("Database Mode: Executing database-specific code")


# Ground station state
class GS_COMMS_STATE:
    RX = 0x00
    TX = 0x01
    DB_RW = 0x02


class GS:
    # Radio abstraction for GS
    radiohead = initialize_radio()

    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)  # RX control pin
    GPIO.setup(23, GPIO.OUT)  # TX control pin

    rx_ctrl = 22  # GPIO pin number for rx_ctrl
    tx_ctrl = 23  # GPIO pin number for tx_ctrl

    # Ensure pins are off initially
    GPIO.output(rx_ctrl, GPIO.LOW)
    GPIO.output(tx_ctrl, GPIO.LOW)

    # State ground station
    state = GS_COMMS_STATE.RX

    # For packet timing tests
    rx_time = time.monotonic()

    # -------------------------- SM functions ------------------------------- #
    @classmethod
    def database_readwrite(self):
        if self.state == GS_COMMS_STATE.DB_RW:
            print("////////////////////////")
            print("Currently in DB_RW state")
            print("///////////////////////")
            
            if RECEIVE.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
                TRANSMIT.rq_cmd = FILETRANSFER.initiate_file_transfer_sq()

            else:
                # TODO: Check if queue has a valid message ID
                if commands_available() == None: 
                    print("CQ is empty")
                    TRANSMIT.rq_cmd = {
                        "id": MSG_ID.GS_CMD_REQUEST_TM_NOMINAL,
                        "args": {},
                    }
                else:
                    TRANSMIT.rq_cmd = get_latest_command()
                    print("Latest Command:", TRANSMIT.rq_cmd)
                    remove_latest_command()


            self.state = GS_COMMS_STATE.TX

        else:

            self.state = GS_COMMS_STATE.RX

    @classmethod
    def receive(self):
        GPIO.output(self.rx_ctrl, GPIO.HIGH)  # Turn RX on
        print("\n")
        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()

        if rx_obj is not None:
            # Message from SAT
            RECEIVE.rx_message = rx_obj.message
            print(f"Msg RSSI: {rx_obj.rssi} at {time.monotonic() - self.rx_time}")
            self.rx_time = time.monotonic()

            RECEIVE.unpack_message_header()

            if self.state == GS_COMMS_STATE.RX:
                print("////////////////////////")
                print("Currently in RX state")
                print("///////////////////////")
        
                if RECEIVE.rx_msg_id in MSG_ID.VALID_RX_MSG_IDS:
                    add_downlink_data(RECEIVE.rx_msg_id, RECEIVE.rx_message)
                    self.state = GS_COMMS_STATE.DB_RW
                    self.database_readwrite()        
                
                elif RECEIVE.rx_msg_id == MSG_ID.SAT_FILE_PKT:
                    FILETRANSFER.receiving_multipkt()
                    
                    if FILETRANSFER.flag_rq_file is True:
                        print("**** Received PKT. RX --> TX ****")
                        self.state = GS_COMMS_STATE.TX
                    else:
                        print("**** Received all packets. RX --> DB_RW ****")

                        add_File_Packet(FILETRANSFER.file_array, FILETRANSFER.file_id, FILETRANSFER.filename)

                        self.state = GS_COMMS_STATE.DB_RW
                        self.database_readwrite()          
                
                else:
                    # Invalid RX message ID
                    print(f"**** Received invalid msgID {RECEIVE.rx_msg_id} ****")
                    self.state = GS_COMMS_STATE.RX

            print("\n")
            GPIO.output(self.rx_ctrl, GPIO.LOW)  # Turn RX off
            return True

        else:
            # No message from SAT
            print("**** Nothing Received. Stay in RX ****")
            print("\n")
            self.state = GS_COMMS_STATE.RX
            return False

    @classmethod
    def transmit(self):
        if self.state == GS_COMMS_STATE.TX:
            print("////////////////////////")
            print("Currently in TX state")
            print("///////////////////////")
            # Transmit message through radiohead
            GPIO.output(self.tx_ctrl, GPIO.HIGH)  # Turn TX on

            if TRANSMIT.rq_cmd["id"] in MSG_ID.VALID_TX_MSG_IDS:
                TRANSMIT.pack()
            else:
                # Set RQ message parameters for HB request
                TRANSMIT.rq_cmd = {"id": MSG_ID.GS_CMD_REQUEST_TM_NOMINAL, "args": {}}
                self.rq_sq = 0
                self.rq_len = 0
                self.payload = bytearray()

            # header_from and header_to set to 255
            self.radiohead.send_message(TRANSMIT.tx_message, 255, 1)

            print("Transmitted CMD. TX --> RX")
            self.state = GS_COMMS_STATE.RX
            GPIO.output(self.tx_ctrl, GPIO.LOW)  # Turn TX off

        else:
            self.state = GS_COMMS_STATE.RX
            raise Exception(f"[COMMS ERROR] Not in TX state. In {self.state}")

        print("Requesting ID:", TRANSMIT.rq_cmd, "SQ:", TRANSMIT.rq_sq)



