import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS02_WORLDPOP, DS03_INFRASTRUCTURE, FLOOD_PROB_RASTER, DEII_WALKING_SPEED_KMH, DEII_THRESHOLDS_MIN, DEII_SCENARIOS, TABLE3_CATCHMENT, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 5B: DEMOGRAPHIC CATCHMENT COLLAPSE & LANDFILL EXPOSURE')
print('=' * 75)
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
admin_union = admin_gdf.union_all()
with rasterio.open(str(DS02_WORLDPOP)) as src_pop:
    pop_masked, pop_tr = rasterio_mask(src_pop, [admin_union], crop=False, nodata=-9999.0)
    pop_transform = src_pop.transform
pop_arr = pop_masked[0]
valid_pop = (pop_arr != -9999.0) & np.isfinite(pop_arr) & (pop_arr > 0)
rows_p, cols_p = np.where(valid_pop)
pop_vals = pop_arr[rows_p, cols_p]
xs_p, ys_p = rasterio.transform.xy(pop_transform, rows_p, cols_p)
pop_coords = np.column_stack([xs_p, ys_p])
total_pop = float(pop_vals.sum())
print(f'  Population cells: {len(pop_vals):,} | Total residents: {total_pop:,.0f}')
infra_gdf = gpd.read_file(str(DS03_INFRASTRUCTURE)).to_crs(epsg=32646)
wash_pts = np.column_stack([infra_gdf[infra_gdf['category'] == 'WASH_DRINKING_WATER'].geometry.x, infra_gdf[infra_gdf['category'] == 'WASH_DRINKING_WATER'].geometry.y])
shelter_pts = np.column_stack([infra_gdf[infra_gdf['category'] == 'EMERGENCY_SHELTER'].geometry.x, infra_gdf[infra_gdf['category'] == 'EMERGENCY_SHELTER'].geometry.y])
d_wash_dry, _ = cKDTree(wash_pts).query(pop_coords)
d_shelter_dry, _ = cKDTree(shelter_pts).query(pop_coords)
with rasterio.open(str(FLOOD_PROB_RASTER)) as src_prob:
    p_raw = np.array([v[0] for v in src_prob.sample(pop_coords)])
p_sampled = np.clip(np.where(p_raw == -9999.0, 0.0, p_raw), 0.0, 1.0)
SPEED_MS = DEII_WALKING_SPEED_KMH * 1000.0 / 3600.0
alpha = DEII_SCENARIOS['Baseline']['alpha']
tau = DEII_SCENARIOS['Baseline']['tau']
severed = p_sampled >= tau
d_wash_monsoon = d_wash_dry * (1.0 + alpha * p_sampled)
d_shelter_monsoon = d_shelter_dry * (1.0 + alpha * p_sampled)
d_wash_monsoon[severed] = 1000000000.0
d_shelter_monsoon[severed] = 1000000000.0
print('\n  Population catchment collapse (Baseline: α=3.0, τ=0.70):')
rows_tbl = []
for t_min in DEII_THRESHOLDS_MIN:
    t_m = t_min * 60 * SPEED_MS
    w_dry = float(pop_vals[d_wash_dry <= t_m].sum())
    w_mon = float(pop_vals[d_wash_monsoon <= t_m].sum())
    s_dry = float(pop_vals[d_shelter_dry <= t_m].sum())
    s_mon = float(pop_vals[d_shelter_monsoon <= t_m].sum())
    w_loss = w_dry - w_mon
    s_loss = s_dry - s_mon
    print(f'    {t_min:>2} min  WASH dry={w_dry:>9,.0f}  flood={w_mon:>9,.0f}  loss={w_loss:>9,.0f} ({w_loss / w_dry * 100:.1f}%)  | Shelter dry={s_dry:>9,.0f}  flood={s_mon:>9,.0f}  loss={s_loss:>9,.0f} ({s_loss / s_dry * 100:.1f}%)')
    rows_tbl.append({'Threshold': f'{t_min} min ({t_min * DEII_WALKING_SPEED_KMH / 60:.1f} km)', 'WASH Dry': int(round(w_dry)), 'WASH Flood': int(round(w_mon)), 'WASH Loss': int(round(w_loss)), 'WASH %': f'{w_loss / w_dry * 100:.1f}%', 'Shelter Dry': int(round(s_dry)), 'Shelter Flood': int(round(s_mon)), 'Shelter Loss': int(round(s_loss)), 'Shelter %': f'{s_loss / s_dry * 100:.1f}%'})
LANDFILLS = [('Aminbazar Landfill (DNCC)', 233000, 2634400), ('Matuail Landfill (DSCC)', 244450, 2623300)]
pop_tree = cKDTree(pop_coords)
print('\n  Landfill flood leachate exposure:')
lf_rows = []
for lf_name, lx, ly in LANDFILLS:
    idx_2km = pop_tree.query_ball_point((lx, ly), 2000.0)
    n_total = int(round(pop_vals[idx_2km].sum()))
    p_in = p_sampled[idx_2km]
    n_high = int(round(pop_vals[idx_2km][p_in >= 0.5].sum()))
    print(f'    {lf_name}: {n_total:,} residents within 2 km | {n_high:,} in high-hazard zone (P ≥ 0.50)')
    lf_rows.append({'Landfill': lf_name, 'Population (2 km)': n_total, 'High Hazard Pop': n_high})
combined_2km = int(round(sum((r['Population (2 km)'] for r in lf_rows))))
print(f'    Combined 2-km exposure: {combined_2km:,} residents (published: ~922,000)')
print('\n  Sensitivity analysis (3 disruption scenarios):')
sens_rows = []
for scenario, params in DEII_SCENARIOS.items():
    a, t = (params['alpha'], params['tau'])
    sev = p_sampled >= t
    d_wm = d_wash_dry * (1.0 + a * p_sampled)
    d_wm[sev] = 1000000000.0
    d_sm = d_shelter_dry * (1.0 + a * p_sampled)
    d_sm[sev] = 1000000000.0
    for t_min in [12, 24]:
        t_m = t_min * 60 * SPEED_MS
        w_dry = float(pop_vals[d_wash_dry <= t_m].sum())
        w_mon = float(pop_vals[d_wm <= t_m].sum())
        s_dry = float(pop_vals[d_shelter_dry <= t_m].sum())
        s_mon = float(pop_vals[d_sm <= t_m].sum())
        w_l = w_dry - w_mon
        s_l = s_dry - s_mon
        print(f'    {scenario:<9} α={a} τ={t}  {t_min}min  WASH_loss={w_l:,.0f}({w_l / w_dry * 100:.1f}%)  Shelter_loss={s_l:,.0f}({s_l / s_dry * 100:.1f}%)')
        sens_rows.append({'Scenario': scenario, 'α': a, 'τ': t, 'Threshold': f'{t_min} min', 'WASH Loss': int(round(w_l)), 'WASH %': f'{w_l / w_dry * 100:.1f}%', 'Shelter Loss': int(round(s_l)), 'Shelter %': f'{s_l / s_dry * 100:.1f}%'})
tbl = '# Table 3: Population Catchment Collapse & Landfill Leachate Exposure\n\n'
tbl += '## 3a. Catchment Collapse (Baseline: α=3.0, τ=0.70)\n\n'
tbl += '| Threshold | WASH Dry | WASH Flood | WASH Loss | % | Shelter Dry | Shelter Flood | Shelter Loss | % |\n'
tbl += '|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n'
for r in rows_tbl:
    tbl += f"| {r['Threshold']} | {r['WASH Dry']:,} | {r['WASH Flood']:,} | **{r['WASH Loss']:,}** | **{r['WASH %']}** | {r['Shelter Dry']:,} | {r['Shelter Flood']:,} | **{r['Shelter Loss']:,}** | **{r['Shelter %']}** |\n"
tbl += '\n## 3b. Landfill Leachate Exposure (2 km buffer)\n\n'
tbl += '| Landfill | Population (2 km) | High-Hazard Pop (P≥0.50) |\n|:---|:---:|:---:|\n'
for r in lf_rows:
    tbl += f"| {r['Landfill']} | {r['Population (2 km)']:,} | {r['High Hazard Pop']:,} |\n"
tbl += '\n## 3c. DEII Sensitivity Analysis\n\n'
tbl += '| Scenario | α | τ | Threshold | WASH Loss | WASH % | Shelter Loss | Shelter % |\n'
tbl += '|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n'
for r in sens_rows:
    tbl += f"| {r['Scenario']} | {r['α']} | {r['τ']} | {r['Threshold']} | {r['WASH Loss']:,} | {r['WASH %']} | {r['Shelter Loss']:,} | {r['Shelter %']} |\n"
TABLE3_CATCHMENT.write_text(tbl, encoding='utf-8')
print(f'\n[SUCCESS] Table 3 → {TABLE3_CATCHMENT}')
print('[STEP 5B COMPLETE]')
