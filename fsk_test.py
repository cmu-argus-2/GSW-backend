"""
Simple code that will send a message every few seconds and wait for a response
"""
import time

from lib.argus_fsk import RFM9xFSK

from radio_config import config_dict

# lets start testing the new fsk class
fsk_radio = RFM9xFSK(config_dict)
fsk_radio.modulation_type = 0  # FSK


transmit_interval = 10


# initialize counter
counter = 0
# send a broadcast mesage
print("Sending initial message")
while True:
    
    fsk_radio.send(bytes(f"message number {counter}", "UTF-8"))

    #print regop
    op_mode = fsk_radio.read_u8(0x01)
    print(f"Operation Mode Register (bits): {op_mode:08b}")
    time.sleep(5)
    
# Wait to receive packets.
print("Waiting for packets...")
# initialize flag and timer
time_now = time.monotonic()
while True:
    # Look for a new packet - wait up to 5 seconds:
    packet = fsk_radio.receive(timeout=2.0)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print(f"Received (raw bytes): {packet}")
        
        # print the packet as 0x00 hex values
        print("Received (hex):", " ".join([f"0x{b:02X}" for b in packet]))
        
        # send reading after any packet received
    if time.monotonic() - time_now > transmit_interval:
        # reset timeer
        time_now = time.monotonic()
    
    
        counter = counter + 1
        print("Sending message number", counter)
        fsk_radio.send(bytes(f"message number {counter}", "UTF-8"))
    # #read the temperature
    # temp = fsk_radio.temperature
    # print(f"FSK Radio Temperature: {temp} C")
    # time.sleep(1)
