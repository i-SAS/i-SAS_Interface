import numpy as np
import pandas as pd
from isas_base.data.static_data.structural_model import FiniteElementModel
from isas_base.utils import get_cfg


def create_finite_element_model(
        cfg: dict
        ) -> FiniteElementModel:
    """Create finite element model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.

    Examples:
        >>> cfg = {'GEOMETRY_TYPE': 'PLATE', 'WIDTH': 100, 'HEIGHT': 100, 'THICKNESS': 1, ...}
        >>> structural_model = create_finite_element_model(cfg)
    """
    modeler = FiniteElementModeler(cfg)
    return modeler()


class FiniteElementModeler:
    DEFAULT_CFG = {
        'PLATE': {
            'WIDTH': None,
            'HEIGHT': None,
            'THICKNESS': None,
            'WIDTH_DIVIDE_NUM': 100,
            'HEIGHT_DIVIDE_NUM': 100,
            'YOUNGS_MODULUS': None,
            'POISSONS_RATIO': None,
            'R3': 0,
            'ELEM_TYPE': 'iQS4',
            'NODE_NUM': 4,
            'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
                123456: {},
            },
        },
        'CUSTOM_PLATE': {
            'X_ARRAY': None,
            'Y_ARRAY': None,
            'YOUNGS_MODULUS': None,
            'POISSONS_RATIO': None,
            'THICKNESS': None,
            'R3': 0,
            'ELEM_TYPE': 'iQS4',
            'NODE_NUM': 4,
            'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
                123456: {},
            },
        },
        'CUBOID': {
            'WIDTH': None,
            'DEPTH': None,
            'HEIGHT': None,
            'WIDTH_DIVIDE_NUM': 100,
            'DEPTH_DIVIDE_NUM': 100,
            'HEIGHT_DIVIDE_NUM': 100,
            'YOUNGS_MODULUS': None,
            'POISSONS_RATIO': None,
            'R3': 0,
            'ELEM_TYPE': 'solid',
            'NODE_NUM': 8,
            'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
                123456: {},
            },
        },
        'PIPE': {
            'LONGITUDINAL_LENGTH': None,
            'PIPE_RADIUS': None,
            'THICKNESS': None,
            'LONGITUDINAL_DIVIDE_NUM': 100,
            'CROSS_SECTION_DIVIDE_NUM': 100,
            'YOUNGS_MODULUS': None,
            'POISSONS_RATIO': None,
            'R3': 0,
            'ELEM_TYPE': 'iQS4',
            'NODE_NUM': 4,
            'CROSS_SECTION_SHAPE': None,  # ('circle', 'rectangle')
            'CONSTRAINT': {  # constraint_dof: {node_id: constraint_value}
                123456: {},
            },
        },
    }

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize FiniteElementModeler.

        Args:
            cfg: FiniteElementModel config.
        """
        geometry_type = cfg.get('GEOMETRY_TYPE', None)
        if geometry_type is None:
            raise ValueError('"GEOMETRY_TYPE" is not designated.')
        default_cfg = self.DEFAULT_CFG.get(geometry_type, None)
        if default_cfg is None:
            raise ValueError(f'"{geometry_type}" is not supported.')
        cfg = get_cfg(cfg, default_cfg)
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
        pass

    def __call__(self) -> FiniteElementModel:
        """Create FiniteElementModel.

        Returns:
            An instance of FiniteElementModel.
        """
        create_geometory = {
            'PLATE': self._create_plate,
            'CUSTOM_PLATE': self._create_custom_plate,
            'CUBOID': self._create_cuboid,
            'PIPE': self._create_pipe,
            }
        model = create_geometory[self.cfg['GEOMETRY_TYPE']]()
        return FiniteElementModel(
            **model,
            **self._create_constraint(model),
            )

    def _create_constraint(
            self,
            model: dict,
            ) -> dict:
        """Create node constraints.

        Returns:
            A dict containing constraint values.
        """
        dofs = ('x', 'y', 'z', 'rotation_x', 'rotation_y', 'rotation_z')
        fe_node_id = list()
        component = list()
        constraint = list()
        for dof, node_constraints in self.cfg['CONSTRAINT'].items():
            dof_num = len(str(dof))
            node_num = len(node_constraints)
            fe_node_id += np.repeat(list(node_constraints.keys()), dof_num, axis=0).tolist()
            component += [dofs[int(_dof)-1] for _dof in str(dof)]*node_num
            constraint += np.repeat(list(node_constraints.values()), dof_num, axis=0).tolist()
        fe_constraint_dict = {
            'fe_constraint_id': np.arange(1, len(constraint)+1),
            'fe_node_id': fe_node_id,
            'coord_sys': np.full(len(constraint), 'global'),
            'component': component,
            'constraint': constraint,
        }
        fe_constraint = pd.DataFrame.from_dict(fe_constraint_dict, orient='columns').set_index('fe_constraint_id')
        if model is not None:
            assert set(model['fe_node'].index) >= set(fe_constraint.fe_node_id), 'Invalid node id detected.'
        return {'fe_constraint': fe_constraint}

    def _create_plate(self) -> dict:
        """Create plate model.

        Returns:
            A dict containing node, element and connection values between nodes and elements of created model.
        """
        width_divide_num = int(self.cfg['WIDTH_DIVIDE_NUM'])
        height_divide_num = int(self.cfg['HEIGHT_DIVIDE_NUM'])
        width = float(self.cfg['WIDTH'])
        height = float(self.cfg['HEIGHT'])
        elem_width = width / width_divide_num
        elem_height = height / height_divide_num
        youngs_modulus = float(self.cfg['YOUNGS_MODULUS'])
        poissons_ratio = float(self.cfg['POISSONS_RATIO'])
        thickness = float(self.cfg['THICKNESS'])
        r3 = float(self.cfg['R3'])
        elem_type = self.cfg['ELEM_TYPE']
        each_elem_node_num = int(self.cfg['NODE_NUM'])
        if each_elem_node_num != 4:
            raise Exception(f'node_num = {each_elem_node_num} is unsupported value.')
        # Create fe_node.
        node_num = (width_divide_num + 1) * (height_divide_num + 1)
        fe_node_fe_node_id = np.arange(1, node_num + 1)
        fe_node_x_pos = np.tile(np.arange(0, width+elem_width/10, elem_width), height_divide_num + 1)
        fe_node_y_pos = np.repeat(np.arange(0, height+elem_height/10, elem_height), width_divide_num + 1)
        fe_node_z_pos = np.zeros(node_num)
        fe_node_dict = {
            'fe_node_id': fe_node_fe_node_id,
            'x': fe_node_x_pos,
            'y': fe_node_y_pos,
            'z': fe_node_z_pos,
        }
        fe_node = pd.DataFrame.from_dict(fe_node_dict, orient='columns').set_index('fe_node_id')
        # Create fe_elem.
        elem_num = width_divide_num * height_divide_num
        fe_elem_fe_elem_id = np.arange(1, elem_num + 1)
        fe_elem_elem_type = np.full(elem_num, elem_type)
        fe_elem_fe_node_num = np.full(elem_num, each_elem_node_num)
        fe_elem_r3 = np.full(elem_num, r3)
        fe_elem_youngs_modulus = np.full(elem_num, youngs_modulus)
        fe_elem_poissons_ratio = np.full(elem_num, poissons_ratio)
        fe_elem_dict = {
            'fe_elem_id': fe_elem_fe_elem_id,
            'elem_type': fe_elem_elem_type,
            'node_num': fe_elem_fe_node_num,
            'r3': fe_elem_r3,
            'youngs_modulus': fe_elem_youngs_modulus,
            'poissons_ratio': fe_elem_poissons_ratio,
        }
        fe_elem = pd.DataFrame.from_dict(fe_elem_dict, orient='columns').set_index('fe_elem_id')
        # Create fe_connection.
        fe_connection_id_list = []
        fe_connection_fe_node_id_list = []
        fe_connection_fe_elem_id_list = []
        fe_connection_fe_node_order = []
        fe_connection_thickness_list = []
        node_addjust_num = 0
        columns_count = 0
        for i in range(width_divide_num * height_divide_num):
            columns_count += 1
            if (columns_count > width_divide_num):
                node_addjust_num += 1
                columns_count = 1
            fe_connection_id_list.extend([4*i+1, 4*i+2, 4*i+3, 4*i+4])
            fe_connection_fe_node_id_list.extend([
                node_addjust_num * (width_divide_num + 1) + columns_count,
                node_addjust_num * (width_divide_num + 1) + columns_count + 1,
                (node_addjust_num + 1) * (width_divide_num + 1) + columns_count + 1,
                (node_addjust_num + 1) * (width_divide_num + 1) + columns_count
            ])
            fe_connection_fe_elem_id_list.extend([i + 1, i + 1, i + 1, i + 1])
            fe_connection_fe_node_order.extend([1, 2, 3, 4])
            fe_connection_thickness_list.extend([thickness, thickness, thickness, thickness])
        fe_connection_dict = {
            'fe_connection_id': fe_connection_id_list,
            'fe_node_id': fe_connection_fe_node_id_list,
            'fe_elem_id': fe_connection_fe_elem_id_list,
            'fe_node_order': fe_connection_fe_node_order,
            'thickness': fe_connection_thickness_list,
        }
        fe_connection = pd.DataFrame.from_dict(fe_connection_dict, orient='columns').set_index('fe_connection_id')

        structural_model = {
            'fe_node': fe_node,
            'fe_elem': fe_elem,
            'fe_connection': fe_connection,
        }
        return structural_model

    def _create_custom_plate(self) -> dict:
        """Create custom plate model.

        Returns:
            A dict containing node, element and connection values between nodes and elements of created model.
        """
        width_divide_num = len(self.cfg['X_ARRAY']) - 1
        height_divide_num = len(self.cfg['Y_ARRAY']) - 1
        youngs_modulus = float(self.cfg['YOUNGS_MODULUS'])
        poissons_ratio = float(self.cfg['POISSONS_RATIO'])
        thickness = float(self.cfg['THICKNESS'])
        r3 = float(self.cfg['R3'])
        elem_type = self.cfg['ELEM_TYPE']
        each_elem_node_num = int(self.cfg['NODE_NUM'])
        if each_elem_node_num != 4:
            raise Exception(f'node_num = {each_elem_node_num} is unsupported value.')
        # Create fe_node.
        node_num = (width_divide_num + 1) * (height_divide_num + 1)
        fe_node_fe_node_id = np.arange(1, node_num + 1)
        fe_node_x_pos = np.tile(self.cfg['X_ARRAY'], height_divide_num + 1)
        fe_node_y_pos = np.repeat(self.cfg['Y_ARRAY'], width_divide_num + 1)
        fe_node_z_pos = np.zeros(node_num)
        fe_node_dict = {
            'fe_node_id': fe_node_fe_node_id,
            'x': fe_node_x_pos,
            'y': fe_node_y_pos,
            'z': fe_node_z_pos,
        }
        fe_node = pd.DataFrame.from_dict(fe_node_dict, orient='columns').set_index('fe_node_id')
        # Create fe_elem.
        elem_num = width_divide_num * height_divide_num
        fe_elem_fe_elem_id = np.arange(1, elem_num + 1)
        fe_elem_elem_type = np.full(elem_num, elem_type)
        fe_elem_fe_node_num = np.full(elem_num, each_elem_node_num)
        fe_elem_r3 = np.full(elem_num, r3)
        fe_elem_youngs_modulus = np.full(elem_num, youngs_modulus)
        fe_elem_poissons_ratio = np.full(elem_num, poissons_ratio)
        fe_elem_dict = {
            'fe_elem_id': fe_elem_fe_elem_id,
            'elem_type': fe_elem_elem_type,
            'node_num': fe_elem_fe_node_num,
            'r3': fe_elem_r3,
            'youngs_modulus': fe_elem_youngs_modulus,
            'poissons_ratio': fe_elem_poissons_ratio,
        }
        fe_elem = pd.DataFrame.from_dict(fe_elem_dict, orient='columns').set_index('fe_elem_id')
        # Create fe_connection.
        fe_connection_id_list = []
        fe_connection_fe_node_id_list = []
        fe_connection_fe_elem_id_list = []
        fe_connection_fe_node_order = []
        fe_connection_thickness_list = []
        node_addjust_num = 0
        columns_count = 0
        for i in range(width_divide_num * height_divide_num):
            columns_count += 1
            if (columns_count > width_divide_num):
                node_addjust_num += 1
                columns_count = 1
            fe_connection_id_list.extend([4*i+1, 4*i+2, 4*i+3, 4*i+4])
            fe_connection_fe_node_id_list.extend([
                node_addjust_num * (width_divide_num + 1) + columns_count,
                node_addjust_num * (width_divide_num + 1) + columns_count + 1,
                (node_addjust_num + 1) * (width_divide_num + 1) + columns_count + 1,
                (node_addjust_num + 1) * (width_divide_num + 1) + columns_count])
            fe_connection_fe_elem_id_list.extend([i + 1, i + 1, i + 1, i + 1])
            fe_connection_fe_node_order.extend([1, 2, 3, 4])
            fe_connection_thickness_list.extend(
                [thickness, thickness, thickness, thickness])
        fe_connection_dict = {
            'fe_connection_id': fe_connection_id_list,
            'fe_node_id': fe_connection_fe_node_id_list,
            'fe_elem_id': fe_connection_fe_elem_id_list,
            'fe_node_order': fe_connection_fe_node_order,
            'thickness': fe_connection_thickness_list,
        }
        fe_connection = pd.DataFrame.from_dict(fe_connection_dict, orient='columns').set_index('fe_connection_id')

        structural_model = {
            'fe_node': fe_node,
            'fe_elem': fe_elem,
            'fe_connection': fe_connection,
        }
        return structural_model

    def _create_cuboid(self) -> dict:
        """Create cuboid model.

        Returns:
            dict: A dict containing node, element and connection values between nodes and elements of created model.
        """
        width_divide_num = int(self.cfg['WIDTH_DIVIDE_NUM'])
        height_divide_num = int(self.cfg['HEIGHT_DIVIDE_NUM'])
        depth_divide_num = int(self.cfg['DEPTH_DIVIDE_NUM'])
        width = float(self.cfg['WIDTH'])
        height = float(self.cfg['HEIGHT'])
        depth = float(self.cfg['DEPTH'])
        elem_width = width / width_divide_num
        elem_height = height / height_divide_num
        elem_depth = depth / depth_divide_num
        youngs_modulus = float(self.cfg['YOUNGS_MODULUS'])
        poissons_ratio = float(self.cfg['POISSONS_RATIO'])
        r3 = float(self.cfg['R3'])
        elem_type = self.cfg['ELEM_TYPE']
        each_elem_node_num = int(self.cfg['NODE_NUM'])
        if each_elem_node_num != 8:
            raise Exception(f'node_num = {each_elem_node_num} is unsupported value.')
        # Create fe_node.
        node_num = (width_divide_num + 1) * (height_divide_num + 1) * (depth_divide_num + 1)
        fe_node_fe_node_id = np.arange(1, node_num + 1)
        fe_node_x_pos = np.tile(
            np.arange(0, width+elem_width/10, elem_width), (height_divide_num + 1) * (depth_divide_num + 1))
        fe_node_y_pos = np.tile(
            np.repeat(
                np.arange(0, height+elem_height/10, elem_height), width_divide_num + 1), depth_divide_num + 1)
        fe_node_z_pos = np.repeat(
            np.arange(0, depth + 1, elem_depth), (width_divide_num + 1) * (height_divide_num + 1))
        fe_node_dict = {
            'fe_node_id': fe_node_fe_node_id,
            'x': fe_node_x_pos,
            'y': fe_node_y_pos,
            'z': fe_node_z_pos,
        }
        fe_node = pd.DataFrame.from_dict(fe_node_dict, orient='columns').set_index('fe_node_id')
        # Create fe_elem.
        elem_num = width_divide_num * height_divide_num * depth_divide_num
        fe_elem_fe_elem_id = np.arange(1, elem_num + 1)
        fe_elem_elem_type = np.full(elem_num, elem_type)
        fe_elem_fe_node_num = np.full(elem_num, each_elem_node_num)
        fe_elem_r3 = np.full(elem_num, r3)
        fe_elem_youngs_modulus = np.full(elem_num, youngs_modulus)
        fe_elem_poissons_ratio = np.full(elem_num, poissons_ratio)
        fe_elem_dict = {
            'fe_elem_id': fe_elem_fe_elem_id,
            'elem_type': fe_elem_elem_type,
            'node_num': fe_elem_fe_node_num,
            'r3': fe_elem_r3,
            'youngs_modulus': fe_elem_youngs_modulus,
            'poissons_ratio': fe_elem_poissons_ratio,
        }
        fe_elem = pd.DataFrame.from_dict(fe_elem_dict, orient='columns').set_index('fe_elem_id')
        # Create fe_connection.
        surface_node_num = (width_divide_num+1) * (height_divide_num+1)
        surface_elem_num = width_divide_num * height_divide_num
        fe_connection_id = np.arange(1, 8*elem_num+1)
        fe_connection_fe_node_id = []
        fe_connection_fe_elem_id = np.repeat(np.arange(1, elem_num+1), each_elem_node_num)
        fe_connection_fe_node_order = np.tile(np.arange(1, each_elem_node_num+1), elem_num)
        fe_connection_thickness = np.full(8*elem_num, elem_depth)
        for j in range(depth_divide_num):
            node_addjust_num = 0
            columns_count = 0
            for i in range(surface_elem_num):
                columns_count += 1
                if (columns_count > width_divide_num):
                    node_addjust_num += 1
                    columns_count = 1
                fe_connection_fe_node_id.extend([
                    surface_node_num*j+node_addjust_num * (width_divide_num+1) + columns_count,
                    surface_node_num*j+node_addjust_num * (width_divide_num+1) + columns_count + 1,
                    surface_node_num*j+(node_addjust_num+1) * (width_divide_num+1) + columns_count + 1,
                    surface_node_num*j+(node_addjust_num+1) * (width_divide_num+1) + columns_count,
                    surface_node_num*(j+1) + node_addjust_num * (width_divide_num+1) + columns_count,
                    surface_node_num*(j+1) + node_addjust_num * (width_divide_num+1) + columns_count + 1,
                    surface_node_num*(j+1) + (node_addjust_num+1) * (width_divide_num+1) + columns_count + 1,
                    surface_node_num*(j+1) + (node_addjust_num+1) * (width_divide_num+1) + columns_count])
        fe_connection_dict = {
            'fe_connection_id': fe_connection_id,
            'fe_node_id': fe_connection_fe_node_id,
            'fe_elem_id': fe_connection_fe_elem_id,
            'fe_node_order': fe_connection_fe_node_order,
            'thickness': fe_connection_thickness,
        }
        fe_connection = pd.DataFrame.from_dict(fe_connection_dict, orient='columns').set_index('fe_connection_id')

        structural_model = {
            'fe_node': fe_node,
            'fe_elem': fe_elem,
            'fe_connection': fe_connection,
        }
        return structural_model

    def _create_pipe(self) -> dict:
        """Create pipe model.

        Returns:
            A dict containing node, element and connection values between nodes and elements of created model.
        """
        longitudinal_length = float(self.cfg['LONGITUDINAL_LENGTH'])
        thickness = float(self.cfg['THICKNESS'])
        longitudinal_divide_num = int(self.cfg['LONGITUDINAL_DIVIDE_NUM'])
        longitudinal_divide_length = longitudinal_length / longitudinal_divide_num
        youngs_modulus = float(self.cfg['YOUNGS_MODULUS'])
        poissons_ratio = float(self.cfg['POISSONS_RATIO'])
        r3 = float(self.cfg['R3'])
        elem_type = self.cfg['ELEM_TYPE']
        each_elem_node_num = int(self.cfg['NODE_NUM'])
        if each_elem_node_num != 4:
            raise Exception(f'node_num = {each_elem_node_num} is unsupported value.')
        if self.cfg['CROSS_SECTION_SHAPE'] == 'circle':
            pipe_radius = float(self.cfg['PIPE_RADIUS'])
            cross_sect_divide_num = int(self.cfg['CROSS_SECTION_DIVIDE_NUM'])
            theta = 2 * np.pi / cross_sect_divide_num
        elif self.cfg['CROSS_SECTION_SHAPE'] == 'rectangle':
            pipe_y_length = float(self.cfg['y_length'])
            pipe_z_length = float(self.cfg['z_length'])
            pipe_y_divide_num = int(self.cfg['y_divide_num'])
            pipe_z_divide_num = int(self.cfg['z_divide_num'])
            cross_sect_divide_num = pipe_y_divide_num * 2 + pipe_z_divide_num * 2
        else:
            pipe_cross_shape = self.cfg['CROSS_SECTION_SHAPE']
            raise Exception(f'{pipe_cross_shape} is unsupported value.')
        # Create fe_node.
        node_num = (longitudinal_divide_num + 1) * cross_sect_divide_num
        fe_node_fe_node_id = np.arange(1, node_num + 1)
        fe_node_x_pos = np.repeat(
            np.arange(0, longitudinal_length+longitudinal_divide_length/10, longitudinal_divide_length),
            cross_sect_divide_num
            )
        if self.cfg['CROSS_SECTION_SHAPE'] == 'circle':
            fe_node_y_cross = []
            fe_node_z_cross = []
            for i in range(cross_sect_divide_num):
                fe_node_y_cross.append(pipe_radius*np.cos(i*theta))
                fe_node_z_cross.append(pipe_radius*np.sin(i*theta))
        elif self.cfg['CROSS_SECTION_SHAPE'] == 'rectangle':
            each_elem_y_length = pipe_y_length / pipe_y_divide_num
            each_elem_z_length = pipe_z_length / pipe_z_divide_num
            fe_node_y_1 = np.arange(pipe_y_length/2, -pipe_y_length/2, -each_elem_y_length)
            fe_node_y_2 = np.full(pipe_z_divide_num, -pipe_y_length/2)
            fe_node_y_3 = np.arange(-pipe_y_length/2, pipe_y_length/2, each_elem_y_length)
            fe_node_y_4 = np.full(pipe_z_divide_num, pipe_y_length/2)
            fe_node_y_cross = np.hstack([fe_node_y_1, fe_node_y_2, fe_node_y_3, fe_node_y_4])
            fe_node_z_1 = np.full(pipe_y_divide_num, pipe_z_length/2)
            fe_node_z_2 = np.arange(pipe_z_length/2, -pipe_z_length/2, -each_elem_z_length)
            fe_node_z_3 = np.full(pipe_y_divide_num, -pipe_z_length/2)
            fe_node_z_4 = np.arange(-pipe_z_length/2, pipe_z_length/2, each_elem_z_length)
            fe_node_z_cross = np.hstack([fe_node_z_1, fe_node_z_2, fe_node_z_3, fe_node_z_4])
        fe_node_y_pos = np.tile(fe_node_y_cross, longitudinal_divide_num + 1)
        fe_node_z_pos = np.tile(fe_node_z_cross, longitudinal_divide_num + 1)
        fe_node_dict = {
            'fe_node_id': fe_node_fe_node_id,
            'x': fe_node_x_pos,
            'y': fe_node_y_pos,
            'z': fe_node_z_pos,
        }
        fe_node = pd.DataFrame.from_dict(fe_node_dict, orient='columns').set_index('fe_node_id')
        # Create fe_elem.
        elem_num = longitudinal_divide_num * cross_sect_divide_num
        fe_elem_fe_elem_id = np.arange(1, elem_num + 1)
        fe_elem_elem_type = np.full(elem_num, elem_type)
        fe_elem_fe_node_num = np.full(elem_num, each_elem_node_num)
        fe_elem_r3 = np.full(elem_num, r3)
        fe_elem_youngs_modulus = np.full(elem_num, youngs_modulus)
        fe_elem_poissons_ratio = np.full(elem_num, poissons_ratio)
        fe_elem_dict = {
            'fe_elem_id': fe_elem_fe_elem_id,
            'elem_type': fe_elem_elem_type,
            'node_num': fe_elem_fe_node_num,
            'r3': fe_elem_r3,
            'youngs_modulus': fe_elem_youngs_modulus,
            'poissons_ratio': fe_elem_poissons_ratio,
        }
        fe_elem = pd.DataFrame.from_dict(fe_elem_dict, orient='columns').set_index('fe_elem_id')
        # Create fe_connection.
        fe_connection_id = np.arange(1, each_elem_node_num*elem_num+1)
        fe_connection_fe_node_id = []
        fe_connection_fe_elem_id = np.repeat(np.arange(1, elem_num+1), each_elem_node_num)
        fe_connection_fe_node_order = np.tile(np.arange(1, each_elem_node_num+1), elem_num)
        fe_connection_thickness = np.full(each_elem_node_num*elem_num, thickness)
        for j in range(longitudinal_divide_num):
            for i in range(cross_sect_divide_num):
                if i != cross_sect_divide_num - 1:
                    fe_connection_fe_node_id.extend([
                        j*cross_sect_divide_num + i + 1,
                        j*cross_sect_divide_num + i + 2,
                        (j+1)*cross_sect_divide_num + i + 2,
                        (j+1)*cross_sect_divide_num + i + 1
                    ])
                else:
                    fe_connection_fe_node_id.extend([
                        (j+1)*cross_sect_divide_num,
                        j*cross_sect_divide_num + 1,
                        (j+1)*cross_sect_divide_num + 1,
                        (j+2)*cross_sect_divide_num
                    ])
        fe_connection_dict = {
            'fe_connection_id': fe_connection_id,
            'fe_node_id': fe_connection_fe_node_id,
            'fe_elem_id': fe_connection_fe_elem_id,
            'fe_node_order': fe_connection_fe_node_order,
            'thickness': fe_connection_thickness,
        }
        fe_connection = pd.DataFrame.from_dict(fe_connection_dict, orient='columns').set_index('fe_connection_id')

        structural_model = {
            'fe_node': fe_node,
            'fe_elem': fe_elem,
            'fe_connection': fe_connection,
        }
        return structural_model
