import datetime
import time
from collections import deque

import RPi.GPIO as GPIO

import lib.config as config
from lib.database import db_command_queue, db_rx_data
from lib.gs_constants import MSG_ID
from lib.radio_utils import initialize_radio

from lib.telemetry.packing import CommandPacker
# from lib.packing import TRANSMITTED
# from lib.unpacking import RECEIVED


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

    # For packet timing tests
    rx_time = time.monotonic()

    # -------------------------- SM functions ------------------------------- #
    @classmethod
    def database_readwrite(self):
        if self.state == GS_COMMS_STATE.DB_RW:
            print("////////////////////////")
            print("Currently in DB_RW state")
            print("///////////////////////")
            # TODO: Separate queue for RX and RQ

            # Check if we need to start file transfer sequence
            if RECEIVE.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
                print("DB_RW: msg.id: SAT_FILE_METADATA")
                # Check if file metadata was valid
                # TODO: Better error checking
                print(f"META2:[{self.file_id}, {self.file_time}, {self.file_size}, {self.file_target_sq}]")
                if (
                    self.file_id == 0x00
                    or self.file_size == 0
                    or self.file_target_sq == 0
                ):
                    # No file on satellite
                    self.flag_rq_file = False

                    # TODO: Check if queue has a valid message ID
                    if config.MODE == "DB":
                        if db_command_queue.commands_available():  # if db is empty
                            TRANSMIT.rq_cmd = {
                                "id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT,
                                "args": [],
                            }
                        else:
                            TRANSMIT.rq_cmd = (
                                db_command_queue.get_latest_command()
                            )  # get top of the queue
                            print("Latest Command2:", TRANSMIT.rq_cmd)
                            # db_command_queue.remove_latest_command()

                    # TODO: Check if queue has a valid message ID
                    elif config.MODE == "DBG":
                        if queue.is_empty():
                            TRANSMIT.rq_cmd = {
                                "id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT,
                                "args": [],
                            }
                        else:
                            TRANSMIT.rq_cmd = queue.dequeue()

                else:
                    # Valid file on satellite
                    self.flag_rq_file = True
                    TRANSMIT.rq_cmd = MSG_ID.GS_CMD_FILE_PKT
                    print ("found valid file")

            else:
                # db_rx_data.add_downlink_data(RECEIVE.rx_msg_id, RECEIVE.rx_message)
                if config.MODE == "DB":
                    # TODO: Check if queue has a valid message ID
                    # TODO: remove default - handled in CI
                    if db_command_queue.commands_available() == None:  # if db is empty
                        print("CQ is empty")
                        TRANSMIT.rq_cmd = {
                            "id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT,
                            "args": [],
                        }
                    else:
                        TRANSMIT.rq_cmd = db_command_queue.get_latest_command()
                        print("Latest Command1:", TRANSMIT.rq_cmd)
                        db_command_queue.remove_latest_command()

                elif config.MODE == "DBG":
                    if queue.is_empty():
                        print("Queue is empty, requesting heartbeats")
                        TRANSMIT.rq_cmd = {
                            "id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT,
                            "args": [],
                        }
                    else:
                        TRANSMIT.rq_cmd = queue.dequeue()

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

            # RECEIVE.rx_src_id, RECEIVE.rx_dst_id, RECEIVE.rx_msg_id, RECEIVE.rx_message, RECEIVE.rx_msg_sq, RECEIVE.rx_msg_size = UNPACKING.unpack_message()
            RECEIVE.unpack_message_header()

            if self.state == GS_COMMS_STATE.RX:
                print("////////////////////////")
                print("Currently in RX state")
                print("///////////////////////")
        
                if RECEIVE.rx_msg_id == MSG_ID.SAT_FILE_PKT:
                    self.received_Filepkt()
                elif RECEIVE.rx_msg_id in MSG_ID.VALID_RX_MSG_IDS:
                    db_rx_data.add_downlink_data(RECEIVE.rx_msg_id, RECEIVE.rx_message)
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

            if TRANSMIT.rq_cmd in MSG_ID.VALID_TX_MSG_IDS:
                TRANSMIT.pack()
            else:
                # Set RQ message parameters for HB request
                TRANSMIT.rq_cmd = {"id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT, "args": []}
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

    @classmethod
    def received_Filepkt(self):
        # TODO: Check for file ID and file time
        # Message is file packet
        print(f"Received PKT {RECEIVE.rx_msg_sq} out of {self.file_target_sq}")
        print(f"File data {RECEIVE.rx_message}")
        # print(RECEIVE.rx_message[9:RECEIVE.rx_msg_size + 9])

        # Check internal gs_msg_sq against rx_msg_sq
        if self.gs_msg_sq != RECEIVE.rx_msg_sq:
            # Sequence count mismatch
            print("ERROR: Sequence count mismatch")

        else:
            # Append packet to file_array
            self.file_array.append(RECEIVE.rx_message[9 : RECEIVE.rx_msg_size + 9])
            # Increment sequence counter
            self.gs_msg_sq += 1

        # Compare gs_msg_sq to file_target_sq
        if self.gs_msg_sq == self.file_target_sq:
            # Write file to memory
            self.filename = "test_image.jpg"
            write_bytes = open(self.filename, "wb")

            # Write all bytes to the file
            for i in range(self.file_target_sq):
                write_bytes.write(self.file_array[i])

            # Close file
            write_bytes.close()

            # Set flag
            self.flag_rq_file = False

        # Transition based on flag
        if self.flag_rq_file is True:
            print("**** Received PKT. RX --> TX ****")
            self.state = GS_COMMS_STATE.TX
        else:
            print("**** Received all packets. RX --> DB_RW ****")

            if config.MODE == "DB":
                db_rx_data.add_File_Packet(self.file_array, self.file_id, self.filename)
            elif config.MODE == "DBG":
                db_queue.enqueue(
                    f"PKT:{self.file_array},{self.file_id}, {self.filename}"
                )

            self.state = GS_COMMS_STATE.DB_RW
            self.database_readwrite()


# -------------------- TODO: replace with Database functions ---------------- #
# Mockup of Command Interface
class fifoQ:
    def __init__(self):
        self.queue = deque()

    def enqueue(self, item):
        self.queue.append(item)

    def dequeue(self):
        if self.is_empty():
            return "Queue is empty"
        return self.queue.popleft()

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)


# Command Interface Instantiation
queue = fifoQ()
queue.enqueue(MSG_ID.GS_CMD_SWITCH_TO_STATE)
queue.enqueue(MSG_ID.GS_CMD_FILE_METADATA)
queue.enqueue(MSG_ID.GS_CMD_FILE_METADATA)
queue.enqueue(MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE)
# queue.enqueue(0x4B)

# Database Queue Instantiation
db_queue = fifoQ()

# --------------------------------------------------------------------------- #
