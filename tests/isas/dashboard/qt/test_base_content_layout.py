import unittest

from isas.dashboard.qt.layout import Layout

from ....dashboard.content_layout import ContentLayout


class TestBaseContentLayout(unittest.TestCase):
    def setUp(self):
        self.cfg = {}

    def test_init(self):
        ContentLayout(self.cfg)
        self.assertEqual(Layout.cfg, self.cfg)

    def test_call(self):
        content_layout = ContentLayout(self.cfg)
        res = content_layout()
        self.assertIsInstance(res, dict)
        for k, v in res.items():
            self.assertIsInstance(k, str)
            self.assertTrue(callable(v))


if __name__ == '__main__':
    unittest.main()
