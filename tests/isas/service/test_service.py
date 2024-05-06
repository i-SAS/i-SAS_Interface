import os
import queue
import unittest
from pathlib import Path

import yaml

from isas.service import Service, SocketClient, SocketServer

CFG_PATH = Path('tests/cfg/test_project.yml')


class TestService(unittest.TestCase):
    def setUp(self):
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)
        self.service_names = {'test_interface', 'test_dashboard'}
        os.environ['PORT'] = 'test_interface:50001;test_dashboard:50002'

    def tearDown(self):
        self.service.exit()
        del os.environ['PORT']
        del os.environ['SERVICE_NAME']

    def test_interface_init(self):
        self._test_init('test_interface')

    def test_dashboard_init(self):
        self._test_init('test_dashboard')

    def _test_init(self, service_name):
        os.environ['SERVICE_NAME'] = service_name
        cfg = self.cfg['SERVICES'][service_name]
        self.service = Service(cfg)
        self.assertEqual(self.service.cfg, cfg)
        self.assertEqual(self.service.service_name, service_name)
        self.assertIsInstance(self.service.recv_queue, queue.Queue)
        self.assertIsInstance(self.service.socket_clients, dict)
        self.assertEqual(set(self.service.socket_clients.keys()), self.service_names - {service_name})
        for v in self.service.socket_clients.values():
            self.assertIsInstance(v, SocketClient)
        self.assertIsInstance(self.service.socket_server, SocketServer)


if __name__ == '__main__':
    unittest.main()
