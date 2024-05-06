from collections import defaultdict

import numpy as np
import pandas as pd
from isas_base.data.static_data.sensor import Sensor
from isas_base.utils import get_cfg
from scipy.interpolate import interp1d


def create_sensor(
        cfg: dict,
        ) -> Sensor:
    """Create sensor model.

    Args:
        cfg: Sensor config.

    Returns:
        Sensor data.
    """
    modeler = SensorModeler(cfg)
    return modeler()


class SensorModeler:
    DEFAULT_CFG = {
        'SETTING_TYPE': None,  # 'discrete' or 'continuous'
        'LOCATIONAL': None,
        'DIRECTIONAL': None,
        'DIRECTION': [],
        'LOCATION': [],
        'LINES': [{
            'LOCATION': [],
            'POINT_NUM': 10,
            'RESOLUTION': 1
        }]
    }
    SETTING_TYPES = {'discrete', 'continuous'}
    LOCATIONAL_COLUMN_NAMES = ('x', 'y', 'z')
    DIRECTIONAL_COLUMN_NAMES = ('direction_x', 'direction_y', 'direction_z')

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize SensorModeler.

        Args:
            cfg: Sensor config.
        """
        cfg = get_cfg(cfg, self.DEFAULT_CFG)
        self._check_cfg(cfg)
        self.cfg = cfg

    def _check_cfg(
            self,
            cfg: dict,
            ) -> None:
        """Check config.

        Args:
            cfg: Sensor config.
        """
        if set(cfg.keys()) < set(self.DEFAULT_CFG.keys()):
            raise ValueError('Invalud keys in the config.')
        if cfg['SETTING_TYPE'] not in self.SETTING_TYPES:
            raise ValueError(f'Unsupported sentting type. Supporting: {self.SETTING_TYPES}.')
        for k in ('LOCATIONAL', 'DIRECTIONAL'):
            if not isinstance(cfg[k], bool):
                raise ValueError(f'Unsupported {k} type {cfg[k]}.')

        # non-locational and non-directional
        if not cfg['LOCATIONAL'] and not cfg['DIRECTIONAL']:
            return

        # discrete
        if cfg['SETTING_TYPE'] == 'discrete':
            if len(set(cfg.keys()) & {'LOCATION', 'DIRECTION'}) == 0:
                raise ValueError('Invalid discrete sensor setting.')
            # locational
            if cfg['LOCATIONAL'] and 'LOCATION' not in cfg.keys():
                raise ValueError('Invalid discrete sensor setting for locational sensor.')
            # directional
            if cfg['DIRECTIONAL'] and 'DIRECTION' not in cfg.keys():
                raise ValueError('Invalid discrete sensor setting for directional sensor.')

        # continuous
        elif cfg['SETTING_TYPE'] == 'continuous':
            if not cfg['LOCATIONAL']:
                raise ValueError('Continuous sensor setting is required for locational sensor.')
            if 'LINES' not in cfg:
                raise ValueError('Invalid continuous sensor setting.')
            for line in cfg['LINES']:
                if not set(line.keys()) <= {'LOCATION', 'RESOLUTION', 'POINT_NUM'}:
                    raise ValueError('Invalid continuous sensor setting.')
                if (not ('RESOLUTION' in line.keys()) ^ ('POINT_NUM' in line.keys())) or 'LOCATION' not in line.keys():
                    raise ValueError('Invalid continuous sensor setting for locational sensor.')

    def __call__(self) -> Sensor:
        """Create Sensor.

        Returns:
            An instance of Sensor.
        """
        return Sensor(
            **self._create_metadata(),
            **self._create_sensor(),
            **{'structural_model_info': {}},
            )

    def _create_metadata(self) -> dict:
        """Create sensor metadata.

        Returns:
            Sensor metadata
        """
        return {key.lower(): self.cfg[key] for key in {'LOCATIONAL', 'DIRECTIONAL'}}

    def _create_sensor(self) -> dict:
        """Create sensor location and direction.

        Returns:
            Sensor location and direction data.
        """
        # location
        location = None
        if self.cfg['LOCATIONAL']:
            location = self._get_location()
        # directional
        direction = None
        if self.cfg['DIRECTIONAL']:
            direction = self._get_direction(location)

        sensor = self._integrate_sensor(location, direction)
        return {'data': sensor}

    def _get_location(self) -> list[dict]:
        """Get sensor location.

        Returns:
            Location of the sensor.
                x: x coordinates in global coordinate system.
                y: y coordinates in global coordinate system.
                z: z coordinates in global coordinate system.
        """
        if self.cfg['SETTING_TYPE'] == 'discrete':
            location_setting = [self.cfg['LOCATION']]
        elif self.cfg['SETTING_TYPE'] == 'continuous':
            location_setting = []
            for line in self.cfg['LINES']:
                loc = np.asarray(line['LOCATION']).T
                arc_len = np.hstack([0, np.cumsum(np.linalg.norm(np.diff(loc, axis=1), axis=0))])
                f = interp1d(arc_len, loc)
                if 'POINT_NUM' in line.keys():
                    s = np.linspace(0, arc_len[-1], line['POINT_NUM'])
                elif 'RESOLUTION' in line.keys():
                    s = np.arange(0, arc_len[-1] + 10**(-12), line['RESOLUTION'])
                location_setting.append(f(s).T.tolist())
        # location
        location = []
        for _location_setting in location_setting:
            _location = dict()
            for i, k in enumerate(self.LOCATIONAL_COLUMN_NAMES):
                _location[k] = [loc[i] for loc in _location_setting]
            location.append(_location)
        return location

    def _get_direction(
            self,
            location: list[dict]
            ) -> list[dict]:
        """Get sensor direction.

        Args:
            cfg: Sensor config.
            location (list[dict]): Location of the sensor.
                x: x coordinates in global coordinate system.
                y: y coordinates in global coordinate system.
                z: z coordinates in global coordinate system.

        Returns:
            list[dict]: Direction of the sensor.
                direction_x: x components of direction unit vector in global coordinate system.
                direction_y: y components of direction unit vector in global coordinate system.
                direction_z: z components of direction unit vector in global coordinate system.
        """
        if self.cfg['SETTING_TYPE'] == 'discrete':
            direction_setting = [self.cfg['DIRECTION']]
        elif self.cfg['SETTING_TYPE'] == 'continuous':
            direction_setting = []
            for _location in location:
                _location = np.asarray([_location[k] for k in self.LOCATIONAL_COLUMN_NAMES]).T
                vec = np.diff(_location, axis=0)
                vec = (vec/np.linalg.norm(vec, axis=1, keepdims=True)).tolist()
                vec.append(vec[-1])
                direction_setting.append(vec)
        # direction
        direction = []
        for _direction in direction_setting:
            tmp_direction = dict()
            for i, k in enumerate(self.DIRECTIONAL_COLUMN_NAMES):
                tmp_direction[k] = [drc[i] for drc in _direction]
            direction.append(tmp_direction)
        return direction

    def _integrate_sensor(
            self,
            location: list[dict],
            direction: list[dict],
            ) -> pd.DataFrame:
        """Integrate sensor location and direction data.

        Args:
            location: Location of the sensor.
                x: x coordinates in global coordinate system.
                y: y coordinates in global coordinate system.
                z: z coordinates in global coordinate system.
            direction: Direction of the sensor.
                direction_x: x components of direction unit vector in global coordinate system.
                direction_y: y components of direction unit vector in global coordinate system.
                direction_z: z components of direction unit vector in global coordinate system.

        Returns:
            Sensor location and direction data.
        """
        sensor = defaultdict(list)
        if location is not None:
            for _location in location:
                for k in self.LOCATIONAL_COLUMN_NAMES:
                    sensor[k].extend(_location[k])
        if direction is not None:
            for _direction in direction:
                for k in self.DIRECTIONAL_COLUMN_NAMES:
                    sensor[k].extend(_direction[k])
        sensor = pd.DataFrame(dict(sensor))
        sensor.index = sensor.index + 1
        sensor.index.name = 'sensor_id'
        return sensor
