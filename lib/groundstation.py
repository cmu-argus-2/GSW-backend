import datetime
import time
from collections import deque

import RPi.GPIO as GPIO

import lib.config as config

from lib.radio_utils import initialize_radio

from lib.config import AUTH_KEY
from lib.auth.command_auth import compute_mac, get_next_nonce

from lib.command_interface.command_interface import CommandInterfaceGateway
from lib.database.database_backend import GSGateway   # this is comming in to replace the old database imports

from lib.telemetry.splat.splat.telemetry_codec import Ack, pack, unpack, Report, Variable, Command, Fragment
from lib.telemetry.splat.splat.telemetry_helper import format_bytes

from lib.telemetry.transaction_middleware import TransactionMiddleware


class GS:
    # Radio abstraction for GS
    radiohead = initialize_radio()
    
    # init the database gateway
    gs_database = GSGateway()
    
    # init the command interface gateway
    command_interface_gateway = CommandInterfaceGateway()
    command_interface_gateway.serve_in_thread()
    
    # init the middle man responsible for handling the transaction related commands
    transaction_middleware = TransactionMiddleware()
    

    # Initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)  # RX control pin
    GPIO.setup(23, GPIO.OUT)  # TX control pin

    rx_ctrl = 22  # GPIO pin number for rx_ctrl
    tx_ctrl = 23  # GPIO pin number for tx_ctrl

    # Ensure pins are off initially
    GPIO.output(rx_ctrl, GPIO.LOW)
    GPIO.output(tx_ctrl, GPIO.LOW)

    @classmethod
    def set_rx_mode(self):
        """
        set radiohead lib to rx mode
        """
        self.radiohead.radio.set_mode_rx()
        self.radiohead.receive_success = False
    
    @classmethod
    def check_tx_cmd_available(self):
        """
        check if there is a command to be transmitted
        """
        
        if self.command_interface_gateway.commands_available() == 0:
            # no commands available
            return False
        return True
    
    @classmethod
    def check_rx_packet_available(self):
        """
        Use the radiohead lib to check if a new packet is available
        """
        
        if self.radiohead.receive_success == False:
            # no new packets
            return False
        
        return True

    @classmethod
    def get_rx_packet(self):
        """
        Use the radiohead lib to get the latest packet
        """
        
        if self.radiohead.receive_success == False:
            # no new packets
            print("Expected new packet, but not available")
            return None
        
        rx_obj = self.radiohead.last_payload
        
        self.radiohead.receive_success = False  # reset for next packet
        
        return rx_obj
    
    @classmethod
    def process_rx_packet(self, msg_rx):
        """
        Will process the latest received packet
        
        msg_rx is self.radiohead.last_payload 

        decode it and add it to the database
        """
        
        data_bytes = msg_rx.message
        sat_id = data_bytes[0]
        
        print(f"Processing packet from SAT ID {sat_id} with RSSI {msg_rx.rssi}")
        print(f"Raw message bytes: {format_bytes(msg_rx.message)}")

        data_bytes = data_bytes[1:]  # remove sat_id from the data bytes

        message_object = unpack(data_bytes)

        if message_object is None:
            print(f"\033[31m[COMMS ERROR] Failed to unpack message from SAT ID {sat_id}\033[0m")
            return
        
        print(f"Decoded message object: {message_object}")
        
        if type(message_object) == Report:
            print(f"\033[32mReceived report: {message_object.name} from SAT ID {sat_id}\033[0m")
            self.gs_database.add_report(message_object, sat_id)
        if type(message_object) == Command:
            print(f"\033[32mReceived command: {message_object.name} from SAT ID {sat_id}\033[0m")
            self.gs_database.add_command(message_object, sat_id)
            
            # if command is related to transaction 
            # [check] - dont love doing it here, should think of a better arch
            if message_object.name == "INIT_TRANS":
                self.transaction_middleware.process_init_trans(message_object)
        if type(message_object) == Fragment:
            self.transaction_middleware.process_fragment(message_object)
        if type(message_object) == Variable:
            print(f"\033[32mReceived variable: {message_object.name} from SAT ID {sat_id}\033[0m")
            self.gs_database.add_variable(message_object, sat_id)
        if type(message_object) == Ack:
            print(f"\033[32mReceived Ack: {message_object} from SAT ID {sat_id}\033[0m\n")
            # should send this to the command interface

    @classmethod
    def transmit_message(self):
        """
        transmit the latest command in the command queue
        """

        GPIO.output(self.tx_ctrl, GPIO.HIGH)  # Turn TX on

        command = self.command_interface_gateway.pop_command()
        
        # check to see if command is CREATE_TRANS
        # [check] - dont love doing it here, should think of a better arch
        if command.name == "CREATE_TRANS":
            # if it is then we need to pass it to the transaction middleware to handle the transaction related commands
            self.transaction_middleware.process_create_trans(command)
        
        command_bytes = pack(command)
        
        nonce = get_next_nonce()
        mac = compute_mac(bytes.fromhex(AUTH_KEY), command_bytes, nonce)
        
        # add the header, nonce and mac
        header = bytes([69])  # header_from and header_to set to 255
        command_bytes = header + nonce + mac + command_bytes
        
        # header_from and header_to set to 255
        self.radiohead.send_message(command_bytes, 255, 1)

        print(f"Transmitted CMD. \033[34mRequesting {format_bytes(command_bytes)}\033[0m\n")
        GPIO.output(self.tx_ctrl, GPIO.LOW)  # Turn TX off