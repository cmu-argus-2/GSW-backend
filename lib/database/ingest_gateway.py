"""
Implement class that will be used to send things to the gs_database
simple class to facilitate sending data to the database
"""




import socket
import json


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
        """
        Simple telemetry ingest client.

        Usage:
            ingest = Ingest()
            ingest.send(data_dict)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries

    # ------------------------------------------------------------------ #

    def send(self, telemetry_dict: Dict[str, Any]) -> str:
        """
        Send telemetry to the ingest server.

        This method:
        - Opens a socket
        - Sends data
        - Waits for ACK
        - Closes the socket
        - Retries on failure
        """
        payload = (json.dumps(telemetry_dict) + "\n").encode("utf-8")

        last_error = None

        for _ in range(self.retries):
            try:
                return self._send_once(payload)
            except (socket.timeout, socket.error, IngestError) as e:
                print(f"Ingest attempt failed: {e}")
                last_error = e
                return None

        # raise IngestError(f"Ingest failed after {self.retries} retries: {last_error}")

    # ------------------------------------------------------------------ #

    def _send_once(self, payload: bytes) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)

            sock.connect((self.host, self.port))
            sock.sendall(payload)

            response = self._recv_line(sock)

            if not response:
                return None
                raise IngestError("No response from ingest server")

            return response

    # ------------------------------------------------------------------ #

    @staticmethod
    def _recv_line(sock: socket.socket) -> str:
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(1024)
            if not chunk:
                break
            data += chunk

        return data.decode("utf-8").strip()
