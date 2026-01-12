"""
The idea is to have here a single file where I can edit the radio config for all the testing files that I am doing
"""


config_dict = {
    "frequency": 433.707+0.010,
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