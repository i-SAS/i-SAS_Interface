import logging
from typing import Any, Final

from ..base import Base
from .qt import DashboardApp

logger = logging.getLogger(__name__)


class Dashboard(Base):
    """i-SAS Dashboard"""
    SERVICE_TYPE: Final[str] = 'Dashboard'
    DEFAULT_CFG: Final[dict[str, Any]] = {
        'DOWNLOAD_DATA': False,
        'INIT_DB': False,
        'DATADRIVE': '/root/datadrive',
        'TABLE_DATA_SYSTEM': 'file',
        'TIME_SERIES_DATA_SYSTEM': 'file',
        'PREPROCESS': [],
        'DATA_PROCESSING_METHOD': 'batch',
        'LAYOUT': {
            'LAYOUT_NAME': None,
            'COLOR_THEME': 'white',
            'PROJECT_TITLE': 'no_name_project',
            'WINDOW_TITLE': 'i-SAS Dashboard',
            'WINDOW_WIDTH': 1280,
            'WINDOW_HEIGHT': 720,
            }
        }

    def _set_models(
            self,
            cfg: dict[str, Any],
            ) -> None:
        """Set models from cfg.

        Args:
            cfg: A config of the service.
        """
        static_data = self.data_manager.import_static_data(data_system=self.cfg['TABLE_DATA_SYSTEM'])
        self.dashboard_app = DashboardApp(
            cfg,
            self.data_manager,
            self.service_name,
            self.streaming,
            static_data,
            )

    def __call__(self) -> None:
        """Start updating Dashboard window."""
        logger.info(f'[{self.SERVICE_TYPE}] Start Qt.')
        self.dashboard_app.start()

    def exit(self) -> None:
        """Terminate Dashboard window."""
        logger.info(f'[{self.SERVICE_TYPE}] Terminate Qt.')
        self.dashboard_app.terminate()
        logger.info(f'[{self.SERVICE_TYPE}] Exit.')
