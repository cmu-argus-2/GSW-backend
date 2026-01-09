"""
Simple code that will send a message every few seconds and wait for a response
"""
import time

from lib.argus_fsk import RFM9xFSK



config_dict = {
    "frequency": 433.707+0.0096,
    "high_power": True,
    "power": 20,
    
    "afc_auto": 0,
    "data_mode": 0,  # packet mode
    "packet_format": 1,  # variable length
    "max_packet_length": 200,
    
    "bt": 0.0,
    "rx_bw": 15000,
    "bit_rate": 4000,
    "fdev": 1000,
    
    "sync_word": b"\x69\x96",
    "preamble_length": 100,
    
    "crc": False,
    "whitening": 00 # 01 manchester, 10 whitening, 00 none
}

# lets start testing the new fsk class
fsk_radio = RFM9xFSK(config_dict)


transmit_interval = 10


# initialize counter
counter = 0
# send a broadcast mesage
time.sleep(5)
print("Sending initial message")
fsk_radio.send(bytes(f"message number {counter}", "UTF-8"))
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
