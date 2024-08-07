import sys

from lib.shell_utils import (receive_loop, receive_loop_emulator,
                             receive_loop_serial, send_command,
                             send_command_emulator, send_command_serial)


while True:
    connection_prompt = """
Are you connecting to the satellite via:
 - (r) Radio Frequency
 - (t) tty/serial
 - (e) emulated/simulated satellite
 - (q) quit
: """
    conn_type = input(connection_prompt)
    if conn_type == 'q':
        sys.exit(0)

    for_prompt = """
Are you...
 - (r) receive heartbeats from satellite
 - (c) sending a command to the satellite
 - (q) quit
: """
    reason = input(for_prompt)
    if reason == 'q':
        sys.exit(0)

    options = {
        "r": {
            "r": receive_loop,
            "c": send_command
        },
        "t": {
            "r": receive_loop_serial,
            "c": send_command_serial,
        },
        "e": {
            "r": receive_loop_emulator,
            "c": send_command_emulator,
        },
    }

    options[conn_type][reason]()
