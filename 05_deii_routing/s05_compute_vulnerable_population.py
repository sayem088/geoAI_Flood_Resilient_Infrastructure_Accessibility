import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS02_WORLDPOP, DS03_INFRASTRUCTURE, FLOOD_PROB_RASTER, TABLE5_CORP_BREAKDOWN, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 5E: CITY CORPORATION DEMOGRAPHIC CATCHMENT COLLAPSE')
print('=' * 75)
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
infra_gdf = gpd.read_file(str(DS03_INFRASTRUCTURE)).to_crs(epsg=32646)
wash = infra_gdf[infra_gdf['category'] == 'WASH_DRINKING_WATER']
wash_pts = np.column_stack([wash.geometry.x, wash.geometry.y])
shelters = infra_gdf[infra_gdf['category'] == 'EMERGENCY_SHELTER']
shelter_pts = np.column_stack([shelters.geometry.x, shelters.geometry.y])
tree_w = cKDTree(wash_pts)
tree_s = cKDTree(shelter_pts)
results = []
with rasterio.open(str(DS02_WORLDPOP)) as src_pop, rasterio.open(str(FLOOD_PROB_RASTER)) as src_prob:
    for idx, row in admin_gdf.iterrows():
        c_name = row['adm3_name']
        geom = [row.geometry]
        pop_crop, p_transform = rasterio_mask(src_pop, geom, crop=True, nodata=-9999.0)
        pop_arr = pop_crop[0]
        valid = (pop_arr != -9999.0) & np.isfinite(pop_arr) & (pop_arr > 0)
        p_vals = pop_arr[valid]
        r_idx, c_idx = np.where(valid)
        xs, ys = rasterio.transform.xy(p_transform, r_idx, c_idx)
        c_coords = np.column_stack([xs, ys])
        tot_pop = p_vals.sum()
        dw_dry, _ = tree_w.query(c_coords)
        ds_dry, _ = tree_s.query(c_coords)
        p_raw = np.array([val[0] for val in src_prob.sample(c_coords)])
        p_clean = np.clip(np.where(p_raw == -9999.0, 0.0, p_raw), 0.0, 1.0)
        severed = p_clean >= 0.7
        dw_mon = dw_dry * (1.0 + 3.0 * p_clean)
        dw_mon[severed] = 1000000000.0
        ds_mon = ds_dry * (1.0 + 3.0 * p_clean)
        ds_mon[severed] = 1000000000.0
        w_dry_acc = p_vals[dw_dry <= 2000].sum()
        w_mon_acc = p_vals[dw_mon <= 2000].sum()
        s_dry_acc = p_vals[ds_dry <= 2000].sum()
        s_mon_acc = p_vals[ds_mon <= 2000].sum()
        w_cut = w_dry_acc - w_mon_acc
        s_cut = s_dry_acc - s_mon_acc
        high_haz_pop = p_vals[p_clean >= 0.5].sum()
        results.append({'City Corporation': c_name, 'Total Population': int(round(tot_pop)), 'Dry Water Access': int(round(w_dry_acc)), 'Monsoon Water Access': int(round(w_mon_acc)), 'Water Cutoff': int(round(w_cut)), 'Water Loss (%)': round(w_cut / w_dry_acc * 100, 1), 'Dry Shelter Access': int(round(s_dry_acc)), 'Monsoon Shelter Access': int(round(s_mon_acc)), 'Shelter Cutoff': int(round(s_cut)), 'Shelter Loss (%)': round(s_cut / s_dry_acc * 100, 1), 'High Hazard Pop (P>=0.50)': int(round(high_haz_pop)), 'High Hazard (%)': round(high_haz_pop / tot_pop * 100, 1)})
df_res = pd.DataFrame(results)
print(df_res.to_string(index=False))
table_5_md = '# Table 5: Demographic Catchment Collapse and Vulnerable Population Disruption across Dhaka City Corporations (2 km Threshold)\n\n| City Corporation | Total Population | Baseline Water Access | Monsoon Water Access | **Water Cutoff** | Loss (%) | Baseline Shelter Access | Monsoon Shelter Access | **Shelter Cutoff** | Loss (%) | Active High Hazard Pop ($P \\ge 0.50$) | High Hazard Share (%) |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n'
for idx, r in df_res.iterrows():
    table_5_md += f"| **{r['City Corporation']}** | {r['Total Population']:,} | {r['Dry Water Access']:,} | {r['Monsoon Water Access']:,} | **{r['Water Cutoff']:,}** | **-{r['Water Loss (%)']}%** | {r['Dry Shelter Access']:,} | {r['Monsoon Shelter Access']:,} | **{r['Shelter Cutoff']:,}** | **-{r['Shelter Loss (%)']}%** | **{r['High Hazard Pop (P>=0.50)']:,}** | **{r['High Hazard (%)']}%** |\n"
tot_p = df_res['Total Population'].sum()
tot_wc = df_res['Water Cutoff'].sum()
tot_sc = df_res['Shelter Cutoff'].sum()
tot_hh = df_res['High Hazard Pop (P>=0.50)'].sum()
table_5_md += f"| **Combined Urban Core** | **{tot_p:,}** | **{df_res['Dry Water Access'].sum():,}** | **{df_res['Monsoon Water Access'].sum():,}** | **{tot_wc:,}** | **-{tot_wc / df_res['Dry Water Access'].sum() * 100:.1f}%** | **{df_res['Dry Shelter Access'].sum():,}** | **{df_res['Monsoon Shelter Access'].sum():,}** | **{tot_sc:,}** | **-{tot_sc / df_res['Dry Shelter Access'].sum() * 100:.1f}%** | **{tot_hh:,}** | **{tot_hh / tot_p * 100:.1f}%** |\n"
table_5_md += '\n*Note: Evaluates demographic isolation at a 2-km pedestrian walking limit under DEII flood impedance (alpha=3.0, severance at P_flood >= 0.70).*\n'
TABLE5_CORP_BREAKDOWN.write_text(table_5_md, encoding='utf-8')
print(f'\n[SUCCESS] Table 5 exported to: {TABLE5_CORP_BREAKDOWN}')
