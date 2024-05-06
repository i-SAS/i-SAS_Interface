from isas_base.data.static_data.structural_model import GraphModel
from isas_base.utils import get_cfg


def import_graph_model(
        cfg: dict
        ) -> GraphModel:
    """Import graph model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.
    """
    importer = GraphModelImporter(cfg)
    return importer()


class GraphModelImporter:
    DEFAULT_CFG = {}

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize GraphModelImporter.

        Args:
            cfg: GraphModel config.
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
            cfg: GraphModel config.
        """
        raise NotImplementedError()

    def __call__(self) -> GraphModel:
        """Import GraphModel.

        Returns:
            An instance of GraphModel.
        """
        return GraphModel(
            **self._import_graph_model()
            )

    def _import_graph_model(self) -> dict:
        """Import GraphModel from xx."""
        raise NotImplementedError()
