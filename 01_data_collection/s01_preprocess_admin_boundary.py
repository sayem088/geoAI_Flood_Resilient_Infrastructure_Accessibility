import geopandas as gpd
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, ensure_dirs
ensure_dirs()
RAW_PATH = DS01_ADMIN_BOUNDARY
TARGET_THANAS = ['Dhaka North City Corporation', 'Dhaka South City Corporation']
print('=' * 65)
print('  STEP 1: ADMIN BOUNDARY PREPROCESSING')
print('=' * 65)
print(f'Reading: {RAW_PATH}')
raw_gdf = gpd.read_file(str(RAW_PATH))
print(f'  Total raw features: {len(raw_gdf)}')
dhaka_gdf = raw_gdf[raw_gdf['adm3_name'].isin(TARGET_THANAS)].copy()
print(f"  Filtered to {len(dhaka_gdf)} City Corporation(s): {dhaka_gdf['adm3_name'].tolist()}")
invalid = (~dhaka_gdf.is_valid).sum()
if invalid > 0:
    print(f'  Repairing {invalid} invalid geometries…')
    dhaka_gdf['geometry'] = dhaka_gdf['geometry'].make_valid()
dhaka_utm = dhaka_gdf.to_crs(epsg=32646)
dhaka_utm['area_sqkm'] = dhaka_utm.geometry.area / 1000000.0
print('\n  Area verification:')
for _, row in dhaka_utm.iterrows():
    print(f"    {row['adm3_name']}: {row['area_sqkm']:.2f} km²")
print(f"    Combined: {dhaka_utm['area_sqkm'].sum():.2f} km²  (expected 304.51 km²)")
cols = [c for c in ['adm3_name', 'adm2_name', 'adm1_name', 'area_sqkm', 'geometry'] if c in dhaka_utm.columns]
dhaka_utm = dhaka_utm[cols]
dhaka_utm.to_file(str(DS01_ADMIN_BOUNDARY), driver='GeoJSON')
print(f'\n[SUCCESS] Saved ds_01_admin_boundary.geojson → {DS01_ADMIN_BOUNDARY}')
