import importlib
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from isas_base.data import DataManager, StaticData
from PySide6 import QtCore, QtGui, QtWidgets

from ...utils.dynamic_data_utils import arrange_result

logger = logging.getLogger(__name__)


class DashboardApp(QtWidgets.QWidget):
    """QWidget class for Dashboard Application based on PySide6"""
    COLOR_THEME: Final[set] = {
        'white',
        'dark',
        }
    LAYOUT_CLASS_NAME: Final[str] = 'ContentLayout'

    def __init__(
            self,
            cfg: dict,
            data_manager: DataManager,
            service_name: str,
            streaming: bool,
            static_data: StaticData | None = None,
            ) -> None:
        """Initialize QWidget class for Dashboard Application.

        Args:
            cfg: Config.
            data_manager: A instance of DataManager.
            service_name: A name of the service.
            streaming: A flag of streaming.
            static_data: Static data.
        """
        logger.info(f'[Dashboard/DashboardApp] Initializing with args: {cfg=}')

        self.cfg = cfg['SERVICE']
        if self.cfg['LAYOUT']['COLOR_THEME'] not in self.COLOR_THEME:
            raise ValueError(f'Color theme {self.cfg["LAYOUT"]["COLOR_THEME"]} is not defined.')
        self.subpackage_cfg = cfg['SUBPACKAGES']
        self.data_manager = data_manager
        self.service_name = service_name
        self.streaming = streaming
        self.material_dir = Path(__file__).resolve().parents[1] / 'materials'
        self.current_tab_name = None
        self.subpackages = dict()
        self.import_data_names = dict()

        # QApplocation
        logger.info('[Dashboard/DashboardApp] Create QApplocation')
        self.app = QtWidgets.QApplication.instance()
        if not self.app:
            self.app = QtWidgets.QApplication()
        super().__init__()

        # set css
        logger.debug('[Dashboard/DashboardApp] Set CSS.')
        css_path = self.material_dir / f'css/{self.cfg["LAYOUT"]["COLOR_THEME"]}.css'
        with css_path.open('r') as f:
            css = f.readlines()
        self.setStyleSheet(''.join(css))

        # set window
        logger.debug('[Dashboard/DashboardApp] Set window.')
        self.setWindowTitle(self.cfg['LAYOUT']['WINDOW_TITLE'])
        self.resize(self.cfg['LAYOUT']['WINDOW_WIDTH'], self.cfg['LAYOUT']['WINDOW_HEIGHT'])

        # set tab pages
        logger.debug('[Dashboard/DashboardApp] Set tab pages.')
        tab_pages = self._create_tab_pages(
            static_data,
            )
        self.tab_names = list(tab_pages.keys())

        # set main layout
        logger.debug('[Dashboard/DashboardApp] Set main layout.')
        header = self._create_header()
        body = self._create_body(tab_pages)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(header)
        self.main_layout.addLayout(body)

        # set timer
        logger.debug('[Dashboard/DashboardApp] Set timer.')
        self.timer = QtCore.QTimer(self)
        # Use lambda function: https://qiita.com/MachineCAT/items/1141f03da64dfac0be8e
        self.timer.timeout.connect(lambda: self._update())

    def _create_tab_pages(
            self,
            static_data: StaticData,
            ) -> dict:
        """Create tab pages.

        Args:
            static_data: Static data.

        Returns:
            A dict of tab pages. Kyes are tab names and values are Widgets.
        """
        module = importlib.import_module(self.cfg['LAYOUT']['LAYOUT_NAME'])
        model = getattr(module, self.LAYOUT_CLASS_NAME)(self.subpackage_cfg)
        contents = model()

        tab_pages = {}
        for tab_name, function in contents.items():
            logger.debug(f'[Dashboard/DashboardApp] Set tab: {tab_name}')
            layout = function()

            # Set pages.
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setMinimumHeight(1)
            scroll_area.setLayout(layout)
            tab_pages[tab_name] = scroll_area

            # Set subpackages.
            subpackages = []
            for subpackage in layout.isas_subpackages:
                subpackage.set_color_theme(self.cfg['LAYOUT']['COLOR_THEME'])
                subpackage.set_model(static_data=static_data)
                subpackages.append(subpackage)
            self.subpackages[tab_name] = sorted(subpackages, key=lambda x: x.get_update_priority(), reverse=True)

            # Set import data names
            self.import_data_names[tab_name] = list(set([
                data_name for subpackage in subpackages for data_name in subpackage.input_data_names
                ]))
        return tab_pages

    def _create_header(self) -> QtWidgets.QHBoxLayout:
        """Create header of application window.

        Returns:
            A layout for header.
        """
        icon_dir = self.material_dir / f'icon/{self.cfg["LAYOUT"]["COLOR_THEME"]}'
        # i-SAS logo.
        isas_logo_path = icon_dir / 'isas_logo.png'
        isas_logo = QtWidgets.QLabel()
        isas_logo.setPixmap(QtGui.QPixmap(str(isas_logo_path)))

        # A name of project.
        project_name = QtWidgets.QLabel(self.cfg['LAYOUT']['PROJECT_TITLE'])
        project_name.setStyleSheet('font-weight: bold; font-size: 20pt')

        # Timestamp.
        now_datetime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.timestamp = QtWidgets.QLabel(f'Last update time:\n{now_datetime}')
        self.timestamp.setAlignment(QtCore.Qt.AlignCenter)
        self.timestamp.setStyleSheet('font-size: 14pt')

        # Start button.
        start_button_path = icon_dir / 'start.png'
        start_button = QtWidgets.QToolButton()
        start_button.setIcon(QtGui.QIcon(str(start_button_path)))
        start_button.setIconSize(QtCore.QSize(50, 50))
        # Use lambda function: https://qiita.com/MachineCAT/items/1141f03da64dfac0be8e
        start_button.clicked.connect(lambda: self.timer.start(self.cfg['INTERVAL']))

        # Stop button.
        stop_button_path = icon_dir / 'stop.png'
        stop_button = QtWidgets.QToolButton()
        stop_button.setIcon(QtGui.QIcon(str(stop_button_path)))
        stop_button.setIconSize(QtCore.QSize(50, 50))
        # Use lambda function: https://qiita.com/MachineCAT/items/1141f03da64dfac0be8e
        stop_button.clicked.connect(lambda: self.timer.stop())

        # Header.
        empty_widget = QtWidgets.QWidget()
        header = QtWidgets.QHBoxLayout()
        for widget in (isas_logo, project_name, empty_widget, self.timestamp, start_button, stop_button):
            header.addWidget(widget)
        return header

    def _create_body(
            self,
            tab_pages: dict,
            ) -> QtWidgets.QHBoxLayout:
        """Create body of application window.

        Args:
            tab_pages: A dict of tab pages. Kyes are tab names and values are Widgets.

        Returns:
            A layout for body.
        """
        # sidebar and tab buttons
        tab_buttons = QtWidgets.QButtonGroup()
        tab_buttons.setExclusive(True)
        sidebar = QtWidgets.QVBoxLayout()
        for i, tab_name in enumerate(tab_pages):
            # Tab button.
            tab_button = QtWidgets.QPushButton()
            tab_button.setCheckable(True)
            tab_button.setText(tab_name)
            tab_button.setStyleSheet('font-size: 14pt')
            tab_button.setFixedSize(150, 50)
            tab_buttons.addButton(tab_button, i)
            sidebar.addWidget(tab_button)
        # Use lambda function: https://qiita.com/MachineCAT/items/1141f03da64dfac0be8e
        tab_buttons.buttonClicked.connect(lambda btn: self._change_tab(btn))
        sidebar.addStretch()

        # initialize sidebar
        tab_buttons.button(0).setChecked(True)
        self.tab_buttons = tab_buttons

        # content
        self.content = QtWidgets.QStackedWidget()
        for tab_page in tab_pages.values():
            self.content.addWidget(tab_page)
        self._change_tab(tab_buttons.button(0))

        body = QtWidgets.QHBoxLayout()
        body.addLayout(sidebar)
        body.addWidget(self.content)
        return body

    def _update(self) -> None:
        """Update window."""
        logger.info('[Dashboard/DashboardApp] Start updating window.')
        data_name = self.import_data_names[self.current_tab_name]
        logger.debug(f'[Dashboard/DashboardApp] Importing dynamic data: {self.current_tab_name}/{data_name}')
        data_system = 'streaming' if self.streaming else self.cfg['TIME_SERIES_DATA_SYSTEM']
        dynamic_data = self.data_manager.import_dynamic_data(
            data_name=data_name,
            time_series_data_system=data_system,
            import_metadata=False,
            )

        logger.debug('[Dashboard/DashboardApp] Update subpackages.')
        variables = dict()
        for subpackage in self.subpackages[self.current_tab_name]:
            res, new_variables = subpackage(dynamic_data, variables)
            dynamic_data.update(arrange_result(res))
            variables.update(new_variables)

        logger.debug('[Dashboard/DashboardApp] Update Datetime.')
        now_datetime = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y/%m/%d %H:%M:%S')
        self.timestamp.setText(f'Last update time:\n{now_datetime}')
        logger.info(
            f'[Dashboard/DashboardApp] Finish updating window. Timer reaming {self.timer.remainingTime()} msec.'
            )

    def _change_tab(
            self,
            btn: QtWidgets.QPushButton,
            ) -> None:
        """Change active tab."""
        self.current_tab_name = btn.text()
        logger.debug(f'[Dashboard/DashboardApp] Change tab to {self.current_tab_name}.')
        # change current tab
        self.content.setCurrentIndex(self.tab_names.index(self.current_tab_name))

    def start(self) -> None:
        """Start updating."""
        logger.info('[Dashboard/DashboardApp] Start App.')
        self.timer.start(self.cfg['INTERVAL'])
        self.show()
        self.app.exec()
        logger.info('[Dashboard/DashboardApp] Quit App.')

    def terminate(self) -> None:
        """Close window."""
        logger.info('[Dashboard/DashboardApp] Terminate App.')
        self.close()
