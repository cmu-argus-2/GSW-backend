# import datetime
import time

import RPi.GPIO as GPIO

from lib.radio_utils import *
from lib.telemetry.unpacking import TelemetryUnpacker


# Ground station state
class GS_COMMS_STATE:
    RQ_HEARTBEAT = 0x00
    RX = 0x01
    RQ_METADATA = 0x02
    RQ_FILE_PKT = 0x03


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


class GS:
    #     # Radio abstraction for GS
    #     radiohead = initialize_radio()

    #     # Initialize GPIO
    #     GPIO.setmode(GPIO.BCM)
    #     GPIO.setup(22, GPIO.OUT)  # RX control pin
    #     GPIO.setup(23, GPIO.OUT)  # TX control pin

    #     rx_ctrl = 22  # GPIO pin number for rx_ctrl
    #     tx_ctrl = 23  # GPIO pin number for tx_ctrl

    #     # Ensure pins are off initially
    #     GPIO.output(rx_ctrl, GPIO.LOW)
    #     GPIO.output(tx_ctrl, GPIO.LOW)

    #     #State ground station
    #     state = GS_COMMS_STATE.RX

    #     # RX message parameters
    #     rx_msg_id = 0x00
    #     rx_msg_sq = 0
    #     rx_msg_size = 0
    #     rx_message = []

    #     # RQ message parameters for commanding SC
    #     rq_cmd = 0x01
    #     rq_sq = 0
    #     rq_len = 0
    #     payload = []

    #     # File metadata parameters
    #     file_id = 0x00
    #     file_size = 0x00
    #     file_target_sq = 0x00
    #     flag_rq_file = True

    #     # File TX parameters
    #     gs_msg_sq = 0
    #     file_array = []

    #     # For packet timing tests
    #     rx_time = time.monotonic()

    def __init__(self):
        # Initialize radio
        self.radiohead = initialize_radio()

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        self.rx_ctrl = 22
        self.tx_ctrl = 23
        GPIO.setup(self.rx_ctrl, GPIO.OUT)
        GPIO.setup(self.tx_ctrl, GPIO.OUT)
        GPIO.output(self.rx_ctrl, GPIO.LOW)
        GPIO.output(self.tx_ctrl, GPIO.LOW)

        # Ground station state
        self.state = GS_COMMS_STATE.RX

        # RX message parameters
        self.rx_msg_id = 0x00
        self.rx_msg_sq = 0
        self.rx_msg_size = 0
        self.rx_message = []

        # RQ message parameters
        self.rq_cmd = 0x01
        self.rq_sq = 0
        self.rq_len = 0
        self.payload = []

        # File metadata parameters
        self.file_id = 0x00
        self.file_size = 0x00
        self.file_target_sq = 0x00
        self.flag_rq_file = True

        # File TX parameters
        self.gs_msg_sq = 0
        self.file_array = []

        # For packet timing tests
        self.rx_time = time.monotonic()

        # State transition map
        self.state_handlers = {
            GS_COMMS_STATE.RQ_HEARTBEAT: self.handle_rq_heartbeat,
            GS_COMMS_STATE.RX: self.handle_rx,
            GS_COMMS_STATE.RQ_METADATA: self.handle_rq_metadata,
            GS_COMMS_STATE.RQ_FILE_PKT: self.handle_rq_file_pkt,
        }

    @classmethod
    def unpack_header(self):
        self.rx_msg_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_msg_sq = int.from_bytes(self.rx_message[1:3], byteorder="big")
        self.rx_msg_size = int.from_bytes(self.rx_message[3:4], byteorder="big")

    def state_transition(self):
        """Determine the next state based on received message"""
        if self.rx_msg_id == MSG_ID.SAT_HEARTBEAT:
            self.state = GS_COMMS_STATE.RQ_HEARTBEAT
        elif self.rx_msg_id == MSG_ID.SAT_ACK:
            self.state = GS_COMMS_STATE.RX
        elif self.rx_msg_id == MSG_ID.SAT_FILE_METADATA:
            self.state = GS_COMMS_STATE.RQ_METADATA
        elif self.rx_msg_id == MSG_ID.SAT_FILE_PKT:
            self.state = GS_COMMS_STATE.RQ_FILE_PKT
        else:
            self.state = GS_COMMS_STATE.RX  # Default to RX

    def handle_rq_heartbeat(self):
        """Process heartbeat request"""
        print("Processing SAT_HEARTBEAT message")
        TelemetryUnpacker.unpack_tm_frame(self.rx_message)

        # Set RQ message parameters
        self.rq_cmd = MSG_ID.GS_CMD_SWITCH_TO_STATE
        self.rq_sq = 0
        self.rq_len = 5
        self.payload = (0x01).to_bytes(1, "big") + (20).to_bytes(4, "big")

    def handle_rx(self):
        """Process ACK message"""
        print("Processing SAT_ACK message:", self.rx_message)

        # Set RQ message parameters
        self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
        self.rq_sq = 0
        self.rq_len = 0
        self.payload = bytearray()

    def handle_rq_metadata(self):
        """Process file metadata request"""
        print("Processing SAT_FILE_METADATA message:", self.rx_message)
        self.file_id = int.from_bytes(self.rx_message[4:5], byteorder="big")
        self.file_size = int.from_bytes(self.rx_message[5:9], byteorder="big")

    def handle_rq_file_pkt(self):
        """Process file packet request"""
        print("Processing SAT_FILE_PKT message:", self.rx_message)
        self.file_array.append(self.rx_message[4:])  # Store received file chunk

    def unpack_message(self, rx_message):
        """Main function to process incoming messages"""
        self.rx_message = rx_message
        self.unpack_header()
        self.state_transition()

        # Call the appropriate handler based on the current state
        handler = self.state_handlers.get(self.state, self.handle_rx)
        handler()

    # @classmethod
    # def unpack_message(self):
    #     # Get the current time
    #     current_time = datetime.datetime.now()
    #     # Format the current time
    #     formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
    #     formatted_time = formatted_time.encode('utf-8')

    #     # Unpack RX message header
    #     self.unpack_header()

    #     # TODO: Command queue
    #     # Get most recent command from queue and execute
    #     if(self.rx_msg_id == MSG_ID.SAT_HEARTBEAT):
    #         TelemetryUnpacker.unpack_tm_frame(self.rx_message)

    #         # Set RQ message parameters
    #         self.rq_cmd = MSG_ID.GS_CMD_SWITCH_TO_STATE
    #         self.rq_sq = 0
    #         self.rq_len = 5

    #         # Temporary hardcoding for GS_CMD_SWITCH_TO_STATE
    #         self.payload = ((0x01).to_bytes(1, 'big') + (20).to_bytes(4, 'big'))

    #     elif (self.rx_msg_id == MSG_ID.SAT_ACK):
    #         print(self.rx_message)

    #         # Set RQ message parameters
    #         self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
    #         self.rq_sq = 0
    #         self.rq_len = 0

    #         # No payload for this command
    #         self.payload = bytearray()

    #     else:
    #         # Unknown message ID, RQ heartbeat as a default
    #         print(self.rx_message)

    #         # Set RQ message parameters
    #         self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
    #         self.rq_sq = 0
    #         self.rq_len = 0

    @classmethod
    def receive(self):
        GPIO.output(self.rx_ctrl, GPIO.HIGH)  # Turn RX on

        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()

        GPIO.output(self.rx_ctrl, GPIO.LOW)  # Turn RX off

        if rx_obj is not None:
            # Message from SAT
            self.rx_message = rx_obj.message
            print(
                f"Message received with RSSI: {rx_obj.rssi} at time {time.monotonic() - self.rx_time}"
            )
            self.rx_time = time.monotonic()

            self.unpack_message()

            return True

        else:
            # No message from SAT
            return False

    @classmethod
    def transmit(self):
        # Transmit message through radiohead
        GPIO.output(self.tx_ctrl, GPIO.HIGH)  # Turn TX on

        tx_header = (
            self.rq_cmd.to_bytes(1, "big")
            + self.rq_sq.to_bytes(2, "big")
            + self.rq_len.to_bytes(1, "big")
        )

        tx_message = tx_header + self.payload

        # header_from and header_to set to 255
        self.radiohead.send_message(tx_message, 255, 1)

        GPIO.output(self.tx_ctrl, GPIO.LOW)  # Turn TX off
