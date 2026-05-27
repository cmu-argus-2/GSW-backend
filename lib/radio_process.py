import multiprocessing as mp
import queue

from lib.radio_utils_fsk import initialize_radio


def _radio_worker(tx_queue, rx_queue, stop_event):
    radio = initialize_radio()

    def enqueue_payload(payload):
        rx_queue.put((bytes(payload.message), payload.rssi, payload.snr))

    radio.on_recv = enqueue_payload
    radio.set_mode_rx()

    try:
        while not stop_event.is_set():
            try:
                tx_payload = tx_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if tx_payload is None:
                continue

            radio.send(tx_payload, 255, 0, 0)
    finally:
        radio.close()


class RadioProcess:
    def __init__(self):
        context = mp.get_context("spawn")
        self._tx_queue = context.Queue()
        self._rx_queue = context.Queue()
        self._stop_event = context.Event()
        self._process = context.Process(
            target=_radio_worker,
            args=(self._tx_queue, self._rx_queue, self._stop_event),
            daemon=True,
        )

    def start(self):
        self._process.start()

    def send(self, payload):
        self._tx_queue.put(payload)

    def poll_rx_packet(self):
        try:
            return self._rx_queue.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        self._stop_event.set()
        self._tx_queue.put(None)
        if self._process.is_alive():
            self._process.join(timeout=2)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2)