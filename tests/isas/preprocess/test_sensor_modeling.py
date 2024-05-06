import unittest
from pathlib import Path

import pandas as pd
from isas_base.data import DataManager
from isas_base.data.static_data.sensor import Sensor
from isas_base.data.static_data.structural_model import StructuralModelInfo

from isas.preprocess.sensor_modeling import (
    create_sensor, create_sensor_structural_model_connection
)

D_D_CFG_1 = {  # non-locational - directional discrete sensor
    'SETTING_TYPE': 'discrete',
    'LOCATIONAL': False,
    'DIRECTIONAL': True,
    'DIRECTION': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
}
D_D_CFG_2 = {}
L_D_CFG_1 = {  # locational - non-directional discrete sensor
    'SETTING_TYPE': 'discrete',
    'LOCATIONAL': True,
    'DIRECTIONAL': False,
    'LOCATION': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    }
L_D_CFG_2 = {
    'COMPONENT_NAME': 'fe_node',
    'R1': [0, 0, 0],
    'R2': [0, 0, 0],
    'R3': [-1, -1, -1],
    }
L_C_CFG_1 = {  # locational - non-directional continuous sensor
    'SETTING_TYPE': 'continuous',
    'LOCATIONAL': True,
    'DIRECTIONAL': False,
    'LINES': [{
        'LOCATION': [[0, 0, 0], [5, 0, 0], [10, 0, 0]],
        'POINT_NUM': 5
    }, {
        'LOCATION': [[0, 2.5, 0], [5, 2.5, 0], [10, 2.5, 0]],
        'RESOLUTION': 2.5
    }],
    }
L_C_CFG_2 = {
    'COMPONENT_NAME': 'fe_node',
    'R1': 0,
    'R2': 0,
    'R3': -1,
    }
LD_D_CFG_1 = {  # locational - directional discrete sensor
    'SETTING_TYPE': 'discrete',
    'LOCATIONAL': True,
    'DIRECTIONAL': True,
    'LOCATION': [[1, 0, 0], [2, 0, 0], [3, 0, 0]],
    'DIRECTION': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    }
LD_D_CFG_2 = {
    'COMPONENT_NAME': 'fe_elem',
    'R1': 0,
    'R2': 0,
    'R3': [1, -1, 1],
    }
LD_C_CFG_1 = {  # locational - directional continuous sensor
    'LOCATIONAL': True,
    'DIRECTIONAL': True,
    'SETTING_TYPE': 'continuous',
    'LINES': [{
        'LOCATION': [[0, 0, 0], [5, 0, 0], [10, 0, 0]],
        'POINT_NUM': 5
    }, {
        'LOCATION': [[0, 2.5, 0], [5, 2.5, 0], [10, 2.5, 0]],
        'RESOLUTION': 2.5
    }],
    }
LD_C_CFG_2 = {
    'COMPONENT_NAME': 'fe_elem',
    'R1': 0,
    'R2': 0,
    'R3': -1,
    }
STRUCTURAL_MODEL_NAME = 'beam'
DATADRIVE = Path('/root/datadrive')
DATASYSTEM = 'file'


class TestSensorModeling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_manager = DataManager(datadrive=DATADRIVE)
        cls.structural_model = data_manager._import_structural_models(
            STRUCTURAL_MODEL_NAME, data_system=DATASYSTEM
            )[STRUCTURAL_MODEL_NAME]
        cls.cfgs = (
            (D_D_CFG_1, D_D_CFG_2),
            (L_D_CFG_1, L_D_CFG_2),
            (L_C_CFG_1, L_C_CFG_2),
            (LD_D_CFG_1, LD_C_CFG_2),
            )

    def test_create_sensor(self):
        for cfg in self.cfgs:
            sensor = create_sensor(cfg[0])
            self.assertIsInstance(sensor, Sensor)
            for key in ('LOCATIONAL', 'DIRECTIONAL'):
                self.assertEqual(getattr(sensor, key.lower()), cfg[0][key])
            self.assertIsInstance(sensor.data, pd.DataFrame)
            self.assertEqual({}, sensor.structural_model_info)

    def test_sensor_structural_model_connection(self):
        for cfg in self.cfgs:
            sensor = create_sensor(cfg[0])
            sensor = create_sensor_structural_model_connection(
                cfg[1],
                sensor,
                STRUCTURAL_MODEL_NAME, self.structural_model)
            self.assertIsInstance(sensor, Sensor)
            for key in ('LOCATIONAL', 'DIRECTIONAL'):
                self.assertEqual(getattr(sensor, key.lower()), cfg[0][key])
            self.assertIsInstance(sensor.data, pd.DataFrame)
            self.assertIsInstance(sensor.structural_model_info, dict)
            if cfg[0]['LOCATIONAL']:
                self.assertEqual(set(sensor.structural_model_info.keys()), {STRUCTURAL_MODEL_NAME})
                structural_model_info = sensor.structural_model_info[STRUCTURAL_MODEL_NAME]
                self.assertIsInstance(structural_model_info, StructuralModelInfo)
                self.assertIsInstance(structural_model_info.component_name, str)
                self.assertIsInstance(structural_model_info.connection, pd.DataFrame)
            else:
                self.assertEqual({}, sensor.structural_model_info)


if __name__ == '__main__':
    unittest.main()
