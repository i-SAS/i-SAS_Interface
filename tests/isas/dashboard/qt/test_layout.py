import unittest
from pathlib import Path

import yaml
from PySide6 import QtWidgets

from isas.dashboard.qt.layout import Layout

CFG_PATH = Path('tests/cfg/test_dashboard.yml')


class TestLayoutNew(unittest.TestCase):
    def setUp(self):
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def test_new(self):
        Layout.cfg = None
        args = {
            'box': [QtWidgets.QBoxLayout.LeftToRight]
            }
        for layout_type, layout_class in Layout.LAYOUTS.items():
            layout = Layout(layout_type, *args.get(layout_type, []))
            self.assertIsInstance(layout, layout_class)
            self.assertEqual(layout.cfg, None)
            self.assertEqual(layout.isas_subpackages, [])

    def test_new_with_cfg(self):
        Layout.set_cfg(self.cfg['SUBPACKAGES'])
        args = {
            'box': [QtWidgets.QBoxLayout.LeftToRight]
            }
        for layout_type, layout_class in Layout.LAYOUTS.items():
            layout = Layout(layout_type, *args.get(layout_type, []))
            self.assertIsInstance(layout, layout_class)
            self.assertIsInstance(layout.cfg, dict)
            gt_keys = {
                subpackage_cfg['INIT_ARGS']['INSTANCE_NAME']
                for subpackage_cfg in self.cfg['SUBPACKAGES']
                }
            self.assertEqual(set(layout.cfg.keys()), gt_keys)
            self.assertEqual(layout.isas_subpackages, [])


class TestLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Must construct a QApplication before a QWidget
        cls.app = QtWidgets.QApplication.instance()
        if not cls.app:
            cls.app = QtWidgets.QApplication()

    def setUp(self):
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)
        Layout.set_cfg(self.cfg['SUBPACKAGES'])
        self.layout = Layout('vbox')
        self.instance_name = 'visualization_template_dropdowns'

    def test_addSubpackage(self):  # noqa: N802
        self.layout.addSubpackage(self.instance_name)
        self.assertEqual(len(self.layout.isas_subpackages), 1)
        self.assertEqual(self.layout.count(), 1)

    def test_addLayout(self):  # noqa: N802
        layout = Layout('vbox')
        layout.addSubpackage(self.instance_name)
        self.layout.addLayout(layout)
        self.assertEqual(len(self.layout.isas_subpackages), 1)
        self.assertEqual(self.layout.count(), 1)

    def test_addWidget(self):  # noqa: N802
        layout = Layout('vbox')
        layout.addSubpackage(self.instance_name)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setLayout(layout)
        self.layout.addWidget(scroll_area)
        self.assertEqual(len(self.layout.isas_subpackages), 1)
        self.assertEqual(self.layout.count(), 1)


if __name__ == '__main__':
    unittest.main()
