import signal
import sys
import time

import RPi.GPIO as GPIO


# from lib.database.database_utils import initialize_database
from lib.groundstation import GS


def hard_exit(radio, signum, frame):
    print()
    print("Received SIGINT: Hard exit")
    radio.close()
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
    
    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(GS.radio, signum, frame),
    )

    lastPrint = time.time()
    printFreq = 10  # seconds

    GS.set_rx_mode()   # set the chip to rx mode
    
    while True:
        # check for availalbe packet
        new_rx_packet = GS.check_rx_packet_available()
        new_tx_packet = GS.check_tx_cmd_available()

        if new_rx_packet:
            print("Got new packet")
            msg_rx = GS.get_rx_packet()
            GS.process_rx_packet(msg_rx)
            
        if new_tx_packet:
            print("Got new command to send")
            GS.transmit_message()
            GS.set_rx_mode()   # go back to rx mode
            
            
        if time.time() - lastPrint >= printFreq:
            lastPrint = time.time()
            print("Waiting for packet...")
            
def digipeater_test():
    """
    This is a test mode for the digipeater functionality of the radio
    Print all the messages to terminal
    and every 10 seconds it will send a lora aprs packet to be repeated
    """
    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(GS.radio, signum, frame),
    )

    lastPrint = time.time()
    lastSend = time.time()
    printFreq = 10  # seconds
    sendFreq = 10  # seconds

    GS.set_rx_mode()   # set the chip to rx mode
    
    digipeater_header = b"\x3c\xff\x01"   # have it here as well to facilitate checking
    lora_aprs_packet = "CS5CEP-1>APRS4;CT6xxx:ARGUS TEST MESSAGE"
    packet = digipeater_header + lora_aprs_packet.encode("utf-8")
    
    while True:
        # check for availalbe packet
        new_rx_packet = GS.check_rx_packet_available()

        if new_rx_packet:
            print("Got new packet")
            msg_rx = GS.get_rx_packet()
            print(f"Received message: {msg_rx}")
            
        if time.time() - lastPrint >= printFreq:
            lastPrint = time.time()
            print("Waiting for packet...")
            
        if time.time() - lastSend >= sendFreq:
            lastSend = time.time()
            print("Sending test packet...")
            GS.radio.send(packet)
            GS.set_rx_mode()   # set the chip to rx mode