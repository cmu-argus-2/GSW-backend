import sys


from lib.shell_utils import op_mode, digipeater_test


while True:
    connection_prompt = """
What operation mode do you want?
(o) Operations Mode 
(d) Digipeater Test Mode
(q) quit   
Input:  """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "o": op_mode,
        "d": digipeater_test
    }

    options[conn_type]()

