"""
Simple code that will send a message every few seconds and wait for a response
"""
import time

from lib.argus_fsk import RFM9xFSK

from radio_config import config_dict

# lets start testing the new fsk class
fsk_radio = RFM9xFSK(config_dict)


transmit_interval = 0.1


while True:
    # print the current rssi
    print(f"Current RSSI: {fsk_radio.rssi} dBm")
    time.sleep(transmit_interval)