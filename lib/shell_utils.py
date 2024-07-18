import signal
import sys

import serial
import socket

from lib.database_utils import initialize_database
from lib.radio_utils import initialize_radio, unpack_message


def hard_exit(radiohead, db, signum, frame):
    print("hard exit")
    radiohead.radio.close()
    db.client.close()
    sys.exit(0)


def socket_exit(socket, signum, frame):
    socket.close()
    sys.exit(0)


def receive_loop():
    radiohead = initialize_radio()

    point_prompt = "Tag for stored data (leave blank for argus-1):"
    point = input(point_prompt) or "argus-1"
    database = initialize_database("heartbeats", point)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radiohead, database, signum, frame)
    )

    while True:
        print("waiting for packet...")
        msg = radiohead.receive_message()
        if msg is not None:
            res = unpack_message(msg)
            if res is not None:
                id, time, data = res
                database.upload_data(id, time, data)


def send_command():
    pass


def receive_loop_serial():
    # the serial port to listen on
    ser = serial.Serial('/dev/ttyACM0')
    while True:
        print(ser.readlines())


def send_command_serial():
    pass


def receive_loop_emulator():
    # emulator will send data via a socket on port 5000
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((socket.gethostname(), 5000))

    database = initialize_database('heartbeats', "emulator")

    while True:
        serversocket.listen()
        (clientsocket, address) = serversocket.accept()
        with clientsocket:
            print(f"connected to {address}")
            while True:
                data = clientsocket.recv(256)
                if not data:
                    break
                print(data)
                # res = unpack_message(data)
                # if res is not None:
                #     id, time, data = res
                #     print(id, time, data)
                #     database.upload_data(id, time, data)


def send_command_emulator():
    pass
