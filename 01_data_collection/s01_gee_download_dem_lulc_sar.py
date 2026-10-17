import os
import math
import requests
import numpy as np
import rasterio
import ee
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DATASETS_DIR, GEE_PROJECT_ID, GEE_BBOX_WGS84, TARGET_CRS, TARGET_SCALE, ensure_dirs, MONSOON_START, MONSOON_END, PRE_MONSOON_START, PRE_MONSOON_END
ensure_dirs()
print(f'[Step 1-GEE] Initialising Google Earth Engine (project: {GEE_PROJECT_ID})…')
ee.Initialize(project=GEE_PROJECT_ID)
print('[Step 1-GEE] GEE initialised successfully.\n')
bbox = ee.Geometry.BBox(*GEE_BBOX_WGS84)
CRS = TARGET_CRS
SCALE = TARGET_SCALE
DS_DIR = str(DATASETS_DIR)

def stream_download(url: str, out_path: str, description: str) -> None:
    print(f'  Streaming download: {description}…')
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f'Download failed ({response.status_code}): {response.text[:200]}')
    with open(out_path, 'wb') as fh:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fh.write(chunk)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f'  → Saved {os.path.basename(out_path)} ({size_mb:.2f} MB)')
print('=' * 65)
print('DATASET 4: COPERNICUS DEM GLO-30 (ELEVATION, SLOPE, TWI)')
print('=' * 65)
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().clip(bbox).toFloat()
dem_raw_tmp = os.path.join(DS_DIR, '_tmp_dem_elevation.tif')
url_dem = dem.getDownloadURL({'region': bbox, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'})
stream_download(url_dem, dem_raw_tmp, 'Copernicus DEM 30m Elevation')
print('  Computing physical slope and TWI from elevation array…')
with rasterio.open(dem_raw_tmp) as src:
    meta = src.meta.copy()
    elev = src.read(1)
valid = np.isfinite(elev) & (elev > -100) & (elev < 500)
elev_clean = np.where(valid, elev, elev[valid].mean())
dz_dy, dz_dx = np.gradient(elev_clean, float(SCALE))
slope_rad = np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2))
slope_deg = slope_rad * (180.0 / math.pi)
tan_slope = np.tan(np.maximum(slope_rad, 0.001))
twi = np.log(1.0 / tan_slope)
elev_out = np.where(valid, elev_clean, -9999.0).astype(np.float32)
slope_out = np.where(valid, slope_deg, -9999.0).astype(np.float32)
twi_out = np.where(valid, twi, -9999.0).astype(np.float32)
meta.update({'count': 3, 'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
ds04_path = os.path.join(DS_DIR, 'ds_04_copernicus_dem_30m.tif')
with rasterio.open(ds04_path, 'w', **meta) as dst:
    dst.write(elev_out, 1)
    dst.write(slope_out, 2)
    dst.write(twi_out, 3)
    dst.set_band_description(1, 'elevation_meters')
    dst.set_band_description(2, 'slope_degrees')
    dst.set_band_description(3, 'topographic_wetness_index')
os.remove(dem_raw_tmp)
print(f'[SUCCESS] ds_04_copernicus_dem_30m.tif → {os.path.getsize(ds04_path) / (1024 * 1024):.2f} MB\n')
print('=' * 65)
print('DATASET 5: DYNAMIC WORLD IMPERVIOUS SURFACE (30M)')
print('=' * 65)
dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterBounds(bbox).filterDate('2022-01-01', '2022-12-31').select('built').mean().clip(bbox).toFloat().rename('impervious_fraction')
tmp_dw = os.path.join(DS_DIR, '_tmp_dw.tif')
url_dw = dw.getDownloadURL({'region': bbox, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'})
stream_download(url_dw, tmp_dw, 'Dynamic World Impervious Surface')
with rasterio.open(tmp_dw) as src:
    dw_data = src.read(1)
    meta_dw = src.meta.copy()
meta_dw.update({'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
clean_dw = np.where(np.isfinite(dw_data) & (dw_data >= 0), dw_data, -9999.0).astype(np.float32)
ds05_path = os.path.join(DS_DIR, 'ds_05_dynamic_world_lulc_30m.tif')
with rasterio.open(ds05_path, 'w', **meta_dw) as dst:
    dst.write(clean_dw, 1)
    dst.set_band_description(1, 'impervious_fraction')
os.remove(tmp_dw)
print(f'[SUCCESS] ds_05_dynamic_world_lulc_30m.tif → {os.path.getsize(ds05_path) / (1024 * 1024):.2f} MB\n')
print('=' * 65)
print('DATASET 6: SENTINEL-1 SAR FLOOD INUNDATION (30M)')
print('=' * 65)
s1_base = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(bbox).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW'))
s1_dry = s1_base.filterDate(PRE_MONSOON_START, PRE_MONSOON_END).select('VH').median().clip(bbox).focal_median(50, 'circle', 'meters').toFloat()
s1_flood = s1_base.filterDate(MONSOON_START, MONSOON_END).select('VH').median().clip(bbox).focal_median(50, 'circle', 'meters').toFloat()
tmp_dry = os.path.join(DS_DIR, '_tmp_s1_dry.tif')
tmp_flood = os.path.join(DS_DIR, '_tmp_s1_flood.tif')
stream_download(s1_dry.getDownloadURL({'region': bbox, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'}), tmp_dry, 'Sentinel-1 Dry Baseline VH')
stream_download(s1_flood.getDownloadURL({'region': bbox, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'}), tmp_flood, 'Sentinel-1 Monsoon Flood VH')
with rasterio.open(tmp_dry) as src_d:
    dry_vh = src_d.read(1)
    sar_meta = src_d.meta.copy()
with rasterio.open(tmp_flood) as src_f:
    flood_vh = src_f.read(1)
vh_diff = (flood_vh - dry_vh).astype(np.float32)
flood_mask = ((flood_vh < -20.0) | (vh_diff < -2.5)).astype(np.float32)
valid_sar = np.isfinite(dry_vh) & np.isfinite(flood_vh)
flood_mask[~valid_sar] = -9999.0
vh_diff[~valid_sar] = -9999.0
flood_vh[~valid_sar] = -9999.0
dry_vh[~valid_sar] = -9999.0
sar_meta.update({'count': 4, 'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
ds06_path = os.path.join(DS_DIR, 'ds_06_sentinel1_sar_flood_extent_30m.tif')
with rasterio.open(ds06_path, 'w', **sar_meta) as dst:
    dst.write(flood_mask.astype(np.float32), 1)
    dst.write(vh_diff, 2)
    dst.write(flood_vh, 3)
    dst.write(dry_vh.astype(np.float32), 4)
    dst.set_band_description(1, 'flood_ground_truth')
    dst.set_band_description(2, 'vh_diff')
    dst.set_band_description(3, 'monsoon_vh')
    dst.set_band_description(4, 'dry_vh')
for p in [tmp_dry, tmp_flood]:
    if os.path.exists(p):
        os.remove(p)
print(f'[SUCCESS] ds_06_sentinel1_sar_flood_extent_30m.tif → {os.path.getsize(ds06_path) / (1024 * 1024):.2f} MB\n')
print('=' * 65)
print('ALL 3 GEE SATELLITE DATASETS GATHERED SUCCESSFULLY.')
print('=' * 65)
