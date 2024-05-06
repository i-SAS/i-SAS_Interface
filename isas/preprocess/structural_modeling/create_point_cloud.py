from isas_base.data.static_data.structural_model import PointCloud
from isas_base.utils import get_cfg


def create_point_cloud(
        cfg: dict
        ) -> PointCloud:
    """Create point cloud model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.
    """
    modeler = PointCloudModeler(cfg)
    return modeler()


class PointCloudModeler:
    DEFAULT_CFG = {}

    def __init__(
            self,
            cfg: dict
            ) -> None:
        """Initialize PointCloudModeler.

        Args:
            cfg:  PointCloud config.
        """
        cfg = get_cfg(cfg, self.DEFAULT_CFG)
        self._check_cfg(cfg)
        self.cfg = cfg

    def _check_cfg(
            self,
            cfg: dict
            ) -> None:
        """Check config."""
        raise NotImplementedError()

    def __call__(self) -> PointCloud:
        """Create PointCloud.

        Returns:
            An instance of PointCloud.
        """
        return PointCloud(
            **self._create_point_cloud()
            )

    def _create_point_cloud(self) -> dict:
        """Create point cloud model."""
        raise NotImplementedError()
        return {'point_cloud': None}
