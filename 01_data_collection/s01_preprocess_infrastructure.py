import geopandas as gpd
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS03_INFRASTRUCTURE, ensure_dirs
ensure_dirs()
print('=' * 65)
print('  STEP 1: INFRASTRUCTURE DATASET NORMALISATION')
print('=' * 65)
infra_gdf = gpd.read_file(str(DS03_INFRASTRUCTURE))
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
infra_gdf = infra_gdf.to_crs(epsg=32646)
print(f'  Loaded {len(infra_gdf)} infrastructure nodes')
print(f'  Current CRS: {infra_gdf.crs}')
unknown = infra_gdf['category'] == 'UNKNOWN'
if unknown.any():
    print(f'  Reclassifying {unknown.sum()} UNKNOWN → WASH_DRINKING_WATER (Open Cities tube wells)')
    infra_gdf.loc[unknown, 'category'] = 'WASH_DRINKING_WATER'
admin_union = admin_gdf.union_all()
infra_clipped = infra_gdf[infra_gdf.geometry.within(admin_union)].copy()
print(f'  After spatial clip: {len(infra_clipped)} nodes strictly in DNCC & DSCC')
print('\n  Final category counts:')
cat_counts = dict(infra_clipped['category'].value_counts())
for cat, n in cat_counts.items():
    print(f'    {cat}: {n}')
EXPECTED = {'WASH_DRINKING_WATER': 342, 'EMERGENCY_SHELTER': 97, 'WASTE_CONTAMINATION_SITE': 380}
for cat, expected in EXPECTED.items():
    actual = cat_counts.get(cat, 0)
    status = '✓' if actual == expected else f'⚠ expected {expected}'
    print(f'    {cat}: {actual}  {status}')
infra_clipped.to_file(str(DS03_INFRASTRUCTURE), driver='GeoJSON')
print(f'\n[SUCCESS] Saved {len(infra_clipped)} nodes → {DS03_INFRASTRUCTURE}')
