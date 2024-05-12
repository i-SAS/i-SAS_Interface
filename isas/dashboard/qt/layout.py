import importlib
from typing import Final, Self

from isas_base.subpackage import BaseVisualization
from PySide6 import QtWidgets


class Layout:
    LAYOUTS: Final[dict] = {
        'box': QtWidgets.QBoxLayout,
        'form': QtWidgets.QFormLayout,
        'grid': QtWidgets.QGridLayout,
        'hbox': QtWidgets.QHBoxLayout,
        'stacked': QtWidgets.QStackedLayout,
        'vbox': QtWidgets.QVBoxLayout,
    }
    TASKS: Final[set] = {'visualization'}
    cfg: dict | None = None

    @classmethod
    def set_cfg(
            cls,
            cfg: dict,
            ) -> None:
        """Set config.

        Args:
            cfg: A config of subpackages.
        """
        cls.cfg = {
            subpackage_cfg['INIT_ARGS']['INSTANCE_NAME']: subpackage_cfg
            for subpackage_cfg in cfg if subpackage_cfg['TASK'] in cls.TASKS
            }

    def __new__(
            cls,
            layout_type: str,
            *args,
            **kwargs
            ) -> Self:
        """Initialize original layout class that inherits from the corresponding layout class of PySide6.

        Args:
            layout_type: A name of layout type.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            An instance of original layout class that inherits from the corresponding layout class of PySide6.

        Examples:
            >>> layout = Layout('vbox')
            >>> layout.addVisualizer(Visualizer(
                    'visualizer',
                    'example',
                    (6, 6),
                    variable_names={'text': 'dd_text'}
                ))
        """
        layout_class = type(
            'Layout',
            (_Layout, cls.LAYOUTS[layout_type]),
            {
                'cfg': cls.cfg,
                'isas_subpackages': [],
            }
        )
        return layout_class(*args, **kwargs)


class _Layout:
    def addSubpackage(  # noqa: N802
            self,
            instance_name: str,
            ) -> None:
        """Add visualization subpackage to the layout.

        Args:
            instance_name: A instance name of the visualization subpackage.
        """
        model = self._get_model(instance_name)
        self.isas_subpackages.append(model)
        self.addWidget(model.create_widget())

    def addLayout(  # noqa: N802
            self,
            layout: QtWidgets.QLayout,
            *args,
            **kwargs
            ) -> None:
        """Add layout with visualizer and contoller.
        This function override the function of PySide6.

        Args:
            widget: A layout added to the layout.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.isas_subpackages.extend(layout.isas_subpackages)
        super().addLayout(layout, *args, **kwargs)

    def addWidget(  # noqa: N802
            self,
            widget: QtWidgets.QLayout,
            *args,
            **kwargs
            ) -> None:
        """Add widget with visualizer and contoller.
        This function override the function of PySide6.

        Args:
            widget: A widget added to the layout.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        layout = widget.layout()
        if layout is not None and hasattr(layout, 'isas_subpackages'):
            self.isas_subpackages.extend(layout.isas_subpackages)
        super().addWidget(widget, *args, **kwargs)

    def _get_model(
            self,
            instance_name: str
            ) -> BaseVisualization:
        """Get model from config and instance name.

        Args:
            instance_name: A name of the controller instance.

        Returns:
            An instance of the Sub Package.
        """
        if instance_name not in self.cfg:
            raise ValueError(f'{instance_name} does not exist in config.')
        cfg = self.cfg[instance_name]
        module = importlib.import_module(cfg['SUBPACKAGE_NAME'])
        module_class = getattr(module, cfg['MODEL_NAME'])
        model = module_class(
            **{k.lower(): v for k, v in cfg['INIT_ARGS'].items()},
            **cfg['PARAMS'],
            )
        return model
