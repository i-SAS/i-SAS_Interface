import unittest
from pathlib import Path

import yaml
from isas_base.data import StaticData
from isas_base.data.static_data.sensor import Sensor
from isas_base.data.static_data.structural_model import StructuralModel

from isas.preprocess import create_static_data

CFG_PATH = Path('tests/cfg/test_preprocess.yml')
SENSOR_NAME = 'test_sensor'
STRUCTURAL_MODEL_NAME = 'test_model'


class TestCreateStaticData(unittest.TestCase):
    def setUp(self):
        with CFG_PATH.open('r') as f:
            self.cfg = yaml.safe_load(f)

    def test_create_static_data(self):
        static_data = create_static_data(self.cfg)
        self.assertIsInstance(static_data, StaticData)
        self.assertEqual(set(static_data.sensors.keys()), {SENSOR_NAME})
        self.assertIsInstance(static_data.sensors[SENSOR_NAME], Sensor)
        self.assertEqual(set(static_data.structural_models.keys()), {STRUCTURAL_MODEL_NAME})
        self.assertIsInstance(static_data.structural_models[STRUCTURAL_MODEL_NAME], StructuralModel)


if __name__ == '__main__':
    unittest.main()
