import importlib
import logging
import queue
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final

from isas_base.data import DynamicData, ParallelExporter, StaticData

from .base import Base
from .utils.dynamic_data_utils import (
    arrange_result, generate_tag, generate_time_series_batch_metadata,
    get_dependencies
)

logger = logging.getLogger(__name__)


class Interface(Base):
    """i-SAS Interface"""
    SERVICE_TYPE: Final[str] = 'Interface'
    DEFAULT_CFG: Final[dict[str, Any]] = {
        'DOWNLOAD_DATA': False,
        'INIT_DB': False,
        'DATADRIVE': '/root/datadrive',
        'TABLE_DATA_SYSTEM': 'file',
        'TIME_SERIES_DATA_SYSTEM': 'file',
        'PREPROCESS': [],
        'DATA_PROCESSING_METHOD': 'batch',
        'STREAM_EXPORT_QUEUE_MAXSIZE': 100,
        'SIMULATE_STREAM_PARAMS': {
            'SLEEP_TIME': 1,  # sec
            'LOOP': False,  # bool
            'FIRST_DATETIME': '2020-04-01 12:00:00',  # YYYY-mm-dd HH:MM:SS[.ffffff]
            'LAST_DATETIME': '2020-04-01 12:00:00',  # YYYY-mm-dd HH:MM:SS[.ffffff]
            'INTERVAL': 1,  # sec
            },
        }

    def __init__(
            self,
            cfg: str | Path | dict | None = None,
            static_data: StaticData | None = None,
            ) -> None:
        """Initialize Interface class.

        Args:
            cfg: A path to the cfg file or a dict of cfg.
            static_data: A instance of StaticData datalcass.
        """
        super().__init__(cfg, static_data)
        if self.streaming:
            self.export_queue = queue.Queue(maxsize=self.cfg['STREAM_EXPORT_QUEUE_MAXSIZE'])
            self.parallel_exporter = ParallelExporter(
                self.export_queue,
                self.data_manager,
                table_data_system=self.cfg['TABLE_DATA_SYSTEM'],
                time_series_data_system=self.cfg['TIME_SERIES_DATA_SYSTEM'],
                )
            self.parallel_exporter.start()

    def _init_models(self) -> None:
        """Initialize model attributes."""
        super()._init_models()
        self.models = {}
        self.import_data_names = {}
        self.export_data_names = []
        self.last_datetime = None

    def _set_models(
            self,
            cfg: dict[str, Any],
            ) -> None:
        """Set models from cfg.

        Args:
            cfg: A config of the service.
        """
        subpackages_cfg = cfg.get('SUBPACKAGES', [])
        export_data_names = cfg.get('EXPORT_DATA_NAMES', [])
        # import models
        models = defaultdict(list)
        for cfg in subpackages_cfg:
            logger.debug(f'[{self.SERVICE_TYPE}] Importing model: {cfg["MODEL_NAME"]}')
            module = importlib.import_module(cfg['SUBPACKAGE_NAME'])
            module_class = getattr(module, cfg['MODEL_NAME'])
            model = module_class(
                service_name=self.service_name,
                **{k.lower(): v for k, v in cfg['INIT_ARGS'].items()},
                **cfg['PARAMS'],
                )
            models[model.TASK].append(model)
        # check models
        tasks = ('measurement', 'analysis')
        if not set(models.keys()) <= set(tasks):
            raise ValueError(f'Unsupported tasks exist: {set(models.keys()) - set(tasks)}')
        # set models for the task
        for task in tasks:
            if task not in models:
                continue
            logger.debug(f'[{self.SERVICE_TYPE}] Setting task: {task}.')
            input_data_names = []
            output_data_names = []
            for model in models[task]:
                logger.debug(f'[{self.SERVICE_TYPE}] Setting model: {model.MODEL_NAME}')
                # set model.
                model.set_model(
                    static_data=self.static_data,
                    streaming=self.streaming,
                    )
                # update static data.
                self.static_data.update(model.get_static_data())
                input_data_names.extend(model.input_data_names)
                output_data_names.extend(model.output_data_names)
            self.models[task] = models[task]
            logger.debug(f'[{self.SERVICE_TYPE}] Set {task} models: {models[task]=}')
            self.import_data_names[task] = list(set(input_data_names) - set(output_data_names))
            logger.debug(f'[{self.SERVICE_TYPE}] Set import_data_names: {task}/{self.import_data_names[task]}')
            if export_data_names is not None:
                self.export_data_names.extend(list(set(export_data_names) & set(output_data_names)))
                logger.debug(f'[{self.SERVICE_TYPE}] Set export_data_names: {task}/{self.export_data_names}')

    def __call__(
            self,
            dynamic_data: DynamicData | None = None,
            first_datetime: datetime | None = None,
            last_datetime: datetime | None = None,
            ) -> DynamicData:
        """Apply analysis solvers.

        Args:
            dynamic_data: An instance of DynamicData datalcass.
            first_datetime: The data is imported after this datetime. The default, None
            last_datetime: The data is imported before this datetime. The default, None

        Returns:
            An instance of DynamicData datalcass including results.
        """
        if self.cfg['DATA_PROCESSING_METHOD'] == 'simulate_stream':
            if first_datetime is not None or last_datetime is not None:
                raise ValueError('datetime must be None with simulate_stream.')
            first_datetime, last_datetime = self._simulate_streaming()
        logger.info(f'[{self.SERVICE_TYPE}] Calling with args: {first_datetime=}, {last_datetime=}')

        tag = generate_tag(self.service_name)
        tasks = ('measurement', 'analysis')
        dynamic_data = DynamicData() if dynamic_data is None else dynamic_data
        for task in tasks:
            streaming = False if task == 'measurement' else self.streaming
            data_system = 'streaming' if streaming else self.cfg['TIME_SERIES_DATA_SYSTEM']
            # import dynamic data
            logger.debug(f'[{self.SERVICE_TYPE}] Importing dynamic data for {task}.')
            # Do not overwrite existing data.
            data_name = list(set(self.import_data_names.get(task, [])) - set(dynamic_data.time_series_data.keys()))
            _dynamic_data = self.data_manager.import_dynamic_data(
                data_name=data_name,
                time_series_data_system=data_system,
                first_datetime=first_datetime,
                last_datetime=last_datetime,
                import_metadata=False,
                )
            dynamic_data.update(_dynamic_data)
            # apply model
            for model in self.models.get(task, []):
                logger.debug(f'[{self.SERVICE_TYPE}] Applying model: {task}/{model.MODEL_NAME}')
                res = model(dynamic_data)
                dynamic_data.update(arrange_result(res, tag))
        # batch metadata
        dependent_batch_id = get_dependencies(dynamic_data, tag)
        dynamic_data.update(generate_time_series_batch_metadata(tag, dependent_batch_id))
        # export dynamic data
        logger.debug(f'[{self.SERVICE_TYPE}] Exporting dynamic data for {task}.')
        if self.cfg['TIME_SERIES_DATA_SYSTEM'] in ('influx', ):
            self.data_manager.export_dynamic_data(
                dynamic_data,
                data_name=self.export_data_names,
                table_data_system=self.cfg['TABLE_DATA_SYSTEM'],
                time_series_data_system=data_system,
                )
            if self.streaming:
                self.export_queue.put((self.export_data_names, dynamic_data))
        return dynamic_data

    def _simulate_streaming(self) -> tuple[datetime]:
        """Calculate datetime to simulate streaming process.

        Returns
            first and last datetime for simulation.
        """
        cfg = self.cfg['SIMULATE_STREAM_PARAMS']
        time.sleep(cfg['SLEEP_TIME'])
        loop = self.last_datetime is not None and cfg['LOOP'] and \
            self.last_datetime >= datetime.fromisoformat(cfg['LAST_DATETIME'])
        if self.last_datetime is None or loop:
            self.last_datetime = datetime.fromisoformat(cfg['FIRST_DATETIME'])
        fisrt_datetime = self.last_datetime
        last_datetime = fisrt_datetime + timedelta(seconds=cfg['INTERVAL'])
        self.last_datetime = last_datetime
        return fisrt_datetime, last_datetime

    def exit(self) -> None:
        """Exit models."""
        if self.streaming:
            self.parallel_exporter.exit = True
            self.parallel_exporter.join()

        for model_list in self.models.values():
            for model in model_list:
                model.exit()
        logger.info(f'[{self.SERVICE_TYPE}] Exit.')
