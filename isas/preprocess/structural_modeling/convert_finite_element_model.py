import itertools

import numpy as np
import pandas as pd
from isas_base.data.static_data.structural_model import (
    FiniteElementModel, GraphModel, PointCloud, StructuralModel
)
from isas_base.utils import get_cfg

from ..utils import calc_fe_elem_center


def convert_finite_element_model(
        cfg: dict,
        structural_model: FiniteElementModel,
        ) -> StructuralModel:
    """Convert finite element model to other model type.

    Args:
        cfg: Structural model config.
        structural_model: An instance of FiniteElementModel.

    Returns:
        Converted structural model.
    """
    converter = FiniteElementModelConverter(cfg)
    return converter(structural_model)


class FiniteElementModelConverter:
    DEFAULT_CFG = {
        'MODEL_TYPE': None,
    }
    MODEL_TYPES = {
        'fe': FiniteElementModel,
        'graph': GraphModel,
        'point_cloud': PointCloud,
        }

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize FiniteElementModelConverter.

        Args:
            cfg: FiniteElementModel config.
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
            cfg: FiniteElementModel config.
        """
        if 'MODEL_TYPE' not in cfg:
            raise ValueError('"MODEL_TYPE" is required config.')
        if cfg['MODEL_TYPE'] not in self.MODEL_TYPES.keys():
            raise ValueError(f'{self.MODEL_TYPES.keys()} are supported as a model types.')

    def __call__(
            self,
            structural_model: FiniteElementModel,
            ) -> StructuralModel:
        """Convert FiniteElementModel.

        Args:
            cfg: Structural model config.
            structural_model: An instance of FiniteElementModel.

        Returns:
            An instance of StructuralModel.
        """
        if not isinstance(structural_model, FiniteElementModel):
            raise ValueError('Inputted structural model is not finite element model.')
        if self.cfg['MODEL_TYPE'] == 'fe':
            return structural_model
        converter = {
            'graph': self._convert_fe2graph,
            'point_cloud': self._convert_fe2point,
            }
        return self.MODEL_TYPES[self.cfg['MODEL_TYPE']](
            **converter[self.cfg['MODEL_TYPE']](structural_model)
            )

    def _convert_fe2graph(
            self,
            structural_model: FiniteElementModel,
            ) -> GraphModel:
        """Convert FiniteElementModel to GraphModel.

        Args:
            structural_model: An instance of FiniteElementModel.

        Returns:
            An instance of GraphModel.
        """
        fe_node = structural_model.fe_node
        fe_elem = structural_model.fe_elem
        fe_connection = structural_model.fe_connection

        # Create graph node.
        fe_elem_id, fe_elem_center = calc_fe_elem_center(fe_node, fe_elem, fe_connection)
        graph_node = pd.DataFrame(
            np.hstack([fe_elem_id.reshape((-1, 1)), fe_elem_center]),
            columns=['graph_node_id', 'x', 'y', 'z']
            )
        graph_node = graph_node.astype({'graph_node_id': 'int32', 'x': 'float32', 'y': 'float32', 'z': 'float32'})
        graph_node = graph_node.set_index('graph_node_id')

        # Create graph elem.
        _connection_e2n = fe_connection.groupby(['fe_node_id'])['fe_elem_id'].apply(np.array).values
        edges = []
        for i in range(0, len(_connection_e2n)):
            _candidate = list(itertools.combinations(_connection_e2n[i][~np.isnan(_connection_e2n[i])], 2))
            for j in range(0, len(_candidate)):
                if _candidate[j] not in edges:
                    edges.append(_candidate[j])
        edges = np.hstack([np.arange(1, len(edges)+1).reshape((-1, 1)), np.array(edges)])
        graph_edge = pd.DataFrame(edges, columns=['graph_edge_id', 'connection1', 'connection2'])
        graph_edge = graph_edge.astype({'graph_edge_id': 'int32', 'connection1': 'int32', 'connection2': 'int32'})
        graph_edge = graph_edge.set_index('graph_edge_id')
        return {
            'graph_node': graph_node,
            'graph_edge': graph_edge,
            }

    def _convert_fe2point(
            self,
            structural_model: FiniteElementModel,
            ) -> PointCloud:
        """Convert FiniteElementModel to PointCloud.

        Args:
            structural_model: An instance of FiniteElementModel.

        Returns:
            An instance of PointCloud.
        """
        point_cloud = structural_model.fe_node
        point_cloud.index.name = 'point_id'
        return {
            'point_cloud': point_cloud,
            }
