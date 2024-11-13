from lib.argus_lora import LoRa, ModemConfig
from lib.radiohead import RadioHead


def initialize_radio() -> RadioHead:
    CHANNEL = 0
    INTERRUPT = 19
    ADDRESS = 255
    FREQUENCY = 915.6
    TX_POWER = 14
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
        crypto=CRYTPO)

    # RadioHead wrapper class that overwrites on_recv and adds a receive method
    radiohead = RadioHead(radio, 15)
    return radiohead
