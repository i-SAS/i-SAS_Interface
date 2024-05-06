from datetime import datetime

import numpy as np
import pandas as pd
from isas_base.data import DynamicData
from isas_base.data.dynamic_data.time_series_batch_metadata import (
    TimeSeriesBatchDependencies, TimeSeriesBatchMetadata
)
from isas_base.data.dynamic_data.time_series_data import TimeSeriesData


def generate_tag(
        service_name: str,
        ) -> dict[str, str | datetime]:
    """Generate tag for dynamic data.

    Args:
        service_name: A name of the service.

    Returns:
        A tag for this batch.
    """
    batch_datetime = datetime.now()
    return {
        'batch_id': f'{service_name}_{batch_datetime}',
        'service_name': service_name,
        'batch_datetime': batch_datetime,
        }


def arrange_result(
        res: dict[str, pd.DataFrame],
        tag: dict[str, str | datetime] | None = None,
        ) -> DynamicData:
    """Arrange result of model.

    Args:
        res: result of model.
        tag: A tag for this batch.

    Returns
        An instance of DynamicData including the result.
    """
    ns = datetime.now()
    time_series_data = {}
    for data_name, df in res.items():
        if df is None:
            continue
        if not pd.api.types.is_datetime64_dtype(df.index):
            df = df.set_axis([ns]*len(df), axis='index', copy=False)
        df = df.set_axis(np.arange(1, df.shape[1]+1), axis='columns', copy=False)
        df.index.name = 'time'
        if tag is not None:
            tag = pd.DataFrame(tag, index=df.index).convert_dtypes()
        time_series_data[data_name] = TimeSeriesData(df, tag)
    return DynamicData(time_series_data=time_series_data)


def get_dependencies(
        dynamic_data: DynamicData,
        tag: dict[str, str | datetime],
        ) -> list[str]:
    """Get dependencies of the time-series batch.

    Args:
        dynamic_data: Dynamic data of the batch.
        tag: A tag for the batch.

    Returns:
        A list of dependent batch_id.
    """
    dependent_batch_id = []
    for key, time_series_data in dynamic_data.time_series_data.items():
        if 'batch_id' not in time_series_data.tags.columns:
            continue
        unique_tag = time_series_data.tags['batch_id'].drop_duplicates().tolist()
        dependent_batch_id.extend(unique_tag)
    dependent_batch_id = list(set(dependent_batch_id) - {tag['batch_id']})
    return dependent_batch_id


def generate_time_series_batch_metadata(
        tag: dict[str, str | datetime],
        dependent_batch_id: list[str],
        ) -> DynamicData:
    """Generate metadata on the time-series batch.

    Args:
        tag: A tag for the batch.
        dependent_batch_id: A list of dependent batch_id.

    Returns:
        An instance of DynamicData including metadata.
    """
    return DynamicData(time_series_batch_metadata={
        tag['batch_id']: TimeSeriesBatchMetadata(
            service_name=tag['service_name'],
            batch_datetime=tag['batch_datetime'],
            dependencies={
                batch_id: TimeSeriesBatchDependencies()
                for batch_id in dependent_batch_id
                }
        )
        })
