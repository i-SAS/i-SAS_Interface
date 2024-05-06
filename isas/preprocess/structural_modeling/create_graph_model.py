from isas_base.data.static_data.structural_model import GraphModel
from isas_base.utils import get_cfg


def create_graph_model(
        cfg: dict
        ) -> GraphModel:
    """Create graph model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.
    """
    modeler = GraphModeler(cfg)
    return modeler()


class GraphModeler:
    DEFAULT_CFG = {}

    def __init__(
            self,
            cfg: dict
            ) -> None:
        """Initialize GraphModeler.

        Args:
            cfg: GraphModel config.
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

    def __call__(self) -> GraphModel:
        """Create GraphModel.

        Returns:
            An instance of GraphModel.
        """
        return GraphModel(
            **self._create_graph_node(),
            **self._create_graph_edge(),
            )

    def _create_graph_node(self) -> dict:
        """Create nodes of graph model."""
        raise NotImplementedError()
        return {'graph_node': None}

    def _create_graph_edge(self) -> dict:
        """Create edges of graph model."""
        raise NotImplementedError()
        return {'graph_edge': None}
