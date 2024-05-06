import importlib

from isas_base.data import StaticData


def create_static_data(
        preprocess_cfg: dict,
        static_data: StaticData | None = None,
        ) -> StaticData:
    """Create sensor and structural model data.

    Args:
        preprocess_cfg: User-defined config dict to create sensor and structural model.
        static_data: An instance of StaticData.

    Returns:
        An isntacne of StaticData.
    """
    sensors = {}
    structural_models = {}
    static_data = StaticData() if static_data is None else static_data
    for cfg in preprocess_cfg:
        task = cfg['TASK']
        module = importlib.import_module(f'isas.preprocess.{task}', cfg['METHOD'])
        func = getattr(module, cfg['METHOD'])
        args = (cfg['CFG'], )
        if cfg['METHOD'] == 'create_sensor_structural_model_connection':
            args = (
                cfg['CFG'],
                static_data.sensors[cfg['NAME']],
                cfg['STRUCTURAL_MODEL_NAME'],
                static_data.structural_models[cfg['STRUCTURAL_MODEL_NAME']]
                )
        elif cfg['METHOD'] in (
                'convert_finite_element_model',
                'convert_graph_model',
                'convert_point_cloud_model',
                ):
            args = (
                cfg['CFG'],
                static_data.structural_models[cfg['STRUCTURAL_MODEL_NAME']]
                )
        data = func(*args)
        if task == 'sensor_modeling':
            sensors.update({cfg['NAME']: data})
        elif task == 'structural_modeling':
            structural_models.update({cfg['NAME']: data})
        else:
            raise ValueError(f'Unsupported task: {task}')
        static_data.update(StaticData(sensors=sensors, structural_models=structural_models))
    return static_data
