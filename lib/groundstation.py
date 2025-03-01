import datetime
import time
import lib.config as config
from collections import deque

import RPi.GPIO as GPIO
from lib.database import db_services

from lib.radio_utils import initialize_radio
from lib.telemetry.unpacking import TelemetryUnpacker

class MSG_ID: 
    def __init__(self):
        self.ARGUS_1_ID = 0x01  # Argus spacecraft ID
        self.ARGUS_2_ID = 0x02  # Another Argus spacecraft ID
        self.GS_ID = 0x04  # Ground station ID

        # Satellite heartbeat and telemetry frames
        self.SAT_HEARTBEAT = 0x01
        self.SAT_TM_NOMINAL = 0x02
        self.SAT_TM_HAL = 0x03
        self.SAT_TM_STORAGE = 0x04
        self.SAT_TM_PAYLOAD = 0x05
        self.SAT_ACK = 0x0F 

        # File metadata and packet communication
        self.SAT_FILE_METADATA = 0x10
        self.SAT_FILE_PKT = 0x20

        # Ground station commands to satellite
        self.GS_CMD_FORCE_REBOOT = 0x40
        self.GS_CMD_SWITCH_TO_STATE = 0x41
        self.GS_CMD_UPLINK_TIME_REFERENCE = 0x42
        self.GS_CMD_UPLINK_ORBIT_REFERENCE = 0x43
        self.GS_CMD_TURN_OFF_PAYLOAD = 0x44
        self.GS_CMD_SCHEDULE_OD_EXPERIMENT = 0x45
        self.GS_CMD_DOWNLINK_ALL_FILES = 0x4D
        self.GS_CMD_REQUEST_TM_HEARTBEAT = 0x46
        self.GS_CMD_REQUEST_TM_HAL = 0x47
        self.GS_CMD_REQUEST_TM_STORAGE = 0x48
        self.GS_CMD_REQUEST_TM_PAYLOAD = 0x49
        self.GS_CMD_FILE_METADATA = 0x4A
        self.GS_CMD_FILE_PKT = 0x4B


class GPIOController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(22, GPIO.OUT)  # RX control pin
        GPIO.setup(23, GPIO.OUT)  # TX control pin
        self.rx_ctrl = 22
        self.tx_ctrl = 23
        GPIO.output(self.rx_ctrl, GPIO.LOW)  # RX off
        GPIO.output(self.tx_ctrl, GPIO.LOW)  # TX off

    def turn_rx_on(self):
        GPIO.output(self.rx_ctrl, GPIO.HIGH)  # RX on

    def turn_tx_on(self):
        GPIO.output(self.tx_ctrl, GPIO.HIGH)  # TX on

    def turn_rx_off(self):
        GPIO.output(self.rx_ctrl, GPIO.LOW)  # RX off

    def turn_tx_off(self):
        GPIO.output(self.tx_ctrl, GPIO.LOW)  # TX off


class RadioController:
    def __init__(self):
        self.radiohead = initialize_radio()

    def receive_message(self):
        return self.radiohead.receive_message()

    def send_message(self, message, src, dest):
        self.radiohead.send_message(message, src, dest)


class GS_COMMS_STATE:
    RECEIVE_PKT = 0x00
    TRANSMIT_CMD = 0x01
    UNPACK_AND_WRITE = 0x02
    READ_AND_PACK = 0x03
    ERROR_HANDLER = 0x04


class GSStateMachine:
    # default 
    def __init__(self):
        self.state = GS_COMMS_STATE.RECEIVE_PKT

    @classmethod
    def transition_state(self):
        if GS.state == GS_COMMS_STATE.RECEIVE_PKT:
            print ("1")
            # For file pkt transfer [toggle between receive and transmit]
            if GS.flag_rq_file:     
                print ("1.1")
                GS.state = GS_COMMS_STATE.TRANSMIT_CMD 
            elif GS.cmd_received: 
                print ("1.2")
                GS.state = GS_COMMS_STATE.UNPACK_AND_WRITE         
            else: 
                print ("1.3")
                GS.state = GS_COMMS_STATE.RECEIVE_PKT

        elif GS.state == GS_COMMS_STATE.UNPACK_AND_WRITE:
            print ("2")
            GS.state = GS_COMMS_STATE.READ_AND_PACK
        
        elif GS.state == GS_COMMS_STATE.READ_AND_PACK:
            print ("3")
            if GS.read_and_pack_success:
                print ("3.1")
                GS.state = GS_COMMS_STATE.TRANSMIT_CMD
            else: 
                print ("3.2")
                GS.state = GS_COMMS_STATE.ERROR_HANDLER #TODO: Logic 
        
        elif GS.state == GS_COMMS_STATE.TRANSMIT_CMD:
            print ("4")
            GS.state = GS_COMMS_STATE.RECEIVE_PKT
        else:
            print ("5")
            GS.state = GS_COMMS_STATE.RECEIVE_PKT


class DB_MOCK:
    if config.MODE == "DB":
        pass
    elif config.MODE == "DBG":
        pass


class GS:
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
    state = GS_COMMS_STATE.RECEIVE_PKT

    # Source header parameters
    rx_src_id = 0x00
    rx_dst_id = 0x00

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

    # state transitions
    read_and_pack_success = False
    cmd_received = False


    @classmethod
    def receive_pkt(self):
        print("# ----------------------------------- #")
        print("          Receiving packet...          ")
        print("# ----------------------------------- #")
        
        # self.gpio_controller.turn_rx_on()
        GPIO.output(self.rx_ctrl, GPIO.HIGH)
        rx_obj = self.radiohead.receive_message()

        if rx_obj is not None: 
            self.rx_message = rx_obj.message
            print(f"Msg RSSI: {rx_obj.rssi} at {time.monotonic() - self.rx_time}")
            self.rx_time = time.monotonic()
            
            self.rx_msg_id, self.rx_msg_sq, self.rx_msg_size = Unpacking.unpack_message(self.rx_message)
            
            self.cmd_received = True # For state transition 
            # self.gpio_controller.turn_rx_off()
            GPIO.output(self.rx_ctrl, GPIO.LOW)
            GSStateMachine.transition_state()
            return True
        
        else:
            self.cmd_received = False
            print("**** Nothing Received. Stay in RX ****")
            print("\n")
            GSStateMachine.transition_state()
            return False
        

    @classmethod
    def unpack_and_write(self):
        print("# ----------------------------------- #")
        print("     Unpacking and writing data...     ")
        print("# ----------------------------------- #")

        # TODO: Integrate with @Alexis 
        # self.file_id, self.file_time, self.filesize, self.file_target_sq = new_unpacking_function(self.rx_message)
        # add_downlink_data(self.rx_msg_id, self.rx_message)

    @classmethod
    def read_and_pack(self):
        print("# ----------------------------------- #")
        print("     Reading and packing data...     ")
        print("# ----------------------------------- #")
        #TODO: Integrate filepkt code 

         # ----------------------- TO REMOVE AFTER NEW PACKING FUNCTION --------------- #
        if self.rq_cmd == MSG_ID.GS_CMD_FILE_METADATA:
            self.transmit_Metadata()

        elif self.rq_cmd == MSG_ID.GS_CMD_FILE_PKT:
            self.transmit_Filepkt()

        else:
            # Set RQ message parameters for HB request
            self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
            self.rq_sq = 0
            self.rq_len = 0
            self.payload = bytearray()
        # --------------------------------------------------------------------------- #

        if self.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
            print("read_and_pack: SAT_FILE_METADATA")
            if ( self.file_id == 0x00
                or self.file_size == 0
                or self.file_target_sq == 0):

                # No file on satellite
                self.flag_rq_file = False

                if (db_services.commands_available() == None): # if db is empty 
                    self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    self.read_and_pack_success = False
                else:
                    self.rq_cmd = db_services.get_latest_command()
                    self.read_and_pack_success = True

            
            else:
                # Valid file on satellite
                self.flag_rq_file = True
                self.rq_cmd = MSG_ID.GS_CMD_FILE_PKT
                self.read_and_pack_success = True

        else:
            if (db_services.commands_available() == None): # if db is empty 
                    self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    self.read_and_pack_success = False
            else:
                self.rq_cmd = db_services.get_latest_command()
                self.read_and_pack_success = True

        

    @classmethod
    def transmit_cmd(self):
        print("# ----------------------------------- #")
        print("       Transmitting command...         ")
        print("# ----------------------------------- #")
        # self.gpio_controller.turn_tx_on()
        GPIO.output(self.tx_ctrl, GPIO.HIGH)

        # TODO: Integrate with @Alexis
        # self.rq_cmd, self.rq_sq, self.rq_len, self.payload = new_packing_function(self.rq_cmd)


        tx_header = (
            self.rq_cmd.to_bytes(1, "big")
            + self.rq_sq.to_bytes(2, "big")
            + self.rq_len.to_bytes(1, "big")
        )

        tx_message = bytes([MSG_ID.GS_ID, MSG_ID.ARGUS_1_ID]) + tx_header + self.payload

        # header_from and header_to set to 255
        self.radiohead.send_message(tx_message, 255, 1)
        # self.gpio_controller.turn_tx_off()
        GPIO.output(self.rx_ctrl, GPIO.LOW)


    @staticmethod
    def error_handler():
        # Error handling logic
        print("Handling error...")


    # ----------------------- TO REMOVE AFTER NEW (UN)PACKING FUNCTION --------------- #
    
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

    @classmethod
    def received_Heartbeat(self):
        # Message is a heartbeat with TM frame, unpack
        tm_data = TelemetryUnpacker.unpack_tm_frame_nominal(self.rx_message)
        print("**** Received HB ****")

        if (config.MODE == "DB"):
            db_services.add_Telemetry(MSG_ID.SAT_TM_NOMINAL, tm_data)
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"TEL:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()


    @classmethod
    def received_Metadata(self):
        # Message is file metadata
        print("**** Received file metadata ****")
        print(f"META:[{self.file_id}, {self.file_time}, {self.file_size}, {self.file_target_sq}]")

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
        print(f"File data {self.rx_message}")
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
            print("**** Received PKT ****")
        else:
            print("**** Received all packets. RX --> DB_RW ****")
            if (config.MODE == "DB"):
                 db_services.add_File_Packet(self.file_array, self.file_id, self.filename)
            elif (config.MODE == "DBG"):
                db_queue.enqueue(f"PKT:{self.file_array},{self.file_id}, {self.filename}")



    # Other methods (received_* and transmit_* methods) will use the DB service and GPIO/Radio abstractions


class Unpacking: 
    @classmethod
    def unpack_message(self, rx_message):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode("utf-8")
        
        # Unpack message header
        rx_msg_id = int.from_bytes((rx_message[0:1]), byteorder="big")
        rx_msg_sq = int.from_bytes(rx_message[1:3], byteorder="big")
        rx_msg_size = int.from_bytes(rx_message[3:4], byteorder="big")

        return rx_msg_id, rx_msg_sq, rx_msg_size





# -------------------- TODO: replace with Database functions ---------------- #
MSG_ID = MSG_ID()
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
queue.enqueue(MSG_ID.GS_CMD_FILE_METADATA)
queue.enqueue(MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT)
# queue.enqueue(0x4B)

# Database Queue Instantiation
db_queue = fifoQ()

# --------------------------------------------------------------------------- #