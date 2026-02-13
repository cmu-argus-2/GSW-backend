import sys


from lib.shell_utils import (receive_loop, transmit_loop, downlink_all, op_mode)


while True:
    connection_prompt = """
What operation mode do you want?
(r) Normal Operation [Downlink and Uplink Functionality]
(d) Downlink All Mode
(t) Only Transmit Operation 
(o) Only Downlink Operation
(q) quit   
Input: """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "r": receive_loop, 
        "d": downlink_all,
        "t": transmit_loop,
        "o": op_mode
    }

    options[conn_type]()
