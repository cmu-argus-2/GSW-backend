"""
This is the file that will contain the code that will interact with the command interface
the command interface is a simple web app that will be running on the rpi
it is made using flask. The backend will call functions implemented here to send the commands

it will used xmlrpc to send the commands
"""
import os
import sys

if __name__ == "__main__" and __package__ is None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from lib.telemetry.splat.splat.telemetry_codec import pack, unpack, Report, Variable, Command
from lib.telemetry.splat.splat.telemetry_definition import command_list, argument_dict, COMMAND_IDS
from lib.telemetry.splat.splat.telemetry_helper import get_command_size
from lib.config import COMMAND_INTERFACE_IP, COMMAND_INTERFACE_PORT, SC_CALLSIGN
from lib.telemetry import transaction_middleware

from collections import deque
import threading
import time

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# Create a custom handler that suppresses logs
class QuietRequestHandler(SimpleXMLRPCRequestHandler):
    def log_message(self, format, *args):
        pass  # Do nothing, effectively silencing the log
 
  

class CommandInterfaceGateway:
    
    """
    This is the class that will receive the commands from the user
    the commands will be send via xmlrpc and will be added to the command queue
    groundstation will remove the commands from the command queue and add them to the database as well
    """
    
    def __init__(self, host=COMMAND_INTERFACE_IP, port=COMMAND_INTERFACE_PORT):
        self.command_queue = deque()
        self.ack_queue = deque(maxlen=20)
        self.ack_lock = threading.Lock()
        self.rx_packet_queue = deque(maxlen=200)
        self.rx_packet_lock = threading.Lock()
        self.sc_callsign = SC_CALLSIGN

        self.thread_running = False

        self.server = SimpleXMLRPCServer((host, port), requestHandler=QuietRequestHandler, allow_none=True)
        self.server.register_function(self.add_command, "add_command")   # this is the command that will be  called to add command
        self.server.register_function(self.ping, "ping")    # this is the command that command interface will call to see if the server is available
        self.server.register_function(self.add, "add")      # this is just a test command
        self.server.register_function(self.get_command_definitions, "get_command_definitions") # this is the command that will be called to get the command definitions. It will return a list of command names that can be called
        self.server.register_function(self.get_pending_ack, "get_pending_ack")
        self.server.register_function(self.get_transaction_status, "get_transaction_status")
        self.server.register_function(self.get_new_packets, "get_new_packets")
        self.server.register_function(self.set_sc_callsign, "set_sc_callsign")
        self.server.register_function(self.get_sc_callsign, "get_sc_callsign")
        
        
    # -------------------------------------------------------------------------
    #
    #      These are the commands for transaction
    #
    #-------------------------------------------------------------------------
    
    def create_trans(self, command):
        """
        Function that will be called when aci send create trans function
        this will server to deal with the failure of creating the trans

        the logic to see if should create the trans or not is in transaction middleware
        this just serves as a function to call it


        [check] - need to change this. Including the gs here just for this is a terrible idea
        """

        return transaction_middleware.process_create_trans(command)

    def push_ack(self, response_status):
        """Called in-process by groundstation when an Ack packet is received from the satellite."""
        rid = int(response_status)  # ensure plain int for XML-RPC serialization
        print(f"[push_ack] rid={rid} type={type(response_status).__name__}")
        with self.ack_lock:
            self.ack_queue.append({'rid': rid, 'ts': time.time()})

    def push_received_packet(self, packet_dict):
        """Called in-process by groundstation to queue a decoded packet for the frontend."""
        with self.rx_packet_lock:
            self.rx_packet_queue.append(packet_dict)

    def get_new_packets(self):
        """RPC: Drain and return all queued decoded packets since the last call."""
        with self.rx_packet_lock:
            packets = list(self.rx_packet_queue)
            self.rx_packet_queue.clear()
            return packets

    def get_pending_ack(self):
        """RPC: Pop and return the oldest pending ACK, or None if the queue is empty."""
        with self.ack_lock:
            return self.ack_queue.popleft() if self.ack_queue else None

    def get_transaction_status(self, tid):
        """RPC: Return current status of an RX transaction by tid."""
        import traceback
        try:
            transaction = transaction_middleware.transaction_manager.get_transaction(tid, is_tx=False)
            if transaction is None:
                return {'found': False}
            try:
                missing = list(transaction.missing_fragments) if transaction.missing_fragments is not None else []
            except TypeError:
                missing = []
            try:
                fragments = dict(transaction.fragment_dict) if transaction.fragment_dict is not None else {}
            except TypeError:
                fragments = {}
            state_val = int(transaction.state) if transaction.state is not None else 1
            nop_val = int(transaction.number_of_packets) if transaction.number_of_packets is not None else 0
            recv_val = len(fragments)
            miss_val = len(list(missing))
            print(f"[get_transaction_status] tid={tid} state={state_val} nop={nop_val} recv={recv_val} miss={miss_val}")
            return {
                'found': True,
                'state': state_val,
                'number_of_packets': nop_val,
                'received_packets': recv_val,
                'missing_count': miss_val,
                'missing_fragments': list(missing),
            }
        except Exception as e:
            print(f"[get_transaction_status] ERROR: {e}")
            traceback.print_exc()
            raise

    # -------------------------------------------------------------------------
    #
    #      These are the remote function that will be called
    #
    #-------------------------------------------------------------------------
    
    def get_command_definitions(self):
        """
        This is the function that will return the available command
        this command will be used to avoid needing to have splat in aci

            
            
            
        """
        definitions = []

        for cmd_name, precondition, arguments in command_list:
            command_info = {
                "name": cmd_name,
                "id": COMMAND_IDS[cmd_name],
                "size": get_command_size(cmd_name),
                "precondition": precondition if precondition is not None else "",
                "arguments": [
                    {
                        "name": arg_name,
                        "type": argument_dict[arg_name],
                    }
                    for arg_name in arguments
                ],
            }
            definitions.append(command_info)

        return definitions
        
    def add_command(self, cmd_name, cmd_args):
        """
        This is the function that will be called to add a command
        it will receive a json with cmd_name and cmd_args
        cmd_args will already be in the correct type
        """
        
        print(f"Received command: cmd_name={cmd_name}, cmd_args={cmd_args}")
        
        # check if cmd has cmd_name and cmd_args
        if type(cmd_name) != str or type(cmd_args) != dict:
            print("Invalid command format")
            print(f"   Received cmd_name: {cmd_name}, type: {type(cmd_name)}")
            return False
        
        commnad = Command(cmd_name)
                
        for arg_name, arg_value in cmd_args.items():
            commnad.add_argument(arg_name, arg_value)
            
        # check to see if command is create_trans
        if cmd_name == "CREATE_TRANS":
            if not self.create_trans(commnad):
                # means that creating the transaction failed and I do not want to send the message
                return False
                

        self.command_queue.append(commnad)
        print(f"Added command to queue: {commnad}")

        return True
    
    def set_sc_callsign(self, callsign):
        """RPC: Set the active satellite callsign."""
        self.sc_callsign = str(callsign)
        print(f"[set_sc_callsign] Active satellite set to: {self.sc_callsign}")
        return True

    def get_sc_callsign(self):
        """RPC: Return the currently selected satellite callsign."""
        return self.sc_callsign

    def ping(self):
        """
        Function that will be called by command interface periodically to see if everything is working
        """
        # print("ping received")
        return True

    def add(self, x, y):
        """Simple test function to add two numbers"""
        return x + y
    
    def serve_in_thread(self):
        """
        This is the function that will be called by the groundstation
        it will start the server in a separate thread and return
        
        thread_running will be set to true. If someone changes it to false, the server will stop
        """
        if self.thread_running:
            print("Server is already running in a thread")
            return
        
        self.thread_running = True
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        

    def serve_forever(self):
        """Start the XML-RPC server to handle incoming requests."""
        print("Command Interface Gateway is running...")
        
        # 1. Set a timeout (e.g., 0.5 seconds). 
        # This ensures handle_request() returns periodically even if no data is sent,
        # allowing the loop to check if self.thread_running is still True.
        self.server.socket.settimeout(0.5)

        try:            
            # 2. Loop while the flag is True
            while self.thread_running:
                # 3. Handle a single request, then loop back to check the flag
                self.server.handle_request()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            # 4. Cleanup when the loop breaks
            self.server.server_close()
            print("Exiting Command Interface Gateway")


    # -------------------------------------------------------------------------
    #      Local functions. They will be called by the groundstation 
    #        in order to get the next command
    #      
    # -------------------------------------------------------------------------
    
    
    def pop_command(self):
        """
        This function will be called by the groundstation to get the next command
        it will return None if there are no commands in the queue
        if there are commands in the queue it will return the first command and remove it
        return Command Object
        """
        
        if self.command_queue:
            cmd = self.command_queue.popleft()
            print(f"Removed command from queue: {cmd}")
            return cmd
        
        return None

    def commands_available(self):
        """
        This function will be called by the groundstation to see if there are commands in the queue
        it will return the number of commands in the queue
        """
        return len(self.command_queue)


def main():
    gateway = CommandInterfaceGateway()

    try:
        gateway.thread_running = True
        gateway.serve_forever()
    except KeyboardInterrupt:
        gateway.thread_running = False
        print("Stopping Command Interface Gateway...")


if __name__ == "__main__":
    main()
    