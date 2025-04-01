import sys

from lib.shell_utils import (receive_loop, transmit_loop)

while True:
    connection_prompt = """


What operation mode do you want?
(r) Normal Operation [Downlink and Uplink Functionality]
(t) Only Transmit Operation 
(q) quit   
: """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "r": receive_loop, 
        "t" : transmit_loop,
    }

    options[conn_type]()
