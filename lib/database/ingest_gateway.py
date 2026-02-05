import socket
import json
from typing import Any, Dict


class IngestError(Exception):
    pass


class Ingest:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5555,
        timeout: float = 5.0,
        retries: int = 3,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def send(self, telemetry_dict: Dict[str, Any]) -> str:
        payload = (json.dumps(telemetry_dict) + "\n").encode("utf-8")
        last_error = None
        for _ in range(self.retries):
            try:
                return self._send_once(payload)
            except (socket.timeout, socket.error, IngestError) as e:
                print(f"Ingest attempt failed: {e}")
                last_error = e
                return None

    def _send_once(self, payload: bytes) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            sock.sendall(payload)
            response = self._recv_line(sock)
            if not response:
                return None
            return response

    @staticmethod
    def _recv_line(sock: socket.socket) -> str:
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(1024)
            if not chunk:
                break
            data += chunk
        return data.decode("utf-8").strip()
