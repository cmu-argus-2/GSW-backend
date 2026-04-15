import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from lib.shell_utils import op_mode


def run_http_server():
    server_address = ("0.0.0.0", 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("HTTP server running on port 8000...")
    httpd.serve_forever()


# Start server in background thread
server_thread = threading.Thread(target=run_http_server, daemon=True)
server_thread.start()


# Your CLI loop (unchanged)
while True:
    connection_prompt = """
What operation mode do you want?
(o) Operations Mode 
(q) quit   
Input:  """
    conn_type = input(connection_prompt)

    if conn_type == "q":
        sys.exit(0)

    options = {
        "o": op_mode
    }

    options[conn_type]()