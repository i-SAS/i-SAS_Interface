from pathlib import Path

import numpy as np
import pandas as pd
from isas_base.data.static_data.structural_model import FiniteElementModel
from isas_base.utils import get_cfg


def import_finite_element_model(
        cfg: dict
        ) -> FiniteElementModel:
    """Import finite element model.

    Args:
        cfg: Structural model config.

    Returns:
        An instance of structural model.
    """
    importer = FiniteElementModelImporter(cfg)
    return importer()


class FiniteElementModelImporter:
    DEFAULT_CFG = {
        'FILE_PATH': None,
        'DATA_FORMAT': None,
        }
    DATA_FORMATS = {'nastran'}
    ELEM_TYPES = {3: 'shell_T1', 4: 'iQS4'}

    def __init__(
            self,
            cfg: dict,
            ) -> None:
        """Initialize FiniteElementModelImporter.

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
        if cfg['DATA_FORMAT'] not in self.DATA_FORMATS:
            raise ValueError(
                f'{cfg["data_format"]} is not supported as a data format. {self.DATA_FORMATS} are supported.'
                )

    def __call__(self) -> FiniteElementModel:
        """Import FiniteElementModel.

        Returns:
            An instance of FiniteElementModel.
        """
        importer = {
            'nastran': self._import_nastran_model,
            }
        return FiniteElementModel(
            **importer[self.cfg['DATA_FORMAT']]()
            )

    def _import_nastran_model(self) -> dict:
        """Import shell FiniteElementModel from nastran bulk data file.

        Returns
            A dict containing node, element and connection values between nodes and elements of created model.
        """
        with Path(self.cfg['FILE_PATH']).open('r') as f:
            model_data = f.readlines()

        # Import case config
        config_dict = dict()
        for row in model_data:
            if 'SPC' in row and '=' in row:
                config_dict['SPC'] = int(row.replace('SPC', '').replace('=', ''))
            elif 'BEGIN BULK' in row:
                break

        # Import constraint data
        constraint_dict = dict()
        for _ in range(0, len(model_data)):
            if model_data[_][:6] == 'SUPORT':
                # constraint for inertia relief
                row = model_data[_]
                splitter = ',' if ',' in row else ''
                constraint_dict[int(row.split(splitter)[1])] = dict()
                for i in range(len(str(int(row.split(splitter)[2])))):
                    constraint_dict[int(row.split(splitter)[1])][str(int(row.split(splitter)[2]))[i]] = 0
            elif model_data[_][:6] == 'SPC1  ':
                # single point constraint
                row = model_data[_]
                for i in range(3, len(row.split())):
                    constraint_dict[int(row.split()[i])] = dict()
                    for j in range(len(str(int(row.split()[2])))):
                        constraint_dict[int(row.split()[i])][str(int(row.split()[2]))[j]] = 0
            elif model_data[_][:6] == 'SPC   ' or model_data[_][:6] == 'SPCD  ':
                # single point constraint / alternate form
                row = model_data[_]
                for i in range(0, 1+len(row.split())//6):
                    constraint_dict[int(row[16+i*24:24+i*24])] = dict()
                    enforced_disp = 0 if row[32+i*24:40+i*24] == ' '*8 else float(row[32+i*24:40+i*24])
                    for j in range(len(str(int(row[24+i*24:32+i*24])))):
                        constraint_dict[int(row[16+i*24:24+i*24])][str(int(row[24+i*24:32+i*24]))[j]] = enforced_disp

        # Import Shell Data
        shell_dict = dict()
        for _ in range(0, len(model_data)):
            if model_data[_][:6] == 'PSHELL':
                # Shell
                row = model_data[_]
                shell_property = {
                    'material': self._float_conv(row[16:24]),
                    'thickness': self._float_conv(row[24:32])
                }
                shell_dict[self._float_conv(row[8:16])] = shell_property
            elif model_data[_][:5] == 'PCOMP':
                # Layered composite shell
                # Todo: import materials and thichnesses for each plies
                row = model_data[_]
                row_2 = model_data[_+1]
                assert set(row_2[:8]) == set(' ') and set(row_2[8:16]) != set(' '), \
                    'First material id is required for PCOMP card.'
                shell_property = {
                    'material': self._float_conv(row_2[8:16]),
                    'thickness': 2*abs(self._float_conv(row[16:24]))
                }
                shell_dict[self._float_conv(row[8:16])] = shell_property

        # Import Material Data
        mat_dict = dict()
        for _ in range(0, len(model_data)):
            if model_data[_][0:5] == 'MAT1 ':
                # Isotropic Material
                row = model_data[_]
                mat_property = dict({
                    'youngs_modulus': self._float_conv(row[16:24]),
                    'poissons_ratio': self._float_conv(row[32:40]),
                    'density': self._float_conv(row[40:48]),
                    'yield_stress': np.nan
                })
                mat_dict[self._float_conv(row[8:16])] = mat_property
            elif model_data[_][0:5] == 'MAT1*':
                # Isotropic Material / alternate form
                row_1 = model_data[_]
                row_2 = model_data[_+1]
                mat_property = dict({
                    'youngs_modulus': self._float_conv(row_1[24:40]),
                    'poissons_ratio': self._float_conv(row_1[56:64]),
                    'density': self._float_conv(row_2[8:16]),
                    'yield_stress': np.nan
                })
                mat_dict[self._float_conv(row_1[8:16])] = mat_property
            elif model_data[_][0:5] == 'MAT2 ':
                # Anisotropic Material
                row = model_data[_]
                mat_property = dict({
                    'g11': self._float_conv(row[16:24]),
                    'g12': self._float_conv(row[24:32]),
                    'g13': self._float_conv(row[32:40]),
                    'g22': self._float_conv(row[40:48]),
                    'g23': self._float_conv(row[48:56]),
                    'g33': self._float_conv(row[56:64]),
                    'density': self._float_conv(row[64:72]),
                    'yield_stress': np.nan
                })
                mat_dict[self._float_conv(row[8:16])] = mat_property
            elif model_data[_][0:5] == 'MAT8 ':
                # Orthotropic Material
                row = model_data[_]
                mat_property = dict({
                    'youngs_modulus_1': self._float_conv(row[16:24]),
                    'youngs_modulus_2': self._float_conv(row[24:32]),
                    'poissons_ratio': self._float_conv(row[32:40]),
                    'density': self._float_conv(row[64:72]),
                    'yield_stress': np.nan
                })
                mat_dict[self._float_conv(row[8:16])] = mat_property

        # Import Node and Element Data
        node_data = []
        elem_data = []
        for _ in range(0, len(model_data)):
            if model_data[_][:5] == 'GRID ':
                # Node coordinates
                row = model_data[_]
                node_data.append([
                    int(row[8:16]),
                    self._float_conv(row[24:32]),
                    self._float_conv(row[32:40]),
                    self._float_conv(row[40:48])
                ])
            elif model_data[_][:5] == 'GRID*':
                # Node coordinates (multiple lines)
                row1 = model_data[_].split()
                row2 = model_data[_+1].split()
                node_data.append([
                    int(row1[1]),
                    self._float_conv(row1[2]),
                    self._float_conv(row1[3]),
                    self._float_conv(row2[1])
                ])

            if model_data[_][:7] == 'CQUAD4*':
                # Quadrilateral Plate Element (multiple lines)
                row1 = model_data[_].split()
                row2 = model_data[_+1].split()
                shell = shell_dict[self._float_conv(row1[2])]
                elem_data.append([
                    int(row1[1]), int(row1[3]), int(row1[4]), int(row2[1]), int(row2[2]),
                    shell['thickness'], int(0),
                    mat_dict[shell['material']]['youngs_modulus'],
                    mat_dict[shell['material']]['poissons_ratio'],
                    mat_dict[shell['material']]['density'],
                    mat_dict[shell['material']]['yield_stress']
                ])
            elif model_data[_][:7] == 'CQUAD4 ':
                # Quadrilateral Plate Element
                row = model_data[_].split()
                shell = shell_dict[self._float_conv(row[2])]
                elem_data.append([
                    int(row[1]), int(row[3]), int(row[4]), int(row[5]), int(row[6]),
                    shell['thickness'], int(0),
                    mat_dict[shell['material']]['youngs_modulus'],
                    mat_dict[shell['material']]['poissons_ratio'],
                    mat_dict[shell['material']]['density'],
                    mat_dict[shell['material']]['yield_stress']
                ])
            elif model_data[_][:7] == 'CTRIA3 ':
                # Triangular Element
                row = model_data[_].split()
                shell = shell_dict[self._float_conv(row[2])]
                elem_data.append([
                    int(row[1]), int(row[3]), int(row[4]), int(row[5]), int(row[5]),
                    shell['thickness'], int(0),
                    mat_dict[shell['material']]['youngs_modulus'],
                    mat_dict[shell['material']]['poissons_ratio'],
                    mat_dict[shell['material']]['density'],
                    mat_dict[shell['material']]['yield_stress']
                ])

        node_data = np.array(node_data)
        node_data = node_data[np.argsort(node_data[:, 0])]
        elem_data = np.array(elem_data)
        elem_data = elem_data[np.argsort(elem_data[:, 0])]

        _ = elem_data[:, 1:5]
        remove = [True if node_data[i, 0] in _ else False for i in range(0, len(node_data))]
        node_data = node_data[remove]

        node_id = node_data[:, 0].copy()
        node_data[:, 0] = np.arange(1, len(node_data)+1)
        # Convert node_id and elem_id to serial numbers.
        node_dict = dict(zip(node_id.astype('int32'), node_data[:, 0].astype('int32')))
        elem_data[:, 0] = np.arange(1, len(elem_data)+1)
        for i in range(0, len(elem_data)):
            for j in range(1, 5):
                elem_data[i, j] = node_dict[int(elem_data[i, j])]

        _node_num = np.array(list(map(lambda x: len(np.unique(x)), elem_data[:, 1:5])))
        _elem_type = np.array(list(map(lambda x: self.ELEM_TYPES[x], _node_num)))

        # Import constraint data
        constraint_dict = dict()
        for _ in range(0, len(model_data)):
            if model_data[_][:6] == 'SUPORT':
                # point constraint for inertia relief
                row = model_data[_]
                splitter = ',' if ',' in row else ''
                constraint_dict[node_dict[int(row.split(splitter)[1])]] = dict()
                for i in range(len(str(int(row.split(splitter)[2])))):
                    constraint_dict[node_dict[int(row.split(splitter)[1])]][str(int(row.split(splitter)[2]))[i]] = 0
            elif model_data[_][:6] == 'SPC1  ':
                # single point constraint
                k = 0
                while k == 0 or model_data[_+k][:8] == ' '*8:
                    if k > 0 and model_data[_+k][8:16] == ' '*8:
                        break
                    row = model_data[_+k]

                    if k == 0 and int(row.split()[1]) != config_dict['SPC']:
                        continue
                    else:
                        if k == 0:
                            dof = str(int(model_data[_].split()[2]))
                        start = 3 if k == 0 else 0
                        for i in range(start, len(row.split())):
                            constraint_dict[node_dict[int(row.split()[i])]] = dict()
                            for j in range(len(dof)):
                                constraint_dict[node_dict[int(row.split()[i])]][dof[j]] = 0
                    k += 1
            elif model_data[_][:6] == 'SPC   ' or model_data[_][:6] == 'SPCD  ':
                # single point constraint / alternate form  &  enforced displacement
                row = model_data[_]
                if row[:6] == 'SPC   ' and int(row.split()[1]) != config_dict['SPC']:
                    continue
                if row[:6] == 'SPCD  ' and int(row.split()[1]) != config_dict['LOAD']:
                    continue
                for i in range(0, 1+len(row.split())//6):
                    if int(row[16+i*24:24+i*24]) not in constraint_dict.keys():
                        constraint_dict[node_dict[int(row[16+i*24:24+i*24])]] = dict()
                    enforced_disp = 0 if row[32+i*24:40+i*24] == ' '*8 else float(row[32+i*24:40+i*24])
                    for j in range(len(str(int(row[24+i*24:32+i*24])))):
                        constraint_dict[node_dict[int(row[16+i*24:24+i*24])]][str(int(row[24+i*24:32+i*24]))[j]] \
                            = enforced_disp

        # create fe_node, fe_elem, fe_connection
        fe_node = pd.DataFrame(node_data, columns=['fe_node_id', 'x', 'y', 'z'])
        fe_node = fe_node.astype({'fe_node_id': 'int32', 'x': 'float32', 'y': 'float32', 'z': 'float32'})
        fe_node = fe_node.set_index('fe_node_id')

        fe_elem = np.hstack([
            elem_data[:, 0].reshape((-1, 1)).astype('int32'),
            _elem_type.reshape((-1, 1)),
            _node_num.reshape((-1, 1)).astype('int32'),
            elem_data[:, 6].reshape((-1, 1)).astype('int32'),
            elem_data[:, 7:10].astype('float32')
        ])
        fe_elem = pd.DataFrame(fe_elem, columns=[
            'fe_elem_id', 'elem_type', 'node_num',
            'r3', 'youngs_modulus', 'poissons_ratio', 'density'
        ])
        fe_elem = fe_elem.astype({
            'fe_elem_id': 'int32', 'elem_type': 'str', 'node_num': 'int32',
            'r3': 'int32', 'youngs_modulus': 'float32', 'poissons_ratio': 'float32', 'density': 'float32'
        })
        fe_elem = fe_elem.set_index('fe_elem_id')

        _fe_node_id = elem_data[:, 1:5].ravel()
        _fe_elem_id = np.repeat(elem_data[:, 0], 4)
        _fe_node_order = np.tile([1, 2, 3, 4], len(elem_data))
        _thickness = np.repeat(elem_data[:, 5], 4)
        fe_connection = np.hstack([
            _fe_node_id.reshape((-1, 1)),
            _fe_elem_id.reshape((-1, 1)),
            _fe_node_order.reshape((-1, 1)),
            _thickness.reshape((-1, 1)),
        ])
        indexes = np.unique(fe_connection[:, [0, 1, 3]], axis=0, return_index=True)[1]
        fe_connection = np.array([fe_connection[index] for index in sorted(indexes)])
        fe_connection = np.hstack([
            np.arange(1, len(fe_connection)+1).reshape((-1, 1)),
            fe_connection
        ])
        fe_connection = pd.DataFrame(fe_connection, columns=[
            'fe_connection_id', 'fe_node_id', 'fe_elem_id', 'fe_node_order', 'thickness',
        ])
        fe_connection = fe_connection.astype({
            'fe_connection_id': 'int32',
            'fe_node_id': 'int32',
            'fe_elem_id': 'int32',
            'fe_node_order': 'int32',
            'thickness': 'float32',
        })
        fe_connection = fe_connection.set_index('fe_connection_id')

        structural_model = {
            'fe_node': fe_node,
            'fe_elem': fe_elem,
            'fe_connection': fe_connection,
        }

        dof_dict = {'1': 'x', '2': 'y', '3': 'z', '4': 'rotation_x', '5': 'rotation_y', '6': 'rotation_z'}
        constraint_nodes = list(constraint_dict.keys())
        if len(constraint_nodes) >= 1:
            fe_constraint = []
            for i in range(len(constraint_nodes)):
                constraint_dof = constraint_dict[constraint_nodes[i]]
                for j in range(len(constraint_dict[constraint_nodes[i]])):
                    fe_constraint.append([
                        constraint_nodes[i],
                        'global',
                        dof_dict[list(constraint_dict[constraint_nodes[i]].keys())[j]],
                        constraint_dof[list(constraint_dof.keys())[j]]
                    ])
            fe_constraint = np.hstack([np.arange(1, len(fe_constraint)+1).reshape((-1, 1)), np.array(fe_constraint)])
            fe_constraint = pd.DataFrame(fe_constraint, columns=[
                'fe_constraint_id', 'fe_node_id', 'coord_sys', 'component', 'constraint'
            ])
            fe_constraint = fe_constraint.astype({
                'fe_constraint_id': 'int32', 'fe_node_id': 'int32',
                'coord_sys': 'str', 'component': 'str', 'constraint': 'float32'
            })
            fe_constraint = fe_constraint.set_index('fe_constraint_id')
            structural_model['fe_constraint'] = fe_constraint
        return structural_model

    @staticmethod
    def _float_conv(num):
        """Convert string number to float.

        Args:
            num (str): String number.

        Returns:
            float: Float number.
        """
        if num[-1:] == '\n':
            num = num[:-1]
        try:
            num_ = float(num)
        except ValueError:
            if len(num.split()) == 0:
                return np.nan
            if '-' in num:
                ele = num.split('-')
                if ele[0] == '':
                    num_ = float('-'+ele[1]+'e-'+ele[2])
                else:
                    num_ = float(ele[0]+'e-'+ele[1])
            elif '+' in num:
                ele = num.split('+')
                if ele[0] == '':
                    num_ = float('+'+ele[1]+'e+'+ele[2])
                else:
                    num_ = float(ele[0]+'e+'+ele[1])
        return num_
