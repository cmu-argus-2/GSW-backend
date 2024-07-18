import signal
import sys

from lib.radio_utils import initialize_radio, unpack_message
from lib.database_utils import initialize_database


def hard_exit(radiohead, db, signum, frame):
    print("hard exit")
    radiohead.radio.close()
    db.client.close()
    sys.exit(0)


def receive_loop():
    radiohead = initialize_radio()

    point_prompt = "Tag for stored data (leave blank for argus-1):"
    point = input(point_prompt) or "argus-1"
    database = initialize_database("heartbeats", point)

    signal.signal(
        signal.SIGINT,
        lambda signum, frame: hard_exit(radiohead, database, signum, frame)
    )

    while True:
        print("waiting for packet...")
        msg = radiohead.receive_message()
        if msg is not None:
            res = unpack_message(msg)
            if res is not None:
                id, time, data = res
                database.upload_data(id, time, data)
