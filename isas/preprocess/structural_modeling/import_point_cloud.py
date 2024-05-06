from isas_base.data.static_data.structural_model import PointCloud
from isas_base.utils import get_cfg


def import_point_cloud(
        cfg: dict
        ) -> PointCloud:
    """Import point cloud model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.
    """
    importer = PointCloudImporter(cfg)
    return importer()


class PointCloudImporter:
    DEFAULT_CFG = {}

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize PointCloudImporter.

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
        raise NotImplementedError()

    def __call__(self) -> PointCloud:
        """Import PointCloud.

        Returns:
            An instance of PointCloud.
        """
        return PointCloud(
            **self._import_point_cloud()
            )

    def _import_point_cloud(self) -> dict:
        """Import PointCloud from xx."""
        raise NotImplementedError()
