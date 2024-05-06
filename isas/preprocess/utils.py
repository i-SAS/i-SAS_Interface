import numpy as np
import pandas as pd


def calc_fe_elem_center(
        fe_node: pd.DataFrame,
        fe_elem: pd.DataFrame,
        fe_connection: pd.DataFrame,
        ) -> tuple[np.ndarray]:
    """Calculate coordinate of element center points of fe model.

    Args:
        fe_node: Node coordinates of fe model.
        fe_elem: Element data of fe model.
        fe_connection: Connections between nodes and elements.

    Returns:
        Element ID and Coordinate of element center points.
    """
    connection_n2e = fe_connection.groupby(['fe_elem_id'])['fe_node_id'].apply(np.array).to_numpy()
    fe_elem_center = np.array([
        fe_node[fe_node.index.isin(connection_n2e[i])].mean().tolist()
        for i in range(len(fe_elem))
    ])
    fe_elem_id = fe_elem.index.to_numpy().astype(int)
    return fe_elem_id, fe_elem_center
