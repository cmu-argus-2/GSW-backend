import datetime

from lib.argus_lora import LoRa, ModemConfig
from lib.radiohead import RadioHead
from lib.unpacking import TelemetryUnpacker


def unpack_header(msg):
    message_ID = int.from_bytes((msg.message[0:1]), byteorder='big') & 0b01111111
    message_sequence_count = int.from_bytes(msg.message[1:3], byteorder='big')
    message_size = int.from_bytes(msg.message[3:4], byteorder='big')

    return message_ID, message_sequence_count, message_size


def unpack_message(msg):
    # Get the current time
    current_time = datetime.datetime.now()
    # Format the current time
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
    formatted_time = formatted_time.encode('utf-8')

    msg_ID, msg_sc, msg_size = unpack_header(msg)

    if(msg_ID == 0x01):
        TelemetryUnpacker.unpack_tm_frame(msg.message)

    return msg_ID


def initialize_radio() -> RadioHead:
    CHANNEL = 0
    INTERRUPT = 19
    ADDRESS = 25
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
