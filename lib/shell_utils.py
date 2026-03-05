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