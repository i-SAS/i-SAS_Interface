import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from isas import Dashboard
from isas.dashboard.qt.dashboard_app import DashboardApp

DATADRIVE = Path('/root/datadrive_tmp')
CFG_PATH = Path('tests/cfg/test_dashboard.yml')
TEST_MANUALLY = False


class TestDashboardInit(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def tearDown(self):
        if hasattr(self, 'dashboard'):
            self.dashboard.exit()
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def test_attributes(self):
        self.dashboard = Dashboard(self.cfg)
        self.assertIsInstance(self.dashboard.dashboard_app, DashboardApp)


class TestDashboardCall(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def tearDown(self):
        self.dashboard.exit()
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def test_call(self):
        self.dashboard = Dashboard(self.cfg)
        if TEST_MANUALLY:
            self.dashboard()
        else:
            def _quit_app(self):
                self.app.quit()
            with patch.object(DashboardApp, '_update', _quit_app):
                self.dashboard()


if __name__ == '__main__':
    unittest.main()
