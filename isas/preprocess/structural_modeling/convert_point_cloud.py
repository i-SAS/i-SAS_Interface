from isas_base.data.static_data.structural_model import (
    PointCloud, StructuralModel
)
from isas_base.utils import get_cfg


def convert_point_cloud(
        cfg: dict,
        structural_model: PointCloud,
        ) -> StructuralModel:
    """Convert point cloud model to other model type.

     Args:
        cfg: Structural model config.
        structural_model: An instance of PointCloud.

    Returns:
        Converted structural model.
    """
    converter = PointCloudConverter(cfg)
    return converter(structural_model)


class PointCloudConverter:
    DEFAULT_CFG = {
        'MODEL_TYPE': None,
        }
    MODEL_TYPES = {
        'point_cloud': PointCloud
        }

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize PointCloudConverter.

        Args:
            cfg: PointCloud config.
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
            cfg: PointCloud config.
        """
        if 'MODEL_TYPE' not in cfg:
            raise ValueError('"MODEL_TYPE" is required config.')
        if cfg['MODEL_TYPE'] not in self.MODEL_TYPES:
            raise ValueError(f'{self.MODEL_TYPES.keys()} are supported as a model types.')

    def __call__(
            self,
            structural_model: PointCloud,
            ) -> StructuralModel:
        """Convert PointCloud.

        Args:
            structural_model: An instance of PointCloud.

        Returns:
            An instance of StructuralModel.
        """
        if not isinstance(structural_model, PointCloud):
            raise ValueError('Inputted structural model is not point clould.')
        if self.cfg['MODEL_TYPE'] == 'point_cloud':
            return structural_model
        converter = {}  # Add functions here to support new MODEL_TYPES.
        return self.MODEL_TYPES[self.cfg['MODEL_TYPE']](
            **converter[self.cfg['MODEL_TYPE']](structural_model)
            )
