"""
Simple code that will read the temperature from the FSK module
"""

import time

from lib.argus_fsk import RFM9xFSK

# lets start testing the new fsk class
fsk_radio = RFM9xFSK(frequency=433.707, 
                     sync_word=b"\x69\x96",
                     preamble_length=20,
                     high_power=True,
                     crc = False)

operation_mode = fsk_radio.operation_mode
print(f"FSK Radio Operation Mode: {operation_mode}")

# lets try and read the temperature from the fsk module
temp = fsk_radio.temperature
print(f"FSK Radio Temperature: {temp} C")

# lets put the module in receive mode
fsk_radio.receive()


operation_mode = fsk_radio.operation_mode
print(f"FSK Radio Operation Mode: {operation_mode}")

while True:
    # lets try and read the temperature from the fsk module
    temp = fsk_radio.temperature
    print(f"FSK Radio Temperature: {temp} C")
    time.sleep(5)