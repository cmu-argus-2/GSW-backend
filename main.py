import sys

from scripts.remote_update import run_remote_update
run_remote_update()


from lib.shell_utils import op_mode
op_mode()

while True:
    connection_prompt = """
What operation mode do you want?
(o) Operations Mode 
(q) quit   
Input: """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "o": op_mode
    }

    options[conn_type]()

