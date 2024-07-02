import signal
import sys

from lib.argus_lora import LoRa, ModemConfig
from lib.radio_utils import unpack_message
from lib.radiohead import RadioHead
from lib.influxdb import Database


radio = LoRa(0, 19, 25, modem_config=ModemConfig.Bw125Cr45Sf128, acks=False, freq=433)
radiohead = RadioHead(radio, 15)

database = Database()


def hard_exit(radio, signum, fram):
    radio.close()
    database.client.close()
    sys.exit(0)


signal.signal(signal.SIGINT, lambda signum, frame: hard_exit(radio, signum, frame))

while True:
    print("waiting for packet...")
    msg = radiohead.receive_message()
    if msg is not None:
        res = unpack_message(msg)
        if res is not None:
            id, time, data = res
            database.upload_data(id, time, data)
