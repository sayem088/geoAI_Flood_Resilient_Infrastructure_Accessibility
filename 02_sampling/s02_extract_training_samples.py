import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
from shapely.geometry import Point
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS04_DEM, DS05_LULC, DS06_SAR, TRAINING_SAMPLES_GEOJSON, TRAINING_SAMPLES_CSV, SAMPLE_SIZE, RANDOM_SEED, SAR_DELTA_VH_THRESHOLD, SAR_PERM_WATER_THRESHOLD, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 2A: BALANCED SPATIAL SAMPLE EXTRACTION (DNCC & DSCC)')
print('=' * 75)
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
admin_union = admin_gdf.union_all()
print(f'Admin boundary: {len(admin_gdf)} jurisdictions | Area: {admin_gdf.to_crs(32646).geometry.area.sum() / 1000000.0:.2f} km²')
print('Loading and masking 30m raster stacks to DNCC & DSCC…')
geom = [admin_union]
with rasterio.open(str(DS04_DEM)) as s_dem, rasterio.open(str(DS05_LULC)) as s_lulc, rasterio.open(str(DS06_SAR)) as s_sar:
    transform = s_dem.transform
    dem_crop, _ = rasterio_mask(s_dem, geom, crop=False)
    lulc_crop, _ = rasterio_mask(s_lulc, geom, crop=False)
    sar_crop, _ = rasterio_mask(s_sar, geom, crop=False)
elev_arr = dem_crop[0]
slope_arr = dem_crop[1]
twi_arr = dem_crop[2]
imp_arr = lulc_crop[0]
sar_gt = sar_crop[0]
vh_diff = sar_crop[1]
monsoon_vh = sar_crop[2]
dry_vh = sar_crop[3]
print('Filtering valid urban land; masking permanent rivers and lakes…')
valid_city = (elev_arr > -50) & np.isfinite(elev_arr) & (imp_arr >= 0) & np.isfinite(imp_arr)
perm_water = (dry_vh < SAR_PERM_WATER_THRESHOLD) & (imp_arr < 0.1) & valid_city
dry_urban = valid_city & ~perm_water
print(f'  Valid urban pixels:       {valid_city.sum():,} ({valid_city.sum() * 0.0009:.2f} km²)')
print(f'  Permanent water pixels:   {perm_water.sum():,} ({perm_water.sum() * 0.0009:.2f} km²)')
print(f'  Normally dry land pixels: {dry_urban.sum():,}  ({dry_urban.sum() * 0.0009:.2f} km²)')
y_flood_mask = (vh_diff < SAR_DELTA_VH_THRESHOLD) & dry_urban
y_dry_mask = (vh_diff >= 0.0) & dry_urban
rows_f, cols_f = np.where(y_flood_mask)
rows_d, cols_d = np.where(y_dry_mask)
print(f'\nObserved flooded pixels (Y=1): {len(rows_f):,} ({len(rows_f) * 0.0009:.2f} km²)')
print(f'Observed stable dry   (Y=0):  {len(rows_d):,} ({len(rows_d) * 0.0009:.2f} km²)')
N = min(len(rows_f), len(rows_d), SAMPLE_SIZE // 2)
print(f'\nBalanced sample: {N:,} flooded + {N:,} dry (seed={RANDOM_SEED})…')
rng = np.random.default_rng(RANDOM_SEED)
idx_f = rng.choice(len(rows_f), size=N, replace=False)
idx_d = rng.choice(len(rows_d), size=N, replace=False)
sample_rows = np.concatenate([rows_f[idx_f], rows_d[idx_d]])
sample_cols = np.concatenate([cols_f[idx_f], cols_d[idx_d]])
labels = np.concatenate([np.ones(N, dtype=int), np.zeros(N, dtype=int)])
xs, ys = rasterio.transform.xy(transform, sample_rows, sample_cols)
xs, ys = (np.array(xs), np.array(ys))
df = pd.DataFrame({'elevation': elev_arr[sample_rows, sample_cols].astype(np.float32), 'slope': slope_arr[sample_rows, sample_cols].astype(np.float32), 'twi': twi_arr[sample_rows, sample_cols].astype(np.float32), 'impervious_fraction': imp_arr[sample_rows, sample_cols].astype(np.float32), 'vh_diff': vh_diff[sample_rows, sample_cols].astype(np.float32), 'flood_ground_truth': labels.astype(int), 'easting': xs.astype(np.float64), 'northing': ys.astype(np.float64)})
x_mid = float(np.median(xs))
y_mid = float(np.median(ys))
df['spatial_block'] = ((xs >= x_mid).astype(int) * 2 + (ys >= y_mid).astype(int)).astype(int)
print('\nSpatial Block Distribution:')
print(df['spatial_block'].value_counts().sort_index().to_string())
geometry = [Point(x, y) for x, y in zip(xs, ys)]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:32646')
joined = gpd.sjoin(gdf, admin_gdf[['adm3_name', 'geometry']], how='left', predicate='within')
gdf['thana'] = joined['adm3_name']
print('\nCity Corporation Sample Distribution:')
print(gdf['thana'].value_counts().to_string())
print('\n' + '-' * 75)
print('  FEATURE MEANS — FLOODED (Y=1) vs NON-FLOODED (Y=0)')
print('-' * 75)
for feat in ['elevation', 'slope', 'twi', 'impervious_fraction', 'vh_diff']:
    m_f = gdf.loc[gdf['flood_ground_truth'] == 1, feat].mean()
    m_d = gdf.loc[gdf['flood_ground_truth'] == 0, feat].mean()
    print(f'  {feat:<22} | Flooded={m_f:>7.3f} | Dry={m_d:>7.3f}')
gdf.to_file(str(TRAINING_SAMPLES_GEOJSON), driver='GeoJSON')
gdf.drop(columns='geometry').to_csv(str(TRAINING_SAMPLES_CSV), index=False)
print(f'\n[SUCCESS] Saved {len(gdf):,} training samples:')
print(f'  GeoJSON → {TRAINING_SAMPLES_GEOJSON}')
print(f'  CSV     → {TRAINING_SAMPLES_CSV}')
