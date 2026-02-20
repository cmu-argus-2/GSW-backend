"""
Not sure if this is the best name for this file

the goal is to implement a class that will deal with the data
receive telemetry data and add it to the database
receive file packets and build the files out of them
receive the commands from a socket, add to the command queue and eventually add them to the database as well

but for now we will only send the telemetry data to the database and nothing else
"""


import os
import csv
import time
import json
import socket
import logging
import threading
from collections import deque
from lib.config import INGEST_GATEWAY_IP, INGEST_GATEWAY_PORT

from lib.database.ingest_gateway import Ingest

from lib.telemetry.splat.splat.telemetry_codec import Report, Variable, Command

from lib.telemetry.splat.splat.transport_layer import Transaction, transaction_manager


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("GS_GATEWAY")


# -----------------------------------------------------------------------------
# GS Gateway
# -----------------------------------------------------------------------------
class GSGateway:
    def __init__(self, ingest_host=INGEST_GATEWAY_IP, ingest_port=INGEST_GATEWAY_PORT):
        self.command_queue = deque()
        self.current_file_metadata = {}

        self.ingest = Ingest(
            host=ingest_host,
            port=ingest_port,
            timeout=5.0,
            retries=3,
        )

        # Socket server control
        self.running = False
        self.socket_thread = None

        print("GS Gateway initialized")



    # -------------------------------------------------------------------------
    # Entry point for satellite packets
    # -------------------------------------------------------------------------
    
    def add_report(self, report, sat_id):
        """
        Will add a report to the database
        this report is the object defined in telemetry codec

        [check] - should add here the sat_id somehow
        """
        
        # check the type
        if report.__class__.__name__ != 'Report':
            print(f"Invalid report type: {type(report)}")
            return
        
        # # pretty print the report.variables
        # for ss_name, vars in report.variables.items():
        #     for var_name, value in vars.items():
        #         print(f"  {ss_name}-{var_name}: {value}")
        
        print(report.variables)
        
        self._send_tm_to_database(report.variables)
        
    def add_variable(self, variable, sat_id):
        """
        Will add variable to the database
        want to build a dict that has
        {ss_name: {var_name: value}}
        """
        
        # check the type
        if variable.__class__.__name__ != 'Variable':
            print(f"Invalid variable type: {type(variable)}")
            return
        
        variable_dict = {
            variable.subsystem: {
                variable.name: variable.value
            }
        }
        
        self._send_tm_to_database(variable_dict)
  
        
    def add_command(self, command, sat_id):
        """
        Right now this function will be made to deal with the transport layer 
        it will process the commands related to the transport layers and once we have the complete file
        it will put the file on a folder

        [check] - maybe should add the command to the database, but will figure that out later
        
        """
        
        # check the type
        if command.__class__.__name__ != 'Command':
            print(f"Invalid command type: {type(command)}")
            return
        
        if command.name == "INIT_TRANS":
            # received a command to init the transaction, need to create the transaction
            self.init_transaction(command)
        if command.name == "TRANS_PAYLOAD":
            # received a command with fragments, lets add the data
            self.add_fragment_to_transaction(command)
            

        
        
    # -------------------------------------------------------------------------
    # Telemetry → Ingest DB
    # -------------------------------------------------------------------------
    def _send_tm_to_database(self, data_dict):
        try:
            print("Sending telemetry packet to ingest database")
            self.ingest.send(data_dict)
            print()
        except Exception as e:
            print(f"Failed sending telemetry to DB: {e}")


  
    def init_transaction(self, cmd):
        """
        [check] - should move this to a different section in the file
        Receives a command that has already been checked to be a init_trans command
        will create get the data from the command and init the transaction
        """
        #1. create the transaction on the client side using tid from server
        tid = cmd.get_argument("tid")
        number_of_packets = cmd.get_argument("number_of_packets")
        hash_MSB = cmd.get_argument("hash_MSB")
        hash_middlesb = cmd.get_argument("hash_middlesb")
        hash_LSB = cmd.get_argument("hash_LSB")
        file_hash = hash_MSB.to_bytes(8, byteorder='big') + hash_middlesb.to_bytes(8, byteorder='big') + hash_LSB.to_bytes(4, byteorder='big')
        
        trans = transaction_manager.create_transaction(tid=tid, file_hash=file_hash, number_of_packets=number_of_packets, is_tx=False)
        if trans is None:
            print(f"[ERROR] Could not create transaction for INIT_TRANS")
            return
        
    def add_fragment_to_transaction(self, cmd):
        """
        [check] - should move this to a different section in the file
        receives a command that has already been checked to  be a TRANS_PAYLOAD command
        will add the fragment to the transaction
        """

        tid = cmd.get_argument("tid")
        seq_number = cmd.get_argument("seq_number")
        payload_frag = cmd.get_argument("payload_frag")
        transaction = transaction_manager.get_transaction(tid)
        
        if transaction is None:
            print(f"[ERROR] Transaction with id {tid} not found.")
            return
        
        isCompleted = transaction.add_packet(seq_number, payload_frag)
        
        print(f"[COMMAND PROCESSED] Added payload fragment for transaction id {tid} with sequence number {seq_number} to transaction")
        if isCompleted:
            # print green
            print(f"\033[92m[INFO] Transaction {tid} is complete with {transaction.number_of_packets} packets received.\033[0m")
            transaction.write_file("downlinked_data/main.py")
        
        