from isas_base.data.static_data.structural_model import (
    GraphModel, PointCloud, StructuralModel
)
from isas_base.utils import get_cfg


def convert_graph_model(
        cfg: dict,
        structural_model: GraphModel,
        ) -> StructuralModel:
    """Convert graph model to other model type.

    Args:
        cfg: Structural model config.
        structural_model: An instance of GraphModel.

    Returns:
        Converted structural model.
    """
    converter = GraphModelConverter(cfg)
    return converter(structural_model)


class GraphModelConverter:
    DEFAULT_CFG = {
        'MODEL_TYPE': None,
        }
    MODEL_TYPES = {
        'graph': GraphModel,
        'point_cloud': PointCloud,
        }

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize GraphModelConverter.

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
        if 'MODEL_TYPE' not in cfg:
            raise ValueError('"MODEL_TYPE" is required config.')
        if cfg['MODEL_TYPE'] not in self.MODEL_TYPES:
            raise ValueError(f'{self.MODEL_TYPES.keys()} are supported as a model types.')

    def __call__(
            self,
            structural_model: GraphModel,
            ) -> StructuralModel:
        """Convert GraphModel.

        Args:
            structural_model: An instance of GraphModel.

        Returns:
            An instance of StructuralModel.
        """
        if not isinstance(structural_model, GraphModel):
            raise ValueError('Inputted structural model is not graph model.')
        if self.cfg['MODEL_TYPE'] == 'graph':
            return structural_model
        converter = {
            'point_cloud': self._convert_graph2point,
            }
        return self.MODEL_TYPES[self.cfg['MODEL_TYPE']](
            **converter[self.cfg['MODEL_TYPE']](structural_model)
            )

    def _convert_graph2point(
            self,
            structural_model: GraphModel
            ) -> PointCloud:
        """Convert GraphModel to PointCloud.

        Args:
            structural_model: An instance of GraphModel.

        Returns:
            An instance of PointCloud.
        """
        point_cloud = structural_model.graph_node
        point_cloud.index.name = 'point_id'
        return {
            'point_cloud': point_cloud,
            }
