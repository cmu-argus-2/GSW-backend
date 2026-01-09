"""
Simple code that will send a message every few seconds and wait for a response
"""
import time

from lib.argus_fsk import RFM9xFSK



config_dict = {
    "frequency": 433.707,
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


transmit_interval = 0.1


while True:
    # print the current rssi
    print(f"Current RSSI: {fsk_radio.rssi} dBm")
    time.sleep(transmit_interval)