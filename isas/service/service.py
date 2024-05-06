import logging
import os
import queue
import threading
from pathlib import Path

import yaml

from ..dashboard import Dashboard
from ..interface import Interface
from .socket import SocketClient, SocketServer

logger = logging.getLogger(__name__)


class Service:
    """Service class."""

    def __init__(
            self,
            cfg: str | Path | dict,
            ) -> None:
        """Intitialize Service class.

        Args:
            cfg: A config of the project.
        """
        self.service_name = os.environ['SERVICE_NAME']
        self.cfg = self._get_cfg(cfg)
        logger.info(f'[Service/{self.service_name}] Initializing with args: {self.cfg=}')
        # set socket clients and servers
        self.recv_queue = queue.Queue()
        ports = {
            s.split(':')[0]: int(s.split(':')[1])
            for s in os.environ['PORT'].split(';')
            }
        self.socket_clients = self._get_socket_clients(ports)
        self.socket_server = self._get_socket_server(ports)
        self.socket_server.start()

    def _get_cfg(
            self,
            cfg: str | Path | dict,
            ) -> dict:
        """Get config

        Args:
            cfg: A path to the config of the project.

        Returns:
            A config of the project.
        """
        if isinstance(cfg, (str, Path)):
            with Path(cfg).open('r') as f:
                cfg = yaml.safe_load(f)
        return cfg

    def _get_socket_clients(
            self,
            ports: dict,
            ) -> dict:
        """Create socket clients dict.

        Args:
            ports: A dict whose the key is service_name and the value is port number.

        Returns:
            A dict whose the key is service_name and the value is SocketClient instance.
        """
        socket_clients = {}
        for service_name, port in ports.items():
            if service_name == self.service_name:
                continue
            socket_clients[service_name] = SocketClient((service_name, port), self.service_name)
        return socket_clients

    def _get_socket_server(
            self,
            ports: dict,
            ) -> dict:
        """Create socket server dict.

        Args:
            ports: A dict whose the key is service_name and the value is port number.

        Returns:
            A dict whose the key is service_name and the value is SocketServer instance.
        """
        port = ports[self.service_name]
        socket_server = SocketServer(('', port), self.recv_queue, self.service_name)
        return socket_server

    def __call__(self) -> None:
        """Run service."""
        logger.info(f'[Service/{self.service_name}] Running service.')
        self._wait_dependencies()
        logger.debug(f'[Service/{self.service_name}] Launch {self.cfg["SERVICE_TYPE"]}.')
        if self.cfg['SERVICE_TYPE'] == 'Interface':
            self._run_interface()
        elif self.cfg['SERVICE_TYPE'] == 'Dashboard':
            self._run_dashboard()
        else:
            raise ValueError(f'Unsupported service type {self.cfg["SERVICE_TYPE"]}.')
        self.exit()

    def _run_dashboard(self) -> None:
        """Run dashboard."""
        dashboard = Dashboard(cfg=self.cfg)
        self._send_message(self.service_name)
        dashboard()
        logger.debug(f'[Service/{self.service_name}] Exit.')
        self._send_message('exit')

    def _run_interface(self) -> None:
        """Run interface with threading."""
        interface = Interface(cfg=self.cfg)
        self._send_message(self.service_name)
        thread = InterfaceThread(interface)
        thread.start()
        while True:
            logger.debug(f'[Service/{self.service_name}] Waiting message.')
            message = self.recv_queue.get().decode()
            logger.debug(f'[Service/{self.service_name}] Recieve {message=}')
            if message == 'exit':
                logger.debug(f'[Service/{self.service_name}] Exit.')
                thread.stop()
                return
            else:
                logger.warning(f'[Service/{self.service_name}] Unsupported message: {message}')

    def _wait_dependencies(self) -> None:
        """Wait dependencies."""
        finished_init = []
        if not len(self.cfg['DEPENDENCIES']):
            return
        while True:
            logger.debug(f'[Service/{self.service_name}] Waiting dependencies.')
            message = self.recv_queue.get().decode()
            logger.debug(f'[Service/{self.service_name}] Recieve {message=}')
            finished_init.append(message)
            if set(finished_init) >= set(self.cfg['DEPENDENCIES']):
                return

    def _send_message(
            self,
            message: str
            ) -> None:
        """Send message to other services.

        Args:
            message: A message to be sent other services.
        """
        logger.debug(f'[Service/{self.service_name}] Send {message=}')
        for socket_client in self.socket_clients.values():
            socket_client.send(message.encode())

    def exit(self) -> None:
        """Exit service"""
        if self.socket_server.is_alive():
            self.socket_server.stop()


class InterfaceThread(threading.Thread):
    def __init__(
            self,
            isas: Interface,
            ) -> None:
        logger.info('[InterfaceThread] Initializing.')
        super().__init__()
        self.isas = isas
        self.stop_event = threading.Event()
        self.deamon = True

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        logger.info('[InterfaceThread] Running.')
        while not self.stop_event.is_set():
            self.isas()
        logger.info('[InterfaceThread] Stop.')
        self.isas.exit()
