import queue
import unittest

from isas.service import SocketClient, SocketServer


class TestSocketServerAndClient(unittest.TestCase):
    def setUp(self):
        self.recv_queue = queue.Queue()
        self.server = SocketServer(('', 80), self.recv_queue)

    def tearDown(self):
        if self.server.is_alive():
            self.server.stop()

    def test_connect(self):
        client = SocketClient(('localhost', 80))
        self.server.start()
        data = b'test'
        client.send(data)
        recv_data = self.recv_queue.get()
        self.assertEqual(data, recv_data)


if __name__ == '__main__':
    unittest.main()
