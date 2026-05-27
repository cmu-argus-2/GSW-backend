import signal
import sys
import time

import RPi.GPIO as GPIO


# from lib.database.database_utils import initialize_database
from lib.groundstation import GS
from lib.radio_process import RadioProcess


def hard_exit(radio_process, signum, frame):
    print()
    print("Received SIGINT: Hard exit")
    radio_process.close()
    GPIO.cleanup()
    sys.exit(0)


def socket_exit(socket, signum, frame):
    socket.close()
    sys.exit(0)


def op_mode():
    """
    This is the mode that will be used for operation
    It will always listen for messages from the spacecraft unless there are commands to be sent
    it will send received data to the database and get commands via rpc connection
    """
    
    radio_process = RadioProcess()
    radio_process.start()

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radio_process, signum, frame),
    )

    lastPrint = time.time()
    printFreq = 10  # seconds

    while True:
        new_tx_packet = GS.check_tx_cmd_available()

        msg_rx = radio_process.poll_rx_packet()
        if msg_rx is not None:
            print("Got new packet")
            GS.process_rx_packet(msg_rx)
            
        if new_tx_packet:
            print("Got new command to send")
            command_bytes = GS.transmit_message()
            if command_bytes is not None:
                radio_process.send(command_bytes)

        if time.time() - lastPrint >= printFreq:
            lastPrint = time.time()
            print("Waiting for packet...")

            
def digipeater_test():
    """
    This is a test mode for the digipeater functionality of the radio
    Print all the messages to terminal
    and every 10 seconds it will send a lora aprs packet to be repeated
    """
    radio_process = RadioProcess()
    radio_process.start()

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radio_process, signum, frame),
    )

    lastPrint = time.time()
    lastSend = time.time()
    printFreq = 10  # seconds
    sendFreq = 10  # seconds

    digipeater_header = b"\x3c\xff\x01"   # have it here as well to facilitate checking
    lora_aprs_packet = "CS5CEP-1>APRS4;CT6xxx:ARGUS TEST MESSAGE"
    packet = digipeater_header + lora_aprs_packet.encode("utf-8")
    
    while True:
        msg_rx = radio_process.poll_rx_packet()

        if msg_rx is not None:
            print("Got new packet")
            print(f"Received message: {msg_rx}")
            
        if time.time() - lastPrint >= printFreq:
            lastPrint = time.time()
            print("Waiting for packet...")
            
        if time.time() - lastSend >= sendFreq:
            lastSend = time.time()
            print("Sending test packet...")
            radio_process.send(packet)