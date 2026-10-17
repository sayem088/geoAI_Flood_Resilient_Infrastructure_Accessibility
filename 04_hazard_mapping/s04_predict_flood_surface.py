import numpy as np
import geopandas as gpd
import joblib
import rasterio
from rasterio.mask import mask as rasterio_mask
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS04_DEM, DS05_LULC, GEOAI_MODEL, FLOOD_PROB_RASTER, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 4A: WALL-TO-WALL FLOOD HAZARD PROBABILITY INFERENCE')
print('=' * 75)
print(f'Loading model: {GEOAI_MODEL}')
model = joblib.load(str(GEOAI_MODEL))
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
admin_union = admin_gdf.union_all()
geom = [admin_union]
print('Loading and masking 30m raster stacks to DNCC & DSCC…')
with rasterio.open(str(DS04_DEM)) as s_dem, rasterio.open(str(DS05_LULC)) as s_lulc:
    meta = s_dem.meta.copy()
    transform = s_dem.transform
    height, width = s_dem.shape
    dem_masked, _ = rasterio_mask(s_dem, geom, crop=False, nodata=-9999.0)
    lulc_masked, _ = rasterio_mask(s_lulc, geom, crop=False, nodata=-9999.0)
elev = dem_masked[0]
slope = dem_masked[1]
twi = dem_masked[2]
imp = lulc_masked[0]
valid_mask = (elev != -9999.0) & np.isfinite(elev) & (elev > -50) & (slope != -9999.0) & np.isfinite(slope) & (slope >= 0) & (twi != -9999.0) & np.isfinite(twi) & (imp != -9999.0) & np.isfinite(imp) & (imp >= 0)
print(f'  Valid dry-land pixels: {valid_mask.sum():,} ({valid_mask.sum() * 0.0009:.2f} km²)')
X_valid = np.column_stack([elev[valid_mask], slope[valid_mask], twi[valid_mask], imp[valid_mask]])
print(f'  Running XGBoost inference across {len(X_valid):,} pixels…')
prob_valid = model.predict_proba(X_valid)[:, 1]
prob_map = np.full((height, width), -9999.0, dtype=np.float32)
prob_map[valid_mask] = prob_valid
print(f'  P_flood stats: min={prob_valid.min():.3f}  mean={prob_valid.mean():.3f}  median={float(np.median(prob_valid)):.3f}  max={prob_valid.max():.3f}')
high_hazard_km2 = (prob_valid >= 0.5).sum() * 0.0009
print(f'\n  High-hazard area (P ≥ 0.50): {high_hazard_km2:.2f} km²  (published: 59.06 km²; SAR ref: 59.60 km²)')
meta.update({'count': 1, 'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
with rasterio.open(str(FLOOD_PROB_RASTER), 'w', **meta) as dst:
    dst.write(prob_map, 1)
    dst.set_band_description(1, 'flood_hazard_probability_0_to_1')
print(f'[SUCCESS] P_flood raster saved → {FLOOD_PROB_RASTER}')
print('[STEP 4A COMPLETE] Flood surface ready for cartographic mapping (run s04_generate_fig3).')
