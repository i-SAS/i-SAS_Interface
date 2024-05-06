import shutil
import unittest
from copy import deepcopy
from pathlib import Path

import yaml
from isas_base.data import DynamicData, StaticData
from isas_base.subpackage.base.base import Base as BaseSubpackage

from isas import Interface

DATADRIVE = Path('/root/datadrive_tmp')
CFG_PATH = Path('tests/cfg/test_interface.yml')
SENSOR_NAME = 'rosette'
STRUCTURAL_MODEL_NAME = 'beam'
PARAMS = {'TEST_KEY_1': {'TEST_KEY_1_2': 1.2}}

ANALYSIS_INPUT_DATA_NAMES = ['measured_rosette_strain_x']
ANALYSIS_INPUT_DATA_NAME_DICT = {'input_quantity': ANALYSIS_INPUT_DATA_NAMES}
ANALYSIS_OUTPUT_DATA_NAMES = ['analyzed_rosette_strain_x']
ANALYSIS_OUTPUT_DATA_NAME_DICT = {'output_quantity': ANALYSIS_OUTPUT_DATA_NAMES}

MEASUREMENT_INPUT_DATA_NAMES = ['rosette_strain_x']
MEASUREMENT_OUTPUT_DATA_NAMES = ['measured_rosette_strain_x']


class TestInterfaceInit(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def tearDown(self):
        if hasattr(self, 'interface'):
            self.interface.exit()
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def test_attributes(self):
        self.interface = Interface()
        self.assertIsInstance(self.interface.static_data, StaticData)
        self.assertEqual(self.interface.models, {})
        self.assertEqual(self.interface.import_data_names, {})
        self.assertEqual(self.interface.export_data_names, [])
        self.assertIsNone(self.interface.last_datetime)
        self.assertEqual(self.interface.cfg, self.interface.DEFAULT_CFG)

    def test_set_up_batch(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'batch'
        self._test_setup_from_config(cfg, False)

    def test_set_up_stream(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'stream'
        self._test_setup_from_config(cfg, True)

    def test_set_up_simulate_stream(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'simulate_stream'
        self._test_setup_from_config(cfg, True)

    def _test_setup_from_config(self, cfg, streaming):
        self.interface = Interface(cfg)
        self.assertEqual(self.interface.cfg, cfg['SERVICE'])
        self.assertEqual(self.interface.streaming, streaming)

        self.assertIsInstance(self.interface.models, dict)
        gt_tasks = {'analysis', 'measurement'}
        self.assertEqual(set(self.interface.models), gt_tasks)
        for task, model_list in self.interface.models.items():
            self.assertIsInstance(model_list, list)
            for model in model_list:
                self.assertIsInstance(model, BaseSubpackage)
                self.assertEqual(model.TASK, task)


class TestInterfaceCall(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(DATADRIVE, ignore_errors=True)
        shutil.copytree('/root/datadrive', DATADRIVE)
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def tearDown(self):
        self.interface.exit()
        shutil.rmtree(DATADRIVE, ignore_errors=True)

    def _test_results(self):
        dynamic_data = self.interface()
        self.assertIsInstance(dynamic_data, DynamicData)
        input_data_names = MEASUREMENT_INPUT_DATA_NAMES + ANALYSIS_INPUT_DATA_NAMES
        output_data_names = MEASUREMENT_OUTPUT_DATA_NAMES + ANALYSIS_OUTPUT_DATA_NAMES
        gt_keys = set(input_data_names + output_data_names)
        self.assertEqual(set(dynamic_data.time_series_data.keys()), gt_keys)
        self.assertEqual(len(dynamic_data.time_series_batch_metadata), 1)

    def test_call_simulation(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'batch'
        cfg['SUBPACKAGES'][0]['INIT_ARGS']['SIMULATION'] = True
        self.interface = Interface(cfg)
        self._test_results()

    def test_call_simulation_streaming(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'simulate_stream'
        cfg['SUBPACKAGES'][0]['INIT_ARGS']['SIMULATION'] = True
        self.interface = Interface(cfg)
        self._test_results()

    def test_call_experiment(self):
        cfg = deepcopy(self.cfg)
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'batch'
        cfg['SUBPACKAGES'][0]['INIT_ARGS']['SIMULATION'] = False
        self.interface = Interface(cfg)
        self._test_results()

    def test_call_experiment_streaming(self):
        cfg = self.cfg.copy()
        cfg['SERVICE']['DATA_PROCESSING_METHOD'] = 'stream'
        cfg['SUBPACKAGES'][0]['INIT_ARGS']['SIMULATION'] = False
        self.interface = Interface(cfg)
        self._test_results()


if __name__ == '__main__':
    unittest.main()
