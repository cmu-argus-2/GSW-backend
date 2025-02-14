import datetime
import time
import config
from collections import deque

import RPi.GPIO as GPIO
from lib.database import db_services

from lib.radio_utils import initialize_radio
from lib.telemetry.unpacking import TelemetryUnpacker

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


# Message ID database for communication protocol
class MSG_ID:
    """
    Comms message IDs that are downlinked during the mission
    """

    # SAT heartbeat, nominally downlinked in orbit
    SAT_HEARTBEAT = 0x01

    # SAT TM frames, requested by GS
    SAT_TM_HAL = 0x02
    SAT_TM_STORAGE = 0x03
    SAT_TM_PAYLOAD = 0x04

    # SAT ACK, in response to GS commands
    SAT_ACK = 0x0F

    # SAT file metadata and file content messages
    SAT_FILE_METADATA = 0x10
    SAT_FILE_PKT = 0x20

    """
    GS commands to be uplinked to Argus
    """

    # GS commands SC responds to with an ACK
    GS_CMD_FORCE_REBOOT = 0x40
    GS_CMD_SWITCH_TO_STATE = 0x41

    # GS commands SC responds to with a frame
    GS_CMD_REQUEST_TM_HEARTBEAT = 0x46

    # GS commands SC responds to with file MD or packets
    GS_CMD_FILE_METADATA = 0x4A
    GS_CMD_FILE_PKT = 0x4B


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

    # RX message parameters
    # received msg parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    # RQ message parameters for commanding SC
    # Request command
    rq_cmd = 0x01
    rq_sq = 0  # sequence command - matters for file
    rq_len = 0  # error checking
    payload = bytearray()

    # File metadata parameters
    file_id = 0x01
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

    @classmethod
    def unpack_header(self):
        self.rx_msg_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_msg_sq = int.from_bytes(self.rx_message[1:3], byteorder="big")
        self.rx_msg_size = int.from_bytes(self.rx_message[3:4], byteorder="big")

    @classmethod
    def unpack_message(self):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode("utf-8")

        # Unpack RX message header
        self.unpack_header()

    # -------------------------- SM functions ------------------------------- #
    @classmethod
    def database_readwrite(self):
        if self.state == GS_COMMS_STATE.DB_RW:
            print("////////////////////////")
            print("Currently in DB_RW state")
            print("///////////////////////")
            # TODO: Separate queue for RX and RQ

            # Check if we need to start file transfer sequence
            if self.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
                print("DB_RW: msg.id: SAT_FILE_METADATA")
                # Check if file metadata was valid
                # TODO: Better error checking
                if (
                    self.file_id == 0x00
                    or self.file_size == 0
                    or self.file_target_sq == 0
                ):
                    # No file on satellite
                    self.flag_rq_file = False


                    # TODO: Check if queue has a valid message ID
                    if (config.MODE == "DB"):
                        if (db_services.commands_available()): # if db is empty 
                            self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                        else:
                            self.rq_cmd = db_services.get_latest_command() # get top of the queue
                            print ("Latest Command2:", self.rq_cmd)
                            # db_services.remove_latest_command()


                    # TODO: Check if queue has a valid message ID
                    elif (config.MODE == "DBG"):
                        if queue.is_empty():
                            self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                        else:
                            self.rq_cmd = queue.dequeue()

                else:
                    # Valid file on satellite
                    self.flag_rq_file = True
                    self.rq_cmd = MSG_ID.GS_CMD_FILE_PKT

            else:
                # db_services.add_downlink_data(self.rx_msg_id, self.rx_message)
                if (config.MODE == "DB"):
                    # TODO: Check if queue has a valid message ID
                    # TODO: remove default - handled in CI
                    if (db_services.commands_available() == None): #if db is empty 
                        print("CI is empty")
                        self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    else:
                        self.rq_cmd = db_services.get_latest_command()
                        print ("Latest Command1:", self.rq_cmd)
                        db_services.remove_latest_command()


                elif (config.MODE == "DBG"):
                    if queue.is_empty():
                        self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    else:
                        self.rq_cmd = queue.dequeue()

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
            self.rx_message = rx_obj.message
            print(f"Msg RSSI: {rx_obj.rssi} at {time.monotonic() - self.rx_time}")
            self.rx_time = time.monotonic()

            self.unpack_message()

            if self.state == GS_COMMS_STATE.RX:
                print("////////////////////////")
                print("Currently in RX state")
                print("///////////////////////")

                if self.rx_msg_id == MSG_ID.SAT_HEARTBEAT:
                    self.received_Heartbeat()

                elif self.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
                    self.received_Metadata()

                elif self.rx_msg_id == MSG_ID.SAT_FILE_PKT:
                    self.received_Filepkt()

                elif self.rx_msg_id == MSG_ID.SAT_ACK:
                    self.received_Ack()
                else:
                    # Invalid RX message ID
                    print(f"**** Received invalid msgID {self.rx_msg_id} ****")
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

            if self.rq_cmd == MSG_ID.GS_CMD_SWITCH_TO_STATE:
                print ("hi")
                self.transmit_SwitchToState()

            elif self.rq_cmd == MSG_ID.GS_CMD_FORCE_REBOOT:
                self.transmit_ForceReboot()

            elif self.rq_cmd == MSG_ID.GS_CMD_FILE_METADATA:
                self.transmit_Metadata()

            elif self.rq_cmd == MSG_ID.GS_CMD_FILE_PKT:
                self.transmit_Filepkt()

            else:
                # Set RQ message parameters for HB request
                self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                self.rq_sq = 0
                self.rq_len = 0
                self.payload = bytearray()

            tx_header = (
                self.rq_cmd.to_bytes(1, "big")
                + self.rq_sq.to_bytes(2, "big")
                + self.rq_len.to_bytes(1, "big")
            )

            tx_message = tx_header + self.payload

            # header_from and header_to set to 255
            self.radiohead.send_message(tx_message, 255, 1)

            print("Transmitted CMD. TX --> RX")
            self.state = GS_COMMS_STATE.RX
            GPIO.output(self.tx_ctrl, GPIO.LOW)  # Turn TX off

        else:
            self.state = GS_COMMS_STATE.RX
            raise Exception(f"[COMMS ERROR] Not in TX state. In {self.state}")

    # ------------------------ Received Information ------------------------- #
    @classmethod
    def received_Heartbeat(self):
        # Message is a heartbeat with TM frame, unpack
        TelemetryUnpacker.unpack_tm_frame_nominal(self.rx_message)
        print("**** Received HB ****")

        if (config.MODE == "DB"):
                db_services.add_Telemetry()
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"TEL:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()


    @classmethod
    def received_Metadata(self):
        # Message is file metadata
        print("**** Received file metadata ****")

        # Unpack file parameters
        self.file_id = int.from_bytes((self.rx_message[4:5]), byteorder="big")
        self.file_time = int.from_bytes((self.rx_message[5:9]), byteorder="big")
        self.file_size = int.from_bytes((self.rx_message[9:13]), byteorder="big")
        self.file_target_sq = int.from_bytes((self.rx_message[13:15]), byteorder="big")

        if (config.MODE == "DB"):
                db_services.add_File_Meta_Data([self.file_id, self.file_time,self.file_size, self.file_target_sq])
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"META:[{self.file_id}, {self.file_time}, {self.file_size}, {self.file_target_sq}]")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()

    @classmethod
    def received_Filepkt(self):
        # TODO: Check for file ID and file time
        # Message is file packet
        print(f"Received PKT {self.rx_msg_sq} out of {self.file_target_sq}")
        # print(self.rx_message[9:self.rx_msg_size + 9])

        # Check internal gs_msg_sq against rx_msg_sq
        if self.gs_msg_sq != self.rx_msg_sq:
            # Sequence count mismatch
            print("ERROR: Sequence count mismatch")

        else:
            # Append packet to file_array
            self.file_array.append(self.rx_message[9 : self.rx_msg_size + 9])
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

            if (config.MODE == "DB"):
                 db_services.add_File_Packet(self.file_array, self.file_id, self.filename)
            elif (config.MODE == "DBG"):
                db_queue.enqueue(f"PKT:{self.file_array},{self.file_id}, {self.filename}")
        
 
            self.state = GS_COMMS_STATE.DB_RW
            self.database_readwrite()

    @classmethod
    def received_Ack(self):
        print(f"**** Received an ACK {self.rx_message} ****")

        if (config.MODE == "DB"):
            db_services.add_Ack()
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"ACK:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()

    # ----------------------- Transmitted Information ----------------------- #
    @classmethod
    def transmit_SwitchToState(self):
        # Set RQ message parameters to force a state change on SC
        self.rq_cmd = MSG_ID.GS_CMD_SWITCH_TO_STATE
        self.rq_sq = 0
        self.rq_len = 5

        # Temporary hardcoding for GS_CMD_SWITCH_TO_STATE
        self.payload = (0x01).to_bytes(1, "big") + (20).to_bytes(4, "big")
        print("Transmitting CMD: GS_CMD_SWITCH_TO_STATE")

    @classmethod
    def transmit_ForceReboot(self):
        # Set RQ message parameters
        self.rq_cmd = MSG_ID.GS_CMD_FORCE_REBOOT
        self.rq_sq = 0
        self.rq_len = 0

        # No payload for this command
        self.payload = bytearray()
        print("Transmitting CMD: GS_CMD_FORCE_REBOOT")

    @classmethod
    def transmit_Metadata(self):
        # Set RQ message parameters for MD request
        self.rq_sq = 0
        self.rq_len = 5

        # Request specific file ID and time of creation
        self.payload = self.file_id.to_bytes(1, "big") + self.file_time.to_bytes(
            4, "big"
        )
        print("Transmitting CMD: GS_CMD_FILE_METADATA")

    @classmethod
    def transmit_Filepkt(self):
        # Set RQ message parameters for PKT
        self.rq_sq = self.gs_msg_sq
        self.rq_len = 7

        # Request specific file ID and time of creation
        self.payload = (
            self.file_id.to_bytes(1, "big")
            + self.file_time.to_bytes(4, "big")
            + self.rq_sq.to_bytes(2, "big")
        )
        print("Transmitting CMD: GS_CMD_FILE_PKT")



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
queue.enqueue(MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT)
queue.enqueue(MSG_ID.GS_CMD_FORCE_REBOOT)
queue.enqueue(MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT)
# queue.enqueue(0x4B)

# Database Queue Instantiation
db_queue = fifoQ()

# --------------------------------------------------------------------------- #
