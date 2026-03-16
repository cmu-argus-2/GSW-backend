"""
This is the file that will contain the code that will interact with the command interface
the command interface is a simple web app that will be running on the rpi
it is made using flask. The backend will call functions implemented here to send the commands

it will used xmlrpc to send the commands
"""
from datetime import datetime, timezone

from lib.telemetry.splat.splat.telemetry_codec import pack, unpack, Report, Variable, Command
from lib.config import COMMAND_INTERFACE_IP, COMMAND_INTERFACE_PORT
from lib.telemetry import transaction_middleware
from lib.session_logger import get_session_logger

from collections import deque
import threading

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler


class CommandXMLRPCServer(SimpleXMLRPCServer):
    """XML-RPC server that exposes the current client IP to handlers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_local = threading.local()

    def verify_request(self, request, client_address):
        self._thread_local.client_ip = client_address[0]
        return super().verify_request(request, client_address)

    def get_client_ip(self):
        return getattr(self._thread_local, "client_ip", "unknown")

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

        self.thread_running = False

        self.command_logger = get_session_logger("command_interface.commands")

        self.server = CommandXMLRPCServer((host, port), requestHandler=QuietRequestHandler)  # <--- Use the quiet class here)
        self.server.register_function(self.add_command, "add_command")   # this is the command that will be  called to add command
        self.server.register_function(self.ping, "ping")    # this is the command that command interface will call to see if the server is available
        self.server.register_function(self.add, "add")      # this is just a test command

    def _log_command_event(self, event, cmd_name, cmd_args, sender_ip, success, error=None, queue_wait_ms=None):
        timestamp = datetime.now(timezone.utc).isoformat()
        message = (
            f"event={event} "
            f"cmd={cmd_name} "
            f"args={cmd_args} "
            f"time={timestamp} "
            f"sender_ip={sender_ip} "
            f"success={success} "
            f"queue_size={len(self.command_queue)}"
        )

        if queue_wait_ms is not None:
            message += f" queue_wait_ms={queue_wait_ms:.2f}"

        if error:
            message += f" error={error}"

        self.command_logger.info(message)
        
        
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
    
    # -------------------------------------------------------------------------
    #
    #      These are the remote function that will be called
    #
    #-------------------------------------------------------------------------
    
    def add_command(self, cmd_name, cmd_args):
        """
        This is the function that will be called to add a command
        it will receive a json with cmd_name and cmd_args
        cmd_args will already be in the correct type
        """
        
        sender_ip = self.server.get_client_ip()
        print(f"Received command: cmd_name={cmd_name}, cmd_args={cmd_args}, sender_ip={sender_ip}")
        
        # check if cmd has cmd_name and cmd_args
        if type(cmd_name) != str or type(cmd_args) != dict:
            print("Invalid command format")
            print(f"   Received cmd_name: {cmd_name}, type: {type(cmd_name)}")
            self._log_command_event(
                event="received",
                cmd_name=cmd_name,
                cmd_args=cmd_args,
                sender_ip=sender_ip,
                success=False,
                error="invalid_command_format",
            )
            return False

        try:
            commnad = Command(cmd_name)
            for arg_name, arg_value in cmd_args.items():
                commnad.add_argument(arg_name, arg_value)
        except Exception as e:
            self._log_command_event(
                event="received",
                cmd_name=cmd_name,
                cmd_args=cmd_args,
                sender_ip=sender_ip,
                success=False,
                error=str(e),
            )
            return False

        commnad.sender_ip = sender_ip
        commnad.received_at_utc = datetime.now(timezone.utc)
            
        # check to see if command is create_trans
        if cmd_name == "CREATE_TRANS":
            if not self.create_trans(commnad):
                # means that creating the transaction failed and I do not want to send the message
                self._log_command_event(
                    event="received",
                    cmd_name=cmd_name,
                    cmd_args=cmd_args,
                    sender_ip=sender_ip,
                    success=False,
                    error="create_trans_failed",
                )
                return False
                

        self.command_queue.append(commnad)
        print(f"Added command to queue: {commnad}")
        self._log_command_event(
            event="received",
            cmd_name=cmd_name,
            cmd_args=cmd_args,
            sender_ip=sender_ip,
            success=True,
        )

        return True
    
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

            queue_wait_ms = None
            if hasattr(cmd, "received_at_utc") and cmd.received_at_utc is not None:
                queue_wait_ms = (datetime.now(timezone.utc) - cmd.received_at_utc).total_seconds() * 1000

            self._log_command_event(
                event="sent",
                cmd_name=cmd.name,
                cmd_args=cmd.arguments,
                sender_ip=getattr(cmd, "sender_ip", "unknown"),
                success=True,
                queue_wait_ms=queue_wait_ms,
            )
            return cmd
        
        return None

    def commands_available(self):
        """
        This function will be called by the groundstation to see if there are commands in the queue
        it will return the number of commands in the queue
        """
        return len(self.command_queue)
    