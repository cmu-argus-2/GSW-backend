import signal
import sys

import serial
import socket
from random import randint
from collections import namedtuple

# from lib.database_utils import initialize_database
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
    # database = initialize_database("heartbeats", point)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radiohead, database, signum, frame)
    )

    while True:
        print("waiting for packet...")
        msg = radiohead.receive_message()
        print(msg)
        # if msg is not None:
        #     res = unpack_message(msg)
            # if res is not None:
            #     id, time, data = res
            #     database.upload_data(id, time, data)


def send_command():
    pass


def receive_loop_serial():
    def ser_exit(serial, database, signum, frame):
        serial.close()
        database.client.close()
        sys.exit(0)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: ser_exit(ser, database, signum, frame)
    )
    # the serial port to listen on
    ser = serial.Serial('/dev/ttyACM0')
    database = initialize_database('heartbeats', "serial")
    while True:
        packet = ser.readline()
        if not packet:
            break
        if packet.startswith(b"[100][SERIAL OUTPUT]:"):
            packet_dec = packet.decode('utf-8').strip()
            packet_formatted = packet_dec[23:-1]
            packet_bytes = bytearray.fromhex(packet_formatted)
            packet_dict = receive_message(packet_bytes)
            res = unpack_message(packet_dict)
            if res is not None:
                id, time, msg = res
                database.upload_data(id, time, msg)


def send_command_serial():
    pass


def receive_loop_emulator():
    # emulator will send data via a socket on port 5000
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((socket.gethostname(), 5500))

    database = initialize_database('heartbeats', "emulator")

    while True:
        serversocket.listen()
        (clientsocket, address) = serversocket.accept()
        with clientsocket:
            print(f"connected to {address}")
            while True:
                packet = clientsocket.recv(256)
                if not packet:
                    break
                packet_dict = receive_message(packet)
                res = unpack_message(packet_dict)
                if res is not None:
                    id, time, data = res
                    database.upload_data(id, time, data)


def receive_message(packet):
    header_to = packet[0]
    header_from = packet[1]
    header_id = packet[2]
    header_flags = packet[3]
    message = bytes(packet[4:]) if len(packet) > 4 else b''
    rssi = randint(20, 120)
    snr = randint(0, 300)
    return namedtuple(
        "Payload",
        ['message', 'header_to', 'header_from', 'header_id', 'header_flags', 'rssi', 'snr']
    )(message, header_to, header_from, header_id, header_flags, rssi, snr)


def send_command_emulator():
    pass
