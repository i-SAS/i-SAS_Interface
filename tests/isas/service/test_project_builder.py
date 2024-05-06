import shutil
import unittest
import warnings
from pathlib import Path

import yaml

from isas.service import ProjectBuilder

PROJECT_DIR = Path('/root/workspace/tests/project_tmp')
CFG_PATH = Path('tests/cfg/test_project.yml')


class TestProjectBuilder(unittest.TestCase):
    def setUp(self):
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)
        shutil.rmtree(PROJECT_DIR, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(PROJECT_DIR, ignore_errors=True)

    def test_init(self):
        builder = ProjectBuilder(self.cfg, PROJECT_DIR)
        self.assertEqual(builder.cfg, self.cfg)
        self.assertEqual(builder.project_dir, PROJECT_DIR)
        self.assertTrue(PROJECT_DIR.exists())

    def test_call(self):
        builder = ProjectBuilder(self.cfg, PROJECT_DIR)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            builder()
        for k in ('.env', 'docker-compose.yml', 'test_interface', 'test_dashboard'):
            self.assertTrue((PROJECT_DIR / k).exists())
        for service_name in ('test_interface', 'test_dashboard'):
            service_dir = PROJECT_DIR / service_name
            self.assertTrue((service_dir / 'cfg').exists())
            with (service_dir / 'cfg/service.yml').open('r') as f:
                cfg = yaml.safe_load(f)
            self.assertEqual(cfg, self.cfg['SERVICES'][service_name])


if __name__ == '__main__':
    unittest.main()
