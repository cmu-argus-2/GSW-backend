import signal
import sys

from influxdb import Database
from radio_utils import initialize_radio, unpack_message
from database_utils import initialize_database


def hard_exit(radio, db, signum, frame):
    print("hard exit")
    radio.close()
    db.client.close()
    sys.exit(0)


def receive_loop():
    radio = initialize_radio()

    point_prompt = "Tag for stored data (leave blank for argus-1):"
    point = input(point_prompt) or "argus-1"
    database = initialize_database("heartbeats", point)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radio, database, signum, frame)
    )

    while True:
        print("waiting for packet...")
        msg = radio.receive_message()
        if msg is not None:
            res = unpack_message(msg)
            if res is not None:
                id, time, data = res
                database.upload_data(id, time, data)
