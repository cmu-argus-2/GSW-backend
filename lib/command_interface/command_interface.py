"""
This is the file that will contain the code that will interact with the command interface
the command interface is a simple web app that will be running on the rpi
it is made using flask. The backend will call functions implemented here to send the commands

it will used xmlrpc to send the commands
"""
from lib.telemetry.splat.splat.telemetry_codec import pack, unpack, Report, Variable, Command


from collections import deque
import threading

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
    
    def __init__(self, host="0.0.0.0", port=8000):
        self.command_queue = deque()

        self.thread_running = False

        self.server = SimpleXMLRPCServer((host, port), requestHandler=QuietRequestHandler)  # <--- Use the quiet class here)
        self.server.register_function(self.add_command, "add_command")   # this is the command that will be  called to add command
        self.server.register_function(self.ping, "ping")    # this is the command that command interface will call to see if the server is available
        self.server.register_function(self.add, "add")      # this is just a test command

    
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
        
        print(f"Received command: cmd_name={cmd_name}, cmd_args={cmd_args}")
        
        # check if cmd has cmd_name and cmd_args
        if type(cmd_name) != str or type(cmd_args) != dict:
            print("Invalid command format")
            print(f"   Received cmd_name: {cmd_name}, type: {type(cmd_name)}")
            return False
        
        commnad = Command(cmd_name)
                
        for arg_name, arg_value in cmd_args.items():
            commnad.add_argument(arg_name, arg_value)

        self.command_queue.append(commnad)
        print(f"Added command to queue: {commnad}")

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
            print("Server running on %s:%s" % self.server.server_address)
            
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
    