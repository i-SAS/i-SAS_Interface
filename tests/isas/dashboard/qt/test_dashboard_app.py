import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from isas_base.data import DataManager
from isas_base.subpackage.base.base import Base as BaseSubpackage
from PySide6 import QtWidgets

from isas.dashboard.qt.dashboard_app import DashboardApp

SERVICE_NAME = 'test'
DATADRIVE = Path('/root/datadrive_tmp')
CFG_PATH = Path('tests/cfg/test_dashboard.yml')
TEST_MANUALLY = False


class TestDashboardAppInit(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)
        self.data_manager = DataManager(
            datadrive=self.cfg['SERVICE']['DATADRIVE'],
            )
        self.streaming = False

    def tearDown(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def test_init(self):
        dashboard_app = DashboardApp(
            self.cfg,
            self.data_manager,
            SERVICE_NAME,
            self.streaming,
            )
        self.assertIsInstance(dashboard_app.main_layout, QtWidgets.QLayout)
        self.assertEqual(dashboard_app.tab_names, ['tab_name'])
        self.assertEqual(dashboard_app.current_tab_name, 'tab_name')
        self.assertEqual(set(dashboard_app.subpackages.keys()), {'tab_name'})
        for subpackage in dashboard_app.subpackages['tab_name']:
            self.assertIsInstance(subpackage, BaseSubpackage)
        self.assertEqual(dashboard_app.import_data_names, {'tab_name': []})


class TestDashboardApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Must construct a QApplication before a QWidget
        cls.app = QtWidgets.QApplication.instance()
        if not cls.app:
            cls.app = QtWidgets.QApplication()

    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)
        data_manager = DataManager(
            datadrive=self.cfg['SERVICE']['DATADRIVE'],
            )
        self.dashboard_app = DashboardApp(
            self.cfg,
            data_manager,
            SERVICE_NAME,
            False,
            )

    def tearDown(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def test_update(self):
        timestamp_1 = self.dashboard_app.timestamp.text()
        self.dashboard_app._update()
        timestamp_2 = self.dashboard_app.timestamp.text()
        self.assertNotEqual(timestamp_1, timestamp_2)

    def test_start(self):
        if TEST_MANUALLY:
            self.dashboard_app.start()
        else:
            def _quit_app(self):
                self.app.quit()
            with patch.object(DashboardApp, '_update', _quit_app):
                self.dashboard_app.start()


if __name__ == '__main__':
    unittest.main()
