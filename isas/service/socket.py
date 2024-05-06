import logging
import queue
import socket
import threading
import time

logger = logging.getLogger(__name__)


class SocketServer(threading.Thread):
    """Socket Server for receiving data from other service."""

    def __init__(
            self,
            address: tuple[str | int],
            queue: queue,
            service_name: str = 'socket_server',
            bufsize: int = 1024
            ) -> None:
        """Initialize Socket Server.

        Args:
            address: A tuple containing IP adress (str) and port (int).
            queue: A queue in which data is stored.
            service_name: Own service name usd in print.
            bufsize: Buffer size.
        """
        self.address = address
        self.queue = queue
        self.service_name = service_name
        logger.info(f'[SocketServer/{self.service_name}/{self.address}] Initializing.')
        super().__init__()
        self.bufsize = bufsize
        self.stop_event = threading.Event()
        self.deamon = True

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        """Receive data."""
        logger.info(f'[SocketServer/{self.service_name}/{self.address}] Running.')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(self.address)
            s.listen(1)
            while not self.stop_event.is_set():
                try:
                    self._recv(s)
                except socket.timeout:
                    pass

    def _recv(
            self,
            socket: socket.socket,
            ) -> None:
        conn, addr = socket.accept()
        data = []
        with conn:
            while True:
                packet = conn.recv(self.bufsize)
                if not packet:
                    break
                data.append(packet)
        data = b''.join(data)
        self.queue.put(data)
        logger.debug(f'[SocketServer/{self.service_name}/{self.address}] Recieve {data=}.')


class SocketClient:
    """Socker Client for sending data to other service."""

    def __init__(
            self,
            address: tuple[str | int],
            service_name: str = 'socket_client'
            ) -> None:
        """Initialize Socket Client.

        Args:
            address: A tuple containing IP adress (str) and port (int).
            service_name: Own service name usd in print.
        """
        self.address = address
        self.service_name = service_name
        logger.info(f'[SocketClient/{self.service_name}/{self.address}] Initializing.')

    def send(
            self,
            data: bytes,
            ) -> None:
        """Send data.

        Aegs:
            data: data to be sent.
        """
        logger.debug(f'[SocketClient/{self.service_name}/{self.address}] Sending {data=}.')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            while True:
                try:
                    s.connect(self.address)
                    s.sendall(data)
                    break
                except socket.error:
                    logger.debug(f'[SocketServer/{self.service_name}/{self.address}] Failed to send {data=}.')
                    time.sleep(1)
        logger.debug(f'[SocketClient/{self.service_name}/{self.address}] Finish sending {data=}.')
