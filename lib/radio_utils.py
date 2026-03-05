from lib.argus_lora import LoRa, ModemConfig

from lib.config import ARGUS_FREQ


def initialize_radio() -> LoRa:
    CHANNEL = 0
    INTERRUPT = 19    # this is the interupt pin
    ADDRESS = 255
    FREQUENCY = ARGUS_FREQ
    TX_POWER = 23
    MODEM_CONFIG = ModemConfig.Bw125Cr45Sf128
    RECEIVE_ALL = False
    ACKS = False
    CRYTPO = None

    # initialize radio instance
    radio = LoRa(
        CHANNEL,
        INTERRUPT,
        ADDRESS,
        modem_config=MODEM_CONFIG,
        freq=FREQUENCY,
        tx_power=TX_POWER,
        receive_all=RECEIVE_ALL,
        acks=ACKS,
        crypto=CRYTPO,
    )
    
    return radio
