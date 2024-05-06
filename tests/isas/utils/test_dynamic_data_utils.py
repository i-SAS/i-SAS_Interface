import unittest
from datetime import datetime

import numpy as np
import pandas as pd
from isas_base.data import DynamicData
from isas_base.data.dynamic_data.time_series_batch_metadata import (
    TimeSeriesBatchDependencies, TimeSeriesBatchMetadata
)

from isas.utils.dynamic_data_utils import (
    arrange_result, generate_tag, generate_time_series_batch_metadata,
    get_dependencies
)


class TestDynamicDataUtils(unittest.TestCase):
    def test_generate_tag(self):
        service_name = 'test'
        dt_1 = datetime.now()
        tag = generate_tag(service_name)
        dt_2 = datetime.now()
        self.assertIsInstance(tag, dict)
        self.assertEqual(set(tag.keys()), {'batch_id', 'service_name', 'batch_datetime'})
        self.assertLessEqual(dt_1, tag['batch_datetime'])
        self.assertLessEqual(tag['batch_datetime'], dt_2)

    def test_arrange_result(self):
        tag = generate_tag('test')
        res = {'res': pd.DataFrame(np.arange(12).reshape(4, 3))}
        dynamic_data = arrange_result(res, tag)
        self.assertIsInstance(dynamic_data, DynamicData)
        self.assertEqual(set(dynamic_data.time_series_data.keys()), set(res.keys()))
        time_series_data = dynamic_data.time_series_data['res']
        df = time_series_data.fields
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (4, 3))
        self.assertEqual(df.index.name, 'time')
        self.assertTrue(pd.api.types.is_datetime64_dtype(df.index))
        self.assertTrue(pd.api.types.is_integer_dtype(df.columns))
        for _, series in df.items():
            self.assertTrue(pd.api.types.is_numeric_dtype(series))
        df = time_series_data.tags
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (4, 3))
        self.assertEqual(df.index.name, 'time')
        self.assertTrue(pd.api.types.is_datetime64_dtype(df.index))
        self.assertEqual(set(tag.keys()), set(df.columns))

    def test_get_dependencies(self):
        tag_1 = generate_tag('test')
        res_1 = {'res': pd.DataFrame(np.arange(12).reshape(4, 3))}
        dynamic_data = arrange_result(res_1, tag_1)
        dependent_batch_id = get_dependencies(dynamic_data, tag_1)
        self.assertIsInstance(dependent_batch_id, list)
        self.assertEqual(len(dependent_batch_id), 0)
        tag_2 = generate_tag('test')
        res_2 = {'res2': pd.DataFrame(np.arange(12).reshape(4, 3))}
        dynamic_data.update(arrange_result(res_2, tag_2))
        dependent_batch_id = get_dependencies(dynamic_data, tag_2)
        self.assertEqual(dependent_batch_id, [tag_1['batch_id']])

    def test_generate_time_series_batch_metadata(self):
        tag_1 = generate_tag('test')
        tag_2 = generate_tag('test')
        dependent_batch_id = [tag_1['batch_id']]
        dynamic_data = generate_time_series_batch_metadata(tag_2, dependent_batch_id)
        self.assertIsInstance(dynamic_data, DynamicData)
        self.assertEqual(set(dynamic_data.time_series_batch_metadata.keys()), {tag_2['batch_id']})
        for metadata in dynamic_data.time_series_batch_metadata.values():
            self.assertIsInstance(metadata, TimeSeriesBatchMetadata)
            self.assertEqual(metadata.service_name, tag_2['service_name'])
            self.assertEqual(metadata.batch_datetime, tag_2['batch_datetime'])
            self.assertIsInstance(metadata.dependencies, dict)
            self.assertEqual(set(metadata.dependencies.keys()), {tag_1['batch_id']})
            for _metadata in metadata.dependencies.values():
                self.assertIsInstance(_metadata, TimeSeriesBatchDependencies)
                self.assertIsNone(_metadata.id)


if __name__ == '__main__':
    unittest.main()
