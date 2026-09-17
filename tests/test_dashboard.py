"""Focused portfolio regressions. Run: python -m unittest discover -s tests -v"""
import ast
import contextlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache' / 'matplotlib'))
import pandas as pd
from streamlit.testing.v1 import AppTest
from dashboard.data import load_data, validate_data, kpis, comparable_models, presence_matrix


@contextlib.contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.models, self.brands, self.presence = load_data()

    def test_cardinality_and_snapshot_denominators(self):
        self.assertEqual(len(self.models), 8)
        self.assertEqual(len(self.brands), 7)
        self.assertEqual(len(self.presence), 28)
        self.assertEqual(kpis(self.models), {'models': 8, 'brands': 7, 'comparable': 4, 'range': 7})
        self.assertEqual(set(comparable_models(self.models).brand), {'BYD', 'Zeekr', 'XPeng', 'NIO'})
        self.assertEqual(int(self.presence.presence_status.eq('present').sum()), 7)
        self.assertEqual(int(self.presence.presence_status.eq('unknown').sum()), 21)
        self.assertEqual(presence_matrix(self.presence).shape, (7, 4))

    def test_invalid_columns_keys_and_semantics_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing columns'):
            validate_data(self.models.drop(columns='range_standard'), self.brands, self.presence)
        with self.assertRaisesRegex(ValueError, 'duplicate keys'):
            validate_data(self.models, pd.concat([self.brands, self.brands.iloc[:1]]), self.presence)
        with self.assertRaisesRegex(ValueError, 'duplicate keys'):
            validate_data(pd.concat([self.models, self.models.iloc[:1]]), self.brands, self.presence)
        broken = self.models.copy()
        broken.loc[0, 'battery_chemistry'] = 'EREV'
        with self.assertRaisesRegex(ValueError, 'Chemistry'):
            validate_data(broken, self.brands, self.presence)
        broken_presence = self.presence.copy()
        broken_presence.loc[broken_presence.presence_status.eq('present'), 'source_url'] = None
        with self.assertRaisesRegex(ValueError, 'Resolved presence'):
            validate_data(self.models, self.brands, broken_presence)

    def test_missing_prices_never_imputed(self):
        models = self.models.copy()
        models['price_eur'] = float('nan')
        self.assertTrue(comparable_models(models).empty)
        self.assertEqual(kpis(models)['comparable'], 0)
        self.assertTrue(models.price_eur.isna().all())
        with patch('dashboard.data.load_data', return_value=(models, self.brands, self.presence)):
            app = AppTest.from_file(str(ROOT / 'dashboard/app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[2].value, '0 / 8')
        self.assertTrue(app.info)

    def test_no_numeric_data_is_safe(self):
        models = self.models.copy()
        for column in ['price_eur', 'electric_range_km', 'battery_capacity_kwh', 'total_range_km']:
            models[column] = float('nan')
        validate_data(models, self.brands, self.presence)
        with patch('dashboard.data.load_data', return_value=(models, self.brands, self.presence)):
            app = AppTest.from_file(str(ROOT / 'dashboard/app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric], ['8', '7', '0 / 8', '0 / 8'])

    def test_every_brand_filter_and_denominator(self):
        expected = {
            'All': ['8', '7', '4 / 8', '7 / 8'],
            'BYD': ['2', '1', '1 / 2', '2 / 2'],
            'Jaecoo': ['1', '1', '0 / 1', '1 / 1'],
            'Li Auto': ['1', '1', '0 / 1', '0 / 1'],
            'NIO': ['1', '1', '1 / 1', '1 / 1'],
            'XPeng': ['1', '1', '1 / 1', '1 / 1'],
            'Xiaomi Auto': ['1', '1', '0 / 1', '1 / 1'],
            'Zeekr': ['1', '1', '1 / 1', '1 / 1'],
        }
        app = AppTest.from_file(str(ROOT / 'dashboard/app.py'), default_timeout=30).run()
        for brand, values in expected.items():
            with self.subTest(brand=brand):
                app.selectbox[0].select(brand).run()
                self.assertFalse(app.exception)
                self.assertEqual([m.value for m in app.metric], values)
                self.assertNotIn('nan', [m.value.lower() for m in app.metric])
                self.assertEqual(len(app.dataframe[0].value), int(values[0]))
                if brand != 'All':
                    self.assertEqual(set(app.dataframe[0].value.Brand), {brand})

    def test_paths_from_root_and_dashboard(self):
        for path in [ROOT, ROOT / 'dashboard']:
            with self.subTest(path=str(path)), working_directory(path):
                app = AppTest.from_file(str(ROOT / 'dashboard/app.py'), default_timeout=30).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, '8')

    def test_load_error_has_useful_message(self):
        with patch('dashboard.data.load_data', side_effect=ValueError('missing columns')):
            app = AppTest.from_file(str(ROOT / 'dashboard/app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertIn('Cannot load the portfolio data', app.error[0].value)

    def test_retired_metrics_and_no_cross_standard_averages(self):
        for path in [ROOT/'dashboard/app.py', ROOT/'dashboard/data.py']:
            code = path.read_text()
            self.assertNotIn('competitiveness_score', code)
            self.assertNotIn('expansion_score', code)
            self.assertNotIn('price_for_score', code)
            tree = ast.parse(code)
            self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                                 and n.func.attr in {'mean', 'interpolate'} for n in ast.walk(tree)))
        self.assertNotIn('EREV', self.models.battery_chemistry.dropna().tolist())
        self.assertTrue(self.models.total_range_km.isna().all())
        self.assertTrue(self.models.loc[self.models.brand.eq('Li Auto'), 'electric_range_km'].isna().all())
        self.assertTrue(self.models.loc[self.models.brand.eq('Xiaomi Auto'), 'price_eur'].isna().all())


if __name__ == '__main__':
    unittest.main()
