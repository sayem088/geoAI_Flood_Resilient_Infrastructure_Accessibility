import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS02_WORLDPOP, ensure_dirs
ensure_dirs()
RAW_PATH = DS02_WORLDPOP
DHAKA_UTM_BOUNDS = (226000.0, 2618000.0, 248000.0, 2647000.0)
print('=' * 65)
print('  STEP 1: WORLDPOP 100M POPULATION PREPROCESSING')
print('=' * 65)
print(f'Reading: {RAW_PATH}')
with rasterio.open(str(RAW_PATH)) as src:
    print(f'  Source CRS:    {src.crs}')
    print(f'  Source Shape:  {src.shape}')
    print(f'  Nodata value:  {src.nodata}')
    data = src.read(1)
    valid = (data != (src.nodata or -99999.0)) & np.isfinite(data) & (data >= 0)
    total_pop = float(data[valid].sum())
    print(f'  Total population in raster: {total_pop:,.0f}')
print(f'\n[INFO] ds_02 already processed at: {DS02_WORLDPOP}')
print('       If you need to re-clip/reproject from a raw Bangladesh raster,')
print('       update RAW_PATH above to point to bd_population_100m.tif')
print(f'\n[SUCCESS] WorldPop 100m raster verified → {DS02_WORLDPOP}')
