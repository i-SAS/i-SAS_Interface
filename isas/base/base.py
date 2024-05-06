import logging
import os
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from isas_base.data import DataManager, StaticData
from isas_base.data.static_data.service_metadata import ServiceMetadata
from isas_base.utils import download, get_cfg

from .. import preprocess

logger = logging.getLogger(__name__)


class Base(ABC):
    """i-SAS Base"""
    DEFAULT_SERVICE_NAME = 'no_name_service'

    @property
    @abstractmethod
    def SERVICE_TYPE(self) -> str:  # NOQA
        pass

    @property
    @abstractmethod
    def DEFAULT_CFG(self) -> dict[str, Any]:  # NOQA
        pass

    def __init__(
            self,
            cfg: str | Path | dict | None = None,
            static_data: StaticData | None = None,
            ) -> None:
        """Initialize Interface class.

        Args:
            cfg: A path to the cfg file or a dict of cfg.
            static_data: An instance of StaticData.
        """
        cfg = self._get_cfg(cfg)
        logger.info(f'[{self.SERVICE_TYPE}] Initializing with args: {cfg=}')
        self.service_name = os.getenv('SERVICE_NAME', self.DEFAULT_SERVICE_NAME)
        self.cfg = cfg.get('SERVICE', {})
        self._init_models()
        if static_data is not None:
            self.static_data.update(static_data)

        # download data from data_source
        if self.cfg['DOWNLOAD_DATA']:
            download(os.getenv('DATA_ID'), os.getenv('DATA_SOURCE'))
        # initialize db
        if self.cfg['INIT_DB']:
            self.data_manager.init_rdb()
            self.data_manager.init_tsdb()
        # pull static data
        static_data = self.data_manager.import_static_data(data_system=self.cfg['TABLE_DATA_SYSTEM'])
        self.static_data.update(static_data)
        # run preprocess and merge static data
        if self.cfg.get('PREPROCESS', None) is not None:
            static_data = preprocess.create_static_data(self.cfg['PREPROCESS'], self.static_data)
            self.static_data.update(static_data)

        static_data = self._get_service_metadata()
        self.static_data.update(static_data)

        self.streaming = self.cfg['DATA_PROCESSING_METHOD'] in ('stream', 'simulate_stream')
        self._set_models(cfg)

        # push static data to DB
        if self.cfg['TABLE_DATA_SYSTEM'] in ('postgres', ):
            self.data_manager.export_static_data(self.static_data, data_system=self.cfg['TABLE_DATA_SYSTEM'])

    def _get_cfg(
            self,
            cfg: str | Path | dict[str, Any],
            ) -> dict:
        """Get a dict of config.

        Args:
            cfg: A path to the config file or a dict of config.

        Returns:
            A dict of config overwriting default config.
        """
        if isinstance(cfg, (str, Path)):
            with Path(cfg).open('r') as f:
                cfg = yaml.safe_load(f)
        base_cfg = {'SERVICE': deepcopy(self.DEFAULT_CFG)}

        cfg = get_cfg(cfg, base_cfg)
        self._check_cfg(cfg)
        return cfg

    def _check_cfg(
            self,
            cfg: dict,
            ) -> None:
        """Check if config is valid.

        Args:
            cfg: A dict of config.
        """
        data_processing_method = cfg['SERVICE']['DATA_PROCESSING_METHOD']
        if data_processing_method not in ('batch', 'stream', 'simulate_stream'):
            raise ValueError(f'Unsupported DATA_PROCESSING_METHOD: {data_processing_method}')

    def _init_models(self) -> None:
        """Initialize model attributes."""
        self.data_manager = DataManager(
            datadrive=self.cfg['DATADRIVE'],
            )
        self.static_data = StaticData()

    def _get_service_metadata(self) -> StaticData:
        """Get ServiceMetadata."""
        return StaticData(
            service_metadata={self.service_name: ServiceMetadata()},
            )

    @abstractmethod
    def __call__(self):
        """Run model."""
        raise NotImplementedError()

    @abstractmethod
    def exit(self) -> None:
        """Exit model."""
        raise NotImplementedError()
