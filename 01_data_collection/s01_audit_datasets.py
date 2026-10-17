import sys
import os
import numpy as np
import rasterio
import geopandas as gpd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS02_WORLDPOP, DS03_INFRASTRUCTURE, DS04_DEM, DS05_LULC, DS06_SAR, ensure_dirs
ensure_dirs()
print('=' * 70)
print('        MASTER DATASET AUDIT  ·  STEP 01 HEALTH CHECK')
print('=' * 70)
errors: list[str] = []

def check_exists(path, label: str) -> bool:
    if not path.exists():
        print(f'  [MISSING] {label}')
        errors.append(str(path))
        return False
    return True
label = 'ds_01  Admin Boundary'
if check_exists(DS01_ADMIN_BOUNDARY, label):
    gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY))
    area_km2 = gdf.to_crs(epsg=32646).geometry.area.sum() / 1000000.0
    print(f'  [OK] {label}: {len(gdf)} jurisdictions | CRS: {gdf.crs} | Area: {area_km2:.2f} km² | Size: {DS01_ADMIN_BOUNDARY.stat().st_size / 1024:.1f} KB')
label = 'ds_02  WorldPop Population'
if check_exists(DS02_WORLDPOP, label):
    with rasterio.open(str(DS02_WORLDPOP)) as src:
        data = src.read(1)
        valid = (data != (src.nodata or -9999.0)) & np.isfinite(data) & (data >= 0)
        total_pop = data[valid].sum()
        print(f'  [OK] {label}: Shape {src.shape} | Res {src.res} m | CRS: {src.crs} | Pop: {total_pop:,.0f} | Size: {DS02_WORLDPOP.stat().st_size / (1024 * 1024):.2f} MB')
label = 'ds_03  Critical Infrastructure'
if check_exists(DS03_INFRASTRUCTURE, label):
    gdf3 = gpd.read_file(str(DS03_INFRASTRUCTURE))
    cats = dict(gdf3['category'].value_counts())
    print(f'  [OK] {label}: {len(gdf3)} points | CRS: {gdf3.crs} | Categories: {cats}')
label = 'ds_04  Copernicus DEM'
if check_exists(DS04_DEM, label):
    with rasterio.open(str(DS04_DEM)) as src:
        print(f'  [OK] {label}: Shape {src.shape} | Bands: {src.count} | Res: {src.res} m | CRS: {src.crs} | Size: {DS04_DEM.stat().st_size / (1024 * 1024):.2f} MB')
        if src.count != 3:
            print(f'  [WARN] Expected 3 bands (elevation, slope, TWI), got {src.count}')
            errors.append('ds_04 band count mismatch')
label = 'ds_05  Dynamic World LULC'
if check_exists(DS05_LULC, label):
    with rasterio.open(str(DS05_LULC)) as src:
        print(f'  [OK] {label}: Shape {src.shape} | Bands: {src.count} | Res: {src.res} m | CRS: {src.crs} | Size: {DS05_LULC.stat().st_size / (1024 * 1024):.2f} MB')
label = 'ds_06  Sentinel-1 SAR'
if check_exists(DS06_SAR, label):
    with rasterio.open(str(DS06_SAR)) as src:
        gt = src.read(1)
        valid_gt = (gt != -9999.0) & np.isfinite(gt)
        flooded_km2 = (gt[valid_gt] == 1).sum() * 0.0009
        print(f'  [OK] {label}: Shape {src.shape} | Bands: {src.count} | Flooded: {flooded_km2:.2f} km² | CRS: {src.crs} | Size: {DS06_SAR.stat().st_size / (1024 * 1024):.2f} MB')
print('=' * 70)
if errors:
    print(f'  STATUS: ⚠  {len(errors)} ISSUE(S) FOUND — Resolve before Step 2!')
    for e in errors:
        print(f'    → {e}')
    sys.exit(1)
else:
    print('  STATUS: ✓  ALL 6 DATASETS VERIFIED — Pipeline ready for Step 02.')
print('=' * 70)
