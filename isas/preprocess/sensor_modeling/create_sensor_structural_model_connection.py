import numpy as np
import pandas as pd
from isas_base.data.static_data.sensor import Sensor
from isas_base.data.static_data.structural_model import (
    StructuralModel, StructuralModelInfo
)
from isas_base.utils import get_cfg

from ..utils import calc_fe_elem_center


def create_sensor_structural_model_connection(
        cfg: dict,
        sensor: Sensor,
        structural_model_name: str,
        structural_model: StructuralModel,
        ) -> Sensor:
    """Create sensor structural model connection.

    Args:
        cfg: Sensor structural model connection config.
        sensor: Sensor data without connection data.
        structural_model_name (str): A target structural model name.
        structural_model (dict): Structural model data.

    Returns:
        Sensor data with connection data.
    """
    modeler = SensorStructuralModelConnectionModeler(cfg, sensor)
    return modeler(structural_model_name, structural_model)


class SensorStructuralModelConnectionModeler:
    DEFAULT_CFG = {
        'OVERWRITE': True,
        'COMPONENT_NAME': None,  # point_cloud, fe_node, fe_elem, graph_node
        'R1': None,  # To set a single value for the whole, use a float; to set individual values, use a list.
        'R2': None,
        'R3': None,
        }
    LOCATIONAL_COLUMN_NAMES = ('x', 'y', 'z')
    DIRECTIONAL_COLUMN_NAMES = ('direction_x', 'direction_y', 'direction_z')
    COMPONENT_KEYS = {
        'fe_node': 'fe_node_id',
        'fe_elem': 'fe_elem_id',
        'graph_node': 'graph_node_id',
        'point_cloud': 'point_id',
        }

    def __init__(
            self,
            cfg: dict,
            sensor: Sensor,
            ) -> None:
        """Initialize SensorStructuralModelConnectionModeler

        Args:
            cfg: Sensor structural model connection config.
            sensor: Sensor data without connection data.
        """
        if sensor.locational:
            cfg = get_cfg(cfg, self.DEFAULT_CFG)
            self._check_cfg(cfg, sensor)
        self.cfg = cfg
        self.sensor = sensor

    def _check_cfg(
            self,
            cfg: dict,
            sensor: Sensor,
            ) -> None:
        """Check config.

        Args:
            cfg: Sensor structural model connection config.
            sensor: Sensor data without connection data.
        """
        if sensor.data is None:
            raise ValueError('Sensor data does not exist in inputted sensor.')
        required_keys = ('COMPONENT_NAME', 'R1', 'R2', 'R3')
        exist_keys = [key for key in required_keys if key in cfg]
        if set(required_keys) != set(exist_keys):
            raise ValueError(f'{set(required_keys) - set(exist_keys)} is requared for cfg key.')

    def __call__(
            self,
            structural_model_name: str,
            structural_model: StructuralModel,
            ) -> Sensor:
        """Create sensor structural model connection.

        Args:
            structural_model_name (str): A target structural model name.
            structural_model (dict): Structural model data.

        Returns:
            Sensor data with connection data.
        """
        if not self.sensor.locational:
            return self.sensor
        if not self.cfg.get('OVERWRITE', self.DEFAULT_CFG['OVERWRITE']) \
                and structural_model_name in self.sensor.structural_model_info:
            raise ValueError(
                'Target connection is already exist in sensor. To overwrite, set "OVERWRITE" to True in cfg.')

        # Arrange R coordinate.
        r_coord = self._arrange_r_coord()
        self.sensor.structural_model_info[structural_model_name] = StructuralModelInfo(
            **self._create_metadata(),
            **self._create_connection(
                structural_model,
                r_coord,
                ),
            )
        return self.sensor

    def _arrange_r_coord(self) -> dict:
        """Arrange r coordinate in cfg.

        Returns:
            A dict contains the information of r coordinate for metadata and connection.
        """
        r_coord = dict()
        r_keys = ('R1', 'R2', 'R3')
        for key in r_keys:
            cfg = self.cfg[key]
            if hasattr(cfg, '__iter__'):  # list, tuple...
                if len(cfg) != len(self.sensor.data):
                    raise ValueError(f'The length of inputted "{key}" in cfg does not match the number of sensors.')
                connection = list([float(_) for _ in cfg])
            elif isinstance(cfg, (int, float)):
                connection = list([float(cfg) for _ in range(len(self.sensor.data))])
            else:
                raise ValueError(f'Unsupported r values in cfg. {key}: {cfg}')
            r_coord[f'connection_{key.lower()}'] = connection
        return r_coord

    def _create_metadata(self) -> dict:
        """Create sensor metadata.

        Returns:
            A dict contains sensor metadata.
        """
        return {
            'component_name': self.cfg['COMPONENT_NAME'],
            }

    def _create_connection(
            self,
            structural_model: StructuralModel,
            r_coord: dict,
            ) -> dict:
        """Create sensor structural model connection.

        Args:
            structural_model: A dict contains structural model data.
            r_coord: Curvilinear coordinates of sensors

        Returns:
            A dict of dataframe contains connections between sensor_id and structural model's id (e.g. fe_node_id).
        """
        component_key = self.COMPONENT_KEYS[self.cfg['COMPONENT_NAME']]
        # sensor locations
        locations = self.sensor.data.loc[:, self.LOCATIONAL_COLUMN_NAMES].to_numpy(dtype=float)
        # model locations
        df = getattr(structural_model, self.cfg['COMPONENT_NAME'])
        if self.cfg['COMPONENT_NAME'] == 'fe_elem':
            sm_point_id, sm_points = calc_fe_elem_center(
                structural_model.fe_node,
                df,
                structural_model.fe_connection,
                )
        else:  # point_cloud, fe_node, graph_node
            sm_points = df.loc[:, self.LOCATIONAL_COLUMN_NAMES].to_numpy(dtype=float)
            sm_point_id = df.index.to_numpy(dtype=int)
        sm_id = self._get_nearest_point_id(locations, sm_points, sm_point_id)
        sensor_id = np.arange(len(locations)) + 1
        connection = {
            'sensor_id': sensor_id,
            component_key: sm_id,
            **{
                key: r_coord[f'connection_{key}']
                for key in ('r1', 'r2', 'r3')
                }
            }
        connection = pd.DataFrame(connection).set_index('sensor_id')
        return {'connection': connection}

    @staticmethod
    def _get_nearest_point_id(
            tgt_points: np.ndarray,
            ref_points: np.ndarray,
            ref_id: np.ndarray,
            ) -> np.ndarray:
        """Get nearest point id.

        Args:
            tgt_points: Target points.
            ref_points: Reference points.
            ref_id: ID of reference points.

        Returns:
            ID of nearest reference points.
        """
        tgt_points = tgt_points.reshape(tgt_points.shape[0], 1, tgt_points.shape[1])
        ref_points = ref_points.reshape(1, ref_points.shape[0], ref_points.shape[1])
        distance_matrix = np.linalg.norm(tgt_points - ref_points, axis=2)
        min_index = distance_matrix.argmin(axis=1)
        return ref_id[min_index]
