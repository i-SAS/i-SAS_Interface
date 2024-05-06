import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from isas_base.data import DataManager
from isas_base.data.static_data.structural_model import (
    FiniteElementModel, GraphModel, PointCloud
)

from isas.preprocess.structural_modeling import (
    convert_finite_element_model, convert_graph_model, convert_point_cloud,
    create_finite_element_model, import_finite_element_model
)

CREATE_PLATE_CFG = {
    'GEOMETRY_TYPE': 'PLATE',
    'WIDTH': 100,
    'HEIGHT': 100,
    'THICKNESS': 1,
    'WIDTH_DIVIDE_NUM': 10,
    'HEIGHT_DIVIDE_NUM': 10,
    'YOUNGS_MODULUS': 70e+3,
    'POISSONS_RATIO': 0.3,
    'R3': 0,
    'ELEM_TYPE': 'iQS4',
    'NODE_NUM': 4,
    'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
        123456: {1: 0, 2: 0, 3: 0},
    },
}
CREATE_CUSTOM_PLATE_CFG = {
    'GEOMETRY_TYPE': 'CUSTOM_PLATE',
    'X_ARRAY': np.linspace(0, 1, 10),
    'Y_ARRAY': np.linspace(0, 1, 10),
    'THICKNESS': 1,
    'YOUNGS_MODULUS': 70e+3,
    'POISSONS_RATIO': 0.3,
    'R3': 0,
    'ELEM_TYPE': 'iQS4',
    'NODE_NUM': 4,
    'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
        123456: {1: 0, 2: 0, 3: 0},
    },
}
CREATE_CUBOID_CFG = {
    'GEOMETRY_TYPE': 'CUBOID',
    'WIDTH': 100,
    'DEPTH': 100,
    'HEIGHT': 100,
    'WIDTH_DIVIDE_NUM': 10,
    'DEPTH_DIVIDE_NUM': 10,
    'HEIGHT_DIVIDE_NUM': 10,
    'YOUNGS_MODULUS': 70e+3,
    'POISSONS_RATIO': 0.3,
    'R3': 0,
    'ELEM_TYPE': 'solid',
    'NODE_NUM': 8,
    'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
        123456: {1: 0, 2: 0, 3: 0},
    },
}
CREATE_PIPE_CFG = {
    'GEOMETRY_TYPE': 'PIPE',
    'LONGITUDINAL_LENGTH': 100,
    'PIPE_RADIUS': 10,
    'THICKNESS': 1,
    'LONGITUDINAL_DIVIDE_NUM': 10,
    'CROSS_SECTION_DIVIDE_NUM': 10,
    'YOUNGS_MODULUS': 70e+3,
    'POISSONS_RATIO': 0.3,
    'R3': 0,
    'ELEM_TYPE': 'iQS4',
    'NODE_NUM': 4,
    'CROSS_SECTION_SHAPE': 'circle',  # ('circle', 'rectangle')
    'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
        123456: {1: 0, 2: 0, 3: 0},
    },
}
STRUCTURAL_MODEL_NAME = 'beam'
IMPORT_FE_CFG = {
    'FILE_PATH': f'/root/datadrive/external_data/{STRUCTURAL_MODEL_NAME}.nas',
    'DATA_FORMAT': 'nastran'
}
DATADRIVE = Path('/root/datadrive')
DATASYSTEM = 'file'


class TestStructuralModeling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_manager = DataManager(datadrive=DATADRIVE)
        cls.structural_model = data_manager._import_structural_models(
            STRUCTURAL_MODEL_NAME, data_system=DATASYSTEM
            )[STRUCTURAL_MODEL_NAME]
        cls.cfgs = (CREATE_PLATE_CFG, CREATE_CUSTOM_PLATE_CFG, CREATE_CUBOID_CFG, CREATE_PIPE_CFG)

    def test_create_finite_element_model(self):
        for cfg in self.cfgs:
            model = create_finite_element_model(cfg)
            self.assertIsInstance(model, FiniteElementModel)
            self.assertEqual(model.MODEL_TYPE, 'fe')
            for key in model.COMPONENT_NAMES:
                self.assertIsInstance(getattr(model, key), pd.DataFrame)

    def test_create_graph_model(self):
        pass

    def test_create_poind_cloud_model(self):
        pass

    def test_convert_finite_element_model(self):
        model = create_finite_element_model(CREATE_PLATE_CFG)
        model_types = {
            'fe': FiniteElementModel,
            'graph': GraphModel,
            'point_cloud': PointCloud,
            }
        for _model_type, _class in model_types.items():
            _cfg = {'MODEL_TYPE': _model_type}
            converted_model = convert_finite_element_model(_cfg, model)
            self.assertIsInstance(converted_model, _class)
            self.assertEqual(converted_model.MODEL_TYPE, _model_type)
            for key in model.COMPONENT_NAMES:
                self.assertIsInstance(getattr(model, key), pd.DataFrame)

    def test_convert_graph_model(self):
        model = create_finite_element_model(CREATE_PLATE_CFG)
        model = convert_finite_element_model({'MODEL_TYPE': 'graph'}, model)
        model_types = {
            'graph': GraphModel,
            'point_cloud': PointCloud,
            }
        for _model_type, _class in model_types.items():
            _cfg = {'MODEL_TYPE': _model_type}
            converted_model = convert_graph_model(_cfg, model)
            self.assertIsInstance(converted_model, _class)
            self.assertEqual(converted_model.MODEL_TYPE, _model_type)
            for key in model.COMPONENT_NAMES:
                self.assertIsInstance(getattr(model, key), pd.DataFrame)

    def test_convert_point_cloud(self):
        model = create_finite_element_model(CREATE_PLATE_CFG)
        model = convert_finite_element_model({'MODEL_TYPE': 'point_cloud'}, model)
        model_types = {
            'point_cloud': PointCloud,
            }
        for _model_type, _class in model_types.items():
            _cfg = {'MODEL_TYPE': _model_type}
            converted_model = convert_point_cloud(_cfg, model)
            self.assertIsInstance(converted_model, _class)
            self.assertEqual(converted_model.MODEL_TYPE, _model_type)
            for key in model.COMPONENT_NAMES:
                self.assertIsInstance(getattr(model, key), pd.DataFrame)

    def test_import_finite_element_model(self):
        # nastran
        model = import_finite_element_model(IMPORT_FE_CFG)
        self.assertIsInstance(model, FiniteElementModel)
        self.assertEqual(model.MODEL_TYPE, 'fe')
        for key in model.COMPONENT_NAMES:
            self.assertIsInstance(getattr(model, key), pd.DataFrame)

    def test_import_graph_model(self):
        pass

    def test_import_poind_cloud_model(self):
        pass


if __name__ == '__main__':
    unittest.main()
