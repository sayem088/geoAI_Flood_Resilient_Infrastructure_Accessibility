import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS03_INFRASTRUCTURE, FLOOD_PROB_RASTER, DEII_RASTER, DEII_ALPHA_BASELINE, DEII_TAU_BASELINE, TABLE4_DEII_SENSITIVITY, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 5A: DYNAMIC ENVIRONMENTAL INACCESSIBILITY INDEX (DEII)')
print('=' * 75)
print(f'Loading P_flood raster: {FLOOD_PROB_RASTER}')
with rasterio.open(str(FLOOD_PROB_RASTER)) as src:
    meta = src.meta.copy()
    transform = src.transform
    height, width = src.shape
    prob_arr = src.read(1)
valid_prob = (prob_arr != -9999.0) & np.isfinite(prob_arr)
p_clean = np.clip(np.where(valid_prob, prob_arr, 0.0), 0.0, 1.0)
print(f'  Valid urban pixels: {valid_prob.sum():,} ({valid_prob.sum() * 0.0009:.2f} km²)')
rows, cols = np.indices((height, width))
xs, ys = rasterio.transform.xy(transform, rows.flatten(), cols.flatten())
coords = np.column_stack([xs, ys])
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
infra_gdf = gpd.read_file(str(DS03_INFRASTRUCTURE)).to_crs(epsg=32646)
wash_gdf = infra_gdf[infra_gdf['category'] == 'WASH_DRINKING_WATER']
shelter_gdf = infra_gdf[infra_gdf['category'] == 'EMERGENCY_SHELTER']
wash_pts = np.column_stack([wash_gdf.geometry.x, wash_gdf.geometry.y])
shelter_pts = np.column_stack([shelter_gdf.geometry.x, shelter_gdf.geometry.y])
print(f'  WASH points:   {len(wash_pts)}')
print(f'  Shelter points: {len(shelter_pts)}')
print('Computing distance grids (KD-Tree)…')
d_wash_dry_m, _ = cKDTree(wash_pts).query(coords)
d_shelter_dry_m, _ = cKDTree(shelter_pts).query(coords)
d_wash_dry_km = (d_wash_dry_m / 1000.0).reshape(height, width).astype(np.float32)
d_shelter_dry_km = (d_shelter_dry_m / 1000.0).reshape(height, width).astype(np.float32)
d_wash_dry_km[~valid_prob] = -9999.0
d_shelter_dry_km[~valid_prob] = -9999.0
alpha = DEII_ALPHA_BASELINE
tau = DEII_TAU_BASELINE
severed = (p_clean >= tau) & valid_prob
print(f'Applying DEII impedance: α={alpha}, τ={tau}…')
print(f'  Severed road pixels (P ≥ {tau}): {severed.sum():,} ({severed.sum() * 0.0009:.2f} km²)')
d_wash_monsoon_km = np.where(valid_prob, d_wash_dry_km * (1.0 + alpha * p_clean), -9999.0).astype(np.float32)
d_shelter_monsoon_km = np.where(valid_prob, d_shelter_dry_km * (1.0 + alpha * p_clean), -9999.0).astype(np.float32)
d_wash_monsoon_km[severed] = 99.0
d_shelter_monsoon_km[severed] = 99.0
wash_delay_km = np.where(valid_prob & ~severed, d_wash_monsoon_km - d_wash_dry_km, -9999.0).astype(np.float32)
shelter_delay_km = np.where(valid_prob & ~severed, d_shelter_monsoon_km - d_shelter_dry_km, -9999.0).astype(np.float32)
meta.update({'count': 5, 'dtype': 'float32', 'nodata': -9999.0, 'compress': 'lzw'})
with rasterio.open(str(DEII_RASTER), 'w', **meta) as dst:
    dst.write(d_wash_dry_km, 1)
    dst.write(d_wash_monsoon_km, 2)
    dst.write(d_shelter_dry_km, 3)
    dst.write(d_shelter_monsoon_km, 4)
    dst.write(wash_delay_km, 5)
    dst.set_band_description(1, 'wash_distance_dry_km')
    dst.set_band_description(2, 'wash_distance_monsoon_km')
    dst.set_band_description(3, 'shelter_distance_dry_km')
    dst.set_band_description(4, 'shelter_distance_monsoon_km')
    dst.set_band_description(5, 'wash_travel_delay_km')
print(f'[SUCCESS] DEII raster saved → {DEII_RASTER}')
print('\nComputing Zonal Disruption Statistics for DNCC and DSCC...')
thana_deii = []
for idx, row in admin_gdf.iterrows():
    c_name = row['adm3_name']
    geom_c = [row.geometry]
    with rasterio.open(str(DEII_RASTER)) as src:
        c_w_dry, _ = rasterio_mask(src, geom_c, crop=True, indexes=1)
        c_w_mon, _ = rasterio_mask(src, geom_c, crop=True, indexes=2)
        c_s_dry, _ = rasterio_mask(src, geom_c, crop=True, indexes=3)
        c_s_mon, _ = rasterio_mask(src, geom_c, crop=True, indexes=4)
    m_valid = (c_w_dry != -9999.0) & np.isfinite(c_w_dry)
    w_severed = ((c_w_mon >= 90.0) & m_valid).sum()
    s_severed = ((c_s_mon >= 90.0) & m_valid).sum()
    w_unsevered = m_valid & (c_w_mon < 90.0)
    s_unsevered = m_valid & (c_s_mon < 90.0)
    mean_w_dry = float(np.mean(c_w_dry[m_valid]))
    mean_w_mon = float(np.mean(c_w_mon[w_unsevered]))
    mean_s_dry = float(np.mean(c_s_dry[m_valid]))
    mean_s_mon = float(np.mean(c_s_mon[s_unsevered]))
    thana_deii.append({'City Corporation': c_name, 'Dry Water Dist (km)': mean_w_dry, 'Monsoon Water Dist (km)': mean_w_mon, 'Water Delay (+km)': mean_w_mon - mean_w_dry, 'Water Delay (%)': (mean_w_mon - mean_w_dry) / mean_w_dry * 100, 'Water Severed (%)': w_severed / m_valid.sum() * 100, 'Dry Shelter Dist (km)': mean_s_dry, 'Monsoon Shelter Dist (km)': mean_s_mon, 'Shelter Delay (+km)': mean_s_mon - mean_s_dry, 'Shelter Delay (%)': (mean_s_mon - mean_s_dry) / mean_s_dry * 100, 'Shelter Severed (%)': s_severed / m_valid.sum() * 100})
df_thana_deii = pd.DataFrame(thana_deii)
print(df_thana_deii.to_string(index=False))
table_4_md = '# Table 4: City Corporation Travel Distance Disruption under Dynamic Environmental Inaccessibility (DEII)\n\n| City Corporation | Dry Water Dist ($km$) | Monsoon Water Dist ($km$) | Water Travel Delay ($+km$) | Delay (\\%) | Water Severed Area (\\%) | Dry Shelter Dist ($km$) | Monsoon Shelter Dist ($km$) | Shelter Travel Delay ($+km$) | Delay (\\%) | Shelter Severed Area (\\%) |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n'
for idx, r in df_thana_deii.iterrows():
    table_4_md += f"| **{r['City Corporation']}** | {r['Dry Water Dist (km)']:.2f} km | {r['Monsoon Water Dist (km)']:.2f} km | **+{r['Water Delay (+km)']:.2f} km** | **+{r['Water Delay (%)']:.1f}\\%** | **{r['Water Severed (%)']:.1f}\\%** | {r['Dry Shelter Dist (km)']:.2f} km | {r['Monsoon Shelter Dist (km)']:.2f} km | **+{r['Shelter Delay (+km)']:.2f} km** | **+{r['Shelter Delay (%)']:.1f}\\%** | **{r['Shelter Severed (%)']:.1f}\\%** |\n"
table_4_md += "\n*Note: Derived from wall-to-wall 30m DEII impedance model (d' = d * (1 + 3.0 * P_flood)) with physical route severance at P_flood >= 0.70 strictly within DNCC and DSCC.*\n"
TABLE4_DEII_SENSITIVITY.write_text(table_4_md, encoding='utf-8')
print(f'[SUCCESS] Table 4 exported to: {TABLE4_DEII_SENSITIVITY}')
print('[STEP 5A COMPLETE] Run s05_compute_catchment_collapse.py next.')
