import datetime
import time

import RPi.GPIO as GPIO

from collections import deque 
from lib.radio_utils import *
from lib.telemetry.unpacking import TelemetryUnpacker

''' 
TODOs: 
- Needs thorough testing (has many bugs!!)
- Read database and write database function - Error in TX-->DB_RW transition
- Check state transitions 
'''


# Ground station state
class GS_COMMS_STATE:
    RX = 0x00
    TX = 0X01
    DB_RW = 0X02
    # RQ_HEARTBEAT = 0X00
    # RX = 0X01
    # RQ_METADATA = 0X02
    # RQ_FILE_PKT = 0X03

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


# MockUp of Database 
class FIFOQueue:
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

queue = FIFOQueue()
#TODO: Fill in with actual commands 
queue.enqueue(0x46)
# queue.enqueue(0x4A) #no ft
queue.enqueue(0x46)
queue.enqueue(0x4B)



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
    
    #State ground station
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
    rq_sq = 0 #sequence command - matters for file 
    rq_len = 0 #error checking - still store errored message in database 
    payload = bytearray()

    # File metadata parameters
    file_id = 0x01
    file_time = 1738351687
    file_size = 0x00
    file_target_sq = 0x00 #maximum sq count (240 bytes) --> error checking 
    flag_rq_file = True #testing in the lab - once the image is received 

    # File TX parameters
    gs_msg_sq = 0 #if file is multiple packets - number of packets received 
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

    #TODO: Command queue
    #TODO: Replace with actual database 
    @classmethod 
    def database_readwrite(self, gls): 
        if gls.state == GS_COMMS_STATE.DB_RW: 
            queue.enqueue(self.rx_msg_id)
            print ("Enq:", self.rx_msg_id)

            if queue.is_empty(): 
                self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
            else: 
                self.rq_cmd = queue.dequeue()
            print ("Deq:", self.rq_cmd)
            gls.state = GS_COMMS_STATE.TX
        else: 
            gls.state = GS_COMMS_STATE.RX


    # all unique message ids --> one function --> actual unpacking with 
    # telemetryUnpacker 


    @classmethod 
    def receive(self, gls):
        GPIO.output(self.rx_ctrl, GPIO.HIGH)  # Turn RX on

        # Receive message from radiohead
        rx_obj = self.radiohead.receive_message()

        if rx_obj is not None:
            # Message from SAT
            self.rx_message = rx_obj.message
            print(f"Message received with RSSI: {rx_obj.rssi} at time {time.monotonic() - self.rx_time}")
            self.rx_time = time.monotonic()

            self.unpack_message()


            if gls.state == GS_COMMS_STATE.RX: 
                print ("RX state")
                #If Heartbeat
                if(self.rx_msg_id == MSG_ID.SAT_HEARTBEAT):
                    # Message is a heartbeat with TM frame, unpack
                    TelemetryUnpacker.unpack_tm_frame(self.rx_message)
                    gls.state = GS_COMMS_STATE.DB_RW
                
                elif(self.rx_msg_id == MSG_ID.SAT_FILE_METADATA):
                    # Message is file metadata
                    print("Received file metadata")

                    # Unpack file parameters
                    self.file_id = int.from_bytes((self.rx_message[4:5]), byteorder='big')
                    self.file_time = int.from_bytes((self.rx_message[5:9]), byteorder='big')
                    self.file_size = int.from_bytes((self.rx_message[9:13]), byteorder='big')
                    self.file_target_sq = int.from_bytes((self.rx_message[13:15]), byteorder='big')

                    print(f"File parameters: ID: {self.file_id}, Time: {self.file_time}, Size: {self.file_size}, Message Count: {self.file_target_sq}")
                    gls.state = GS_COMMS_STATE.DB_RW

                elif(self.rx_msg_id == MSG_ID.SAT_FILE_PKT):
                    # TODO: Check for file ID and file time
                    # Message is file packet
                    print(f"Received file packet {self.rx_msg_sq} out of {self.file_target_sq}")
                    print(self.rx_message[9:self.rx_msg_size + 9])

                    # Check internal gs_msg_sq against rx_msg_sq
                    if(self.gs_msg_sq != self.rx_msg_sq):
                        # Sequence count mismatch
                        print("ERROR: Sequence count mismatch")

                    gls.state = GS_COMMS_STATE.DB_RW
                
                elif (self.rx_msg_id == MSG_ID.SAT_ACK): 
                    print (f'Received an ACK')
                    gls.state = GS_COMMS_STATE.DB_RW

                    
                else: 
                    #self loop 
                    gls.state = GS_COMMS_STATE.RX 

            GPIO.output(self.rx_ctrl, GPIO.LOW)  # Turn RX off
            #TODO: Check logic 
            return True
        
        else: 
            # No message from SAT
            return False


    
    @classmethod 
    def transmit(self, gls):
        if gls.state == GS_COMMS_STATE.TX: 
            # Transmit message through radiohead
            GPIO.output(self.tx_ctrl, GPIO.HIGH)  # Turn TX on

            tx_header = (self.rq_cmd.to_bytes(1, 'big') +
                        self.rq_sq.to_bytes(2, 'big') +
                        self.rq_len.to_bytes(1, 'big'))


            if(self.rq_cmd == MSG_ID.GS_CMD_FILE_METADATA): #rq_cmd
                if(self.flag_rq_file == True):
                    # Set RQ message parameters for MD request
                    # self.rq_cmd = MSG_ID.GS_CMD_FILE_METADATA
                    self.rq_sq = 0
                    self.rq_len = 5
                    self.payload = (self.file_id.to_bytes(1, 'big') +
                                    self.file_time.to_bytes(4, 'big'))
                
                else:
                    # Set RQ message parameters for HB request
                    # self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    self.rq_sq = 0
                    self.rq_len = 0
                    self.payload = bytearray()

                
            elif (self.rq_cmd == MSG_ID.GS_CMD_FILE_PKT):
                # TODO: Better error checking
                if(self.file_id == 0x00 or self.file_size == 0 or self.file_target_sq == 0):
                    # No file on satellite
                    self.flag_rq_file = False

                    # Set RQ message parameters for HB request
                    self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    self.rq_sq = 0
                    self.rq_len = 0
                    self.payload = bytearray()

                else:
                    # Set RQ message parameters for PKT
                    self.rq_cmd = MSG_ID.GS_CMD_FILE_PKT
                    self.rq_sq = self.gs_msg_sq
                    self.rq_len = 7
                    self.payload = (self.file_id.to_bytes(1, 'big') +
                                    self.file_time.to_bytes(4, 'big') + 
                                    self.rq_sq.to_bytes(2, 'big'))

            elif(self.rq_cmd == MSG_ID.GS_CMD_FILE_PKT):
                # TODO: Check for file ID and file time
                # Set RQ message parameters for PKT
                self.rq_cmd = MSG_ID.GS_CMD_FILE_PKT
                self.rq_sq = self.gs_msg_sq
                self.rq_len = 7
                self.payload = (self.file_id.to_bytes(1, 'big') +
                                self.file_time.to_bytes(4, 'big') + 
                                self.rq_sq.to_bytes(2, 'big'))
                
                # Append packet to file_array
                self.file_array.append(self.rx_message[9:self.rx_msg_size + 9])

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

                    # Set RQ message parameters for HB request
                    self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                    self.rq_sq = 0
                    self.rq_len = 0
                    self.payload = bytearray()
                
                else:
                    # Set RQ message parameters for PKT
                    self.rq_cmd = MSG_ID.GS_CMD_FILE_PKT
                    self.rq_sq = self.gs_msg_sq
                    self.rq_len = 7
                    self.payload = (self.file_id.to_bytes(1, 'big') +
                                    self.file_time.to_bytes(4, 'big') + 
                                    self.rq_sq.to_bytes(2, 'big'))
            else:
                # Set RQ message parameters for HB request
                self.rq_cmd = MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT
                self.rq_sq = 0
                self.rq_len = 0
                self.payload = bytearray()

            
            tx_message = tx_header + self.payload

            # header_from and header_to set to 255
            self.radiohead.send_message(tx_message, 255, 1)
            # TODO: Check logic
            gls.state = GS_COMMS_STATE.RX
            GPIO.output(self.tx_ctrl, GPIO.LOW)  # Turn TX off
        else: 
            print ("GS not in TX state, : It is in", gls.state)
            gls.state = GS_COMMS_STATE.RX


        
