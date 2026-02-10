import sys
import threading

from lib.shell_utils import (receive_loop, transmit_loop, downlink_all)
from lib.database.db_server import app

# Start Flask API server in a background thread
api_thread = threading.Thread(
    target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False),
    daemon=True,
)
api_thread.start()

while True:
    connection_prompt = """
What operation mode do you want?
(r) Normal Operation [Downlink and Uplink Functionality]
(d) Downlink All Mode
(t) Only Transmit Operation 
(q) quit   
Input: """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "r": receive_loop, 
        "d": downlink_all,
        "t": transmit_loop,
    }

    options[conn_type]()
