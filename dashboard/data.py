"""Shared CSV validation and selection rules for the app, notebook and tests."""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
REGIONS = ['Europe', 'Southeast Asia', 'Middle East', 'Latin America']
MODEL_COLUMNS = {
    'brand', 'model', 'variant_context', 'specification_market', 'powertrain_type',
    'battery_chemistry', 'battery_capacity_kwh', 'battery_capacity_basis',
    'electric_range_km', 'range_standard', 'total_range_km', 'total_range_standard',
    'price_eur', 'price_market', 'price_basis', 'availability_context', 'source',
    'source_url', 'verification_date', 'verification_status', 'notes',
}
BRAND_COLUMNS = {'brand', 'group_or_company', 'relationship', 'source_url', 'verification_date', 'positioning_editorial'}
PRESENCE_COLUMNS = {'brand', 'region', 'presence_status', 'evidence_country', 'evidence_date',
                    'source', 'source_url', 'verification_date', 'evidence_note'}


def validate_data(models, brands, presence):
    for name, frame, required, keys in [
        ('model_specs.csv', models, MODEL_COLUMNS, ['brand', 'model']),
        ('brands.csv', brands, BRAND_COLUMNS, ['brand']),
        ('expansion_markets.csv', presence, PRESENCE_COLUMNS, ['brand', 'region']),
    ]:
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name}: missing columns {sorted(missing)}")
        if frame.empty or frame[keys].isna().any().any() or frame.duplicated(keys).any():
            raise ValueError(f"{name}: empty data, missing keys or duplicate keys")
        dates = pd.to_datetime(frame.verification_date, format='%Y-%m-%d', errors='coerce')
        if dates.isna().any():
            raise ValueError(f"{name}: invalid verification date")
    if set(models.brand) != set(brands.brand) or set(models.brand) != set(presence.brand):
        raise ValueError('Brand coverage differs between the three CSV files')
    for b, group in presence.groupby('brand'):
        if set(group.region) != set(REGIONS):
            raise ValueError(f'{b}: expected one presence row for each of the four regions')
    if not presence.presence_status.isin(['present', 'absent', 'unknown']).all():
        raise ValueError('Presence status must be present, absent or unknown')
    known = presence.loc[presence.presence_status.ne('unknown')]
    if known[['source_url', 'source', 'evidence_date', 'evidence_country', 'evidence_note']].isna().any().any():
        raise ValueError('Resolved presence requires country, date, source and evidence')
    if models[['powertrain_type', 'source', 'source_url', 'verification_status']].isna().any().any():
        raise ValueError('Each model requires a powertrain, source and verification status')
    if not models.powertrain_type.isin(['BEV', 'EREV', 'PHEV', 'unknown']).all():
        raise ValueError('Invalid powertrain category')
    if not models.verification_status.isin(['verified_values', 'partial']).all():
        raise ValueError('Invalid verification status')
    if not models.battery_chemistry.dropna().isin(['LFP', 'NMC', 'NMC811']).all():
        raise ValueError('Chemistry must be a specific supported chemistry or missing')
    for metric, context in [('electric_range_km', ['range_standard']),
                            ('total_range_km', ['total_range_standard']),
                            ('battery_capacity_kwh', ['battery_capacity_basis']),
                            ('price_eur', ['price_market', 'price_basis'])]:
        numeric = pd.to_numeric(models[metric], errors='raise')
        if ((numeric <= 0) | numeric.eq(float('inf'))).any():
            raise ValueError(f'{metric}: values must be finite and positive or missing')
        if models.loc[numeric.notna(), context].isna().any().any():
            raise ValueError(f'{metric}: missing unit/definition context')
    if not models.battery_capacity_basis.dropna().isin(['usable', 'nominal', 'unspecified']).all():
        raise ValueError('Invalid capacity basis')
    if not models.range_standard.dropna().isin(['EV Database Real Range', 'WLTP', 'CLTC']).all():
        raise ValueError('Invalid electric range standard')


def load_data(data_dir=DATA_DIR):
    data_dir = Path(data_dir)
    models = pd.read_csv(data_dir / 'model_specs.csv', sep=';')
    brands = pd.read_csv(data_dir / 'brands.csv', sep=';')
    presence = pd.read_csv(data_dir / 'expansion_markets.csv', sep=';')
    validate_data(models, brands, presence)
    # Do not merge brand x region evidence into models: that would multiply rows.
    models = models.merge(brands[['brand', 'group_or_company']], on='brand', how='left', validate='many_to_one')
    return models, brands, presence


def comparable_models(models):
    mask = (models.powertrain_type.eq('BEV') & models.price_market.eq('Netherlands')
            & models.price_basis.eq('Listed RRP; excludes indirect incentives')
            & models.availability_context.eq('listed_available')
            & models.range_standard.eq('EV Database Real Range')
            & models.price_eur.notna() & models.electric_range_km.notna())
    return models.loc[mask].copy()


def kpis(models):
    return {'models': len(models), 'brands': models.brand.nunique(),
            'comparable': len(comparable_models(models)),
            'range': int(models.electric_range_km.notna().sum())}


def presence_matrix(presence):
    return presence.pivot(index='brand', columns='region', values='presence_status').reindex(columns=REGIONS).sort_index()
