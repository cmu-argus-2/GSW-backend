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
    
    def add_report(self, report, callsign):
        """
        Will add a report to the database
        this report is the object defined in telemetry codec

        [check] - should add here the callsign somehow
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
        
    def add_variable(self, variable, callsign):
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
  
        
    def add_command(self, command, callsign):
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
        
        pass
            

        
        
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

