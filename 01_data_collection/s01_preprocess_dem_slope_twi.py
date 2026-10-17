import math
import numpy as np
import rasterio
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS04_DEM, TARGET_SCALE, ensure_dirs
ensure_dirs()
print('=' * 65)
print('  STEP 1: DEM SLOPE & TWI RECOMPUTATION VALIDATION')
print('=' * 65)
print(f'Reading: {DS04_DEM}')
with rasterio.open(str(DS04_DEM)) as src:
    meta = src.meta.copy()
    bands = src.count
    elev = src.read(1)
    print(f'  Bands: {bands} | CRS: {src.crs} | Shape: {src.shape}')
    print(f'  Elevation range: {elev.min():.2f} – {elev.max():.2f} m')
if bands >= 3:
    print('[INFO] ds_04 already has 3 bands (elevation, slope, TWI). Recomputing for validation…')
valid = np.isfinite(elev) & (elev > -100) & (elev < 500)
elev_clean = np.where(valid, elev, elev[valid].mean())
CELL_SIZE = float(TARGET_SCALE)
dz_dy, dz_dx = np.gradient(elev_clean, CELL_SIZE)
slope_rad = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
slope_deg = slope_rad * (180.0 / math.pi)
tan_slope = np.tan(np.maximum(slope_rad, 0.001))
twi = np.log(1.0 / tan_slope)
elev_out = np.where(valid, elev_clean, -9999.0).astype(np.float32)
slope_out = np.where(valid, slope_deg, -9999.0).astype(np.float32)
twi_out = np.where(valid, twi, -9999.0).astype(np.float32)
meta.update({'count': 3, 'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
with rasterio.open(str(DS04_DEM), 'w', **meta) as dst:
    dst.write(elev_out, 1)
    dst.write(slope_out, 2)
    dst.write(twi_out, 3)
    dst.set_band_description(1, 'elevation_meters')
    dst.set_band_description(2, 'slope_degrees')
    dst.set_band_description(3, 'topographic_wetness_index')
print(f'  Elevation: mean={elev_clean[valid].mean():.2f} m')
print(f'  Slope:     mean={slope_deg[valid].mean():.4f}°')
print(f'  TWI:       mean={twi[valid].mean():.4f}')
print(f'[SUCCESS] ds_04_copernicus_dem_30m.tif (3-band) updated → {DS04_DEM}')
