import signal
import sys
import time
import threading

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
    lora_aprs_packet = "CS5CEP-1>APRS4,CT6xxx:ARGUS TEST MESSAGE"
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
            

def digi_demo():
    """
    Code that will be used to demonstrate the digipeater at the fair
    there will be two lora terminals running this code. The satellite will be running with digipeater on
    
    terminal shows > and whatever the user writes, after it presses enter, it will packet into the digipeater message
    it will print in blue the full packet message and it will send the message
    
    it will also print in green any received messages
    probably need to run the receive code on a thread
    """

    # ANSI terminal colors
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    digipeater_header = b"\x3c\xff\x01"

    # Change these as needed for each terminal
    callsign = "CS5CEP-1"
    destination = "APRS4"
    path = "CT6ENG"

    stop_event = threading.Event()
    radio_lock = threading.Lock()

    def cleanup_and_exit(signum=None, frame=None):
        print()
        print(f"{RED}Exiting digi demo...{RESET}")
        stop_event.set()

        try:
            with radio_lock:
                GS.radio.close()
        except Exception as e:
            print(f"{RED}Error closing radio: {e}{RESET}")

        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"{RED}Error cleaning GPIO: {e}{RESET}")

        sys.exit(0)

    def rx_worker():
        """
        Background thread that continuously listens for incoming packets.
        """
        while not stop_event.is_set():
            try:
                with radio_lock:
                    new_rx_packet = GS.check_rx_packet_available()

                    if new_rx_packet:
                        msg_rx = GS.get_rx_packet()
                    else:
                        msg_rx = None

                if msg_rx is not None:
                    print()
                    print(f"{GREEN}RX: {msg_rx}{RESET}")
                    print("> ", end="", flush=True)

            except Exception as e:
                print()
                print(f"{RED}RX error: {e}{RESET}")
                print("> ", end="", flush=True)

            time.sleep(0.05)

    signal.signal(signal.SIGINT, cleanup_and_exit)

    print(f"{YELLOW}Starting digipeater demo mode{RESET}")
    print(f"{YELLOW}Type a message and press Enter to send.{RESET}")
    print(f"{YELLOW}Press Ctrl+C to exit.{RESET}")
    print()

    with radio_lock:
        GS.set_rx_mode()

    rx_thread = threading.Thread(target=rx_worker, daemon=True)
    rx_thread.start()

    while True:
        try:
            user_msg = input("> ").strip()

            if not user_msg:
                continue

            aprs_packet = f"{callsign}>{destination},{path}:{user_msg}"
            packet = digipeater_header + aprs_packet.encode("utf-8")

            print(f"{BLUE}TX: {packet}{RESET}")

            with radio_lock:
                GS.radio.send(packet)
                GS.set_rx_mode()

        except EOFError:
            cleanup_and_exit()

        except KeyboardInterrupt:
            cleanup_and_exit()

        except Exception as e:
            print(f"{RED}TX error: {e}{RESET}")

            try:
                with radio_lock:
                    GS.set_rx_mode()
            except Exception:
                pass