import datetime
import time
from collections import deque

import RPi.GPIO as GPIO

import lib.config as config

from lib.radio_utils import initialize_radio

from lib.config import AUTH_KEY, SC_CALLSIGN, GS_CALLSIGN
from lib.auth.command_auth import compute_mac, get_next_nonce

from lib.command_interface.command_interface import CommandInterfaceGateway
from lib.database.database_backend import GSGateway   # this is comming in to replace the old database imports

from lib.telemetry.splat.splat.telemetry_codec import Ack, pack, unpack, Report, Variable, Command, Fragment
from lib.telemetry.splat.splat.telemetry_helper import format_bytes

from lib.telemetry import transaction_middleware  # This is the class object that will deal with transactions
from lib.telemetry import transaction_middleware  # This is the class object that will deal with transactions


class GS:
    # Radio abstraction for GS
    radio = initialize_radio()
    
    # init the database gateway
    gs_database = GSGateway()
    
    # init the command interface gateway
    command_interface_gateway = CommandInterfaceGateway()
    command_interface_gateway.serve_in_thread()


    @classmethod
    def set_rx_mode(self):
        """
        set radio to rx mode
        """
        self.radio.set_mode_rx()
        self.radio.receive_success = False
    
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
        Use the radio to check if a new packet is available
        """
        
        if self.radio.receive_success == False:
            # no new packets
            return False
        
        return True

    @classmethod
    def get_rx_packet(self):
        """
        Use the radio to get the latest packet
        """
        
        if self.radio.receive_success == False:
            # no new packets
            print("Expected new packet, but not available")
            return None
        
        rx_obj = self.radio.last_payload
        
        self.radio.receive_success = False  # reset for next packet
        
        return rx_obj
    
    @classmethod
    def process_rx_packet(self, msg_rx):
        """
        Will process the latest received packet
        
        msg_rx is self.radio.last_payload 

        decode it and add it to the database
        """
        
        data_bytes = msg_rx.message
 
        try:
            callsign, message_object = unpack(data_bytes)
        except Exception as e:
            # print in red taht failed to decode and print the error
            print(f"\033[31m[COMMS ERROR] Failed to unpack message: {e}\033[0m")
            # print in red formated bytes
            print(f"\033[31mRaw message bytes: {format_bytes(msg_rx.message)}\033[0m")
            return

        print(f"\033[35mFrom SAT: {callsign}\033[0m")
        print(f"Raw message bytes: {format_bytes(msg_rx.message)}")
        print(f"Decoded message object: {message_object}")
        
        if type(message_object) == Report:
            print(f"\033[32mReport: {message_object.name}\033[0m")
            self.gs_database.add_report(message_object, callsign)
        if type(message_object) == Command:
            print(f"\033[32mCommand: {message_object.name}\033[0m")
            self.gs_database.add_command(message_object, callsign)
            
            # if command is related to transaction 
            # [check] - dont love doing it here, should think of a better arch
            if message_object.name == "INIT_TRANS":
                transaction_middleware.process_init_trans(message_object)
        if type(message_object) == Fragment:
            transaction_middleware.process_fragment(message_object)
        if type(message_object) == Variable:
            print(f"\033[32mVariable: {message_object.name}\033[0m")
            self.gs_database.add_variable(message_object, callsign)
        if type(message_object) == Ack:
            print(f"\033[32mAck: {message_object}\033[0m\n")
            # should send this to the command interface

    @classmethod
    def transmit_message(self):
        """
        transmit the latest command in the command queue
        """

        command = self.command_interface_gateway.pop_command()
        
        command_bytes = pack(command, GS_CALLSIGN)
        
        if AUTH_KEY is not None:
            # means that we want to encrypt the data
            nonce = get_next_nonce()
            mac = compute_mac(bytes.fromhex(AUTH_KEY), command_bytes, nonce)
            command_bytes = nonce + mac + command_bytes   # add teh encryption info to the command
        
        
        command_bytes = command_bytes
        
        # header_from and header_to set to 255
        # Using send() method directly (with_ack=True equivalent)
        self.radio.send(command_bytes, 255, 0, 0)

        print(f"Transmitted CMD. \033[34mRequesting {format_bytes(command_bytes)}\033[0m\n")