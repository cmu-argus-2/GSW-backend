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

from lib.gs_constants import MSG_ID
from lib.telemetry.unpacking import RECEIVE
from lib.database.ingest_gateway import Ingest

from lib.telemetry.splat.telemetry_codec import Report, Variable, Command


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
    def __init__(self, ingest_host="172.20.48.220", ingest_port=5555):
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
    # Command Queue Handling
    # -------------------------------------------------------------------------
    def add_command(self, cmd: Command):
        print(f"Adding command to queue: {cmd}")
        self.command_queue.append(cmd)

    def get_next_command(self):
        if not self.command_queue:
            return None
        return self.command_queue[0]

    def pop_command(self):
        if self.command_queue:
            cmd = self.command_queue.popleft()
            print(f"Removed command from queue: {cmd}")
            return cmd
        return None

    def commands_available(self):
        return len(self.command_queue)

    # -------------------------------------------------------------------------
    # Start TCP Socket for Commands
    # -------------------------------------------------------------------------
    def start_command_socket(self, host="0.0.0.0", port=6000):
        self.running = True
        self.socket_thread = threading.Thread(
            target=self._socket_server,
            args=(host, port),
            daemon=True,
        )
        self.socket_thread.start()
        print(f"Command socket started on {host}:{port}")

    def stop(self):
        self.running = False
        print("GS Gateway shutting down")

    # -------------------------------------------------------------------------
    # Socket Server
    # -------------------------------------------------------------------------
    def _socket_server(self, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((host, port))
                server.listen()

                while self.running:
                    conn, addr = server.accept()
                    print()
                    print(f"Command connection from {addr}")

                    threading.Thread(
                        target=self._handle_client,
                        args=(conn,),
                        daemon=True,
                    ).start()

        except Exception as e:
            print(f"Socket server error: {e}")

    def _handle_client(self, conn):
        with conn:
            try:
                buffer = ""

                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    buffer += data.decode()

                    # Process JSON lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        self._process_command_line(line.strip())

            except Exception as e:
                print(f"Client handling error: {e}")

    def _process_command_line(self, line: str):
        """
        Process the commands received from the socket
        with the received data will create the command object
        should receive a dict with 
        {
            "name": "COMMAND_NAME",
            "args": [(arg1, value), (arg2, value), ...]
        }
        """
        
        try:
            print ("Processing command line: ", line)
            cmd = json.loads(line)
            
            if "name" not in cmd or "args" not in cmd:
                raise ValueError("Command must have 'name' and 'args' fields")
            
            command_name = cmd["name"]
            argument_list = cmd["args"]  # should be a list of (arg_name, value)

            command = Command(command_name)
            for arg_name, value in argument_list:
                command.add_argument(arg_name, value)

            self.add_command(command)
            print(f"Command received from socket: {command}")

        except Exception as e:
            print(f"Bad command received: {line} | Error: {e}")
        
        print()

    # -------------------------------------------------------------------------
    # Entry point for satellite packets
    # -------------------------------------------------------------------------
    def handle_downlink(self, msg_id, raw_message):
        try:
            unpacked = RECEIVE.unpack_frame(msg_id, raw_message)
            print("Unpacked data: ", unpacked)
        except Exception as e:
            print(f"Failed to unpack frame: {e}")
            return

        if msg_id == MSG_ID.SAT_FILE_METADATA:
            self._handle_file_metadata(unpacked)

        elif msg_id == MSG_ID.SAT_DOWNLINK_ALL_FILES:
            self._log_file_csv(msg_id)

        elif msg_id in MSG_ID.TM_FRAME_TYPES:
            self._send_tm_to_database(unpacked)

        else:
            print(f"Unhandled message type: {msg_id}")
            
    
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
        
        # pretty print the report.variables
        for ss_name, vars in report.variables.items():
            for var_name, value in vars.items():
                print(f"  {ss_name}-{var_name}: {value}")
        
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
        
        
        

    # -------------------------------------------------------------------------
    # File Metadata Handling
    # -------------------------------------------------------------------------
    def _handle_file_metadata(self, unpacked):
        try:
            md = unpacked["METADATA"]

            self.current_file_metadata = {
                "file_id": md["FILE_ID"],
                "file_time": md["FILE_TIME"],
                "file_size": md["FILE_SIZE"],
                "file_target_sq": md["FILE_TARGET_SQ"],
            }

            print(f"Stored file metadata: {self.current_file_metadata}")

        except KeyError as e:
            print(f"Bad metadata packet: missing {e}")

    # -------------------------------------------------------------------------
    # CSV Logging
    # -------------------------------------------------------------------------
    def _log_file_csv(self, msg_id):
        csv_file = "downlink_log.csv"
        fieldnames = [
            "timestamp",
            "msg_id",
            "file_id",
            "file_time",
            "file_size",
            "file_target_sq",
        ]

        try:
            file_exists = os.path.isfile(csv_file)

            with open(csv_file, mode="a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    "timestamp": time.time(),
                    "msg_id": msg_id,
                    **self.current_file_metadata,
                })

            print("Logged file entry to CSV")

        except Exception as e:
            print(f"Failed writing CSV: {e}")

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
