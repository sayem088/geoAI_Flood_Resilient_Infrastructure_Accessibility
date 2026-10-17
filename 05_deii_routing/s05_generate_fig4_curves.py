import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS02_WORLDPOP, DS03_INFRASTRUCTURE, FLOOD_PROB_RASTER, FIG4_CURVES, DEII_WALKING_SPEED_KMH, DEII_SCENARIOS, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 5C: FIGURE 4 — CUMULATIVE CATCHMENT COLLAPSE CURVES')
print('=' * 75)
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
admin_union = admin_gdf.union_all()
with rasterio.open(str(DS02_WORLDPOP)) as src_pop:
    pop_masked, _ = rasterio_mask(src_pop, [admin_union], crop=False, nodata=-9999.0)
    pop_transform = src_pop.transform
pop_arr = pop_masked[0]
valid_pop = (pop_arr != -9999.0) & np.isfinite(pop_arr) & (pop_arr > 0)
rows, cols = np.where(valid_pop)
pop_vals = pop_arr[rows, cols]
xs, ys = rasterio.transform.xy(pop_transform, rows, cols)
pop_coords = np.column_stack([xs, ys])
print(f'  Loaded {len(pop_vals):,} populated cells representing {pop_vals.sum():,.0f} urban residents.')
infra_gdf = gpd.read_file(str(DS03_INFRASTRUCTURE)).to_crs(epsg=32646)
wash_gdf = infra_gdf[infra_gdf['category'] == 'WASH_DRINKING_WATER']
shelter_gdf = infra_gdf[infra_gdf['category'] == 'EMERGENCY_SHELTER']
wash_pts = np.column_stack([wash_gdf.geometry.x, wash_gdf.geometry.y])
shelter_pts = np.column_stack([shelter_gdf.geometry.x, shelter_gdf.geometry.y])
tree_wash = cKDTree(wash_pts)
tree_shelter = cKDTree(shelter_pts)
d_wash_dry, _ = tree_wash.query(pop_coords)
d_shelter_dry, _ = tree_shelter.query(pop_coords)
with rasterio.open(str(FLOOD_PROB_RASTER)) as src_prob:
    p_raw = np.array([v[0] for v in src_prob.sample(pop_coords)])
p_sampled = np.clip(np.where(p_raw == -9999.0, 0.0, p_raw), 0.0, 1.0)
alpha = DEII_SCENARIOS['Baseline']['alpha']
tau = DEII_SCENARIOS['Baseline']['tau']
severed = p_sampled >= tau
d_wash_monsoon = d_wash_dry * (1.0 + alpha * p_sampled)
d_shelter_monsoon = d_shelter_dry * (1.0 + alpha * p_sampled)
d_wash_monsoon[severed] = 1000000000.0
d_shelter_monsoon[severed] = 1000000000.0
print('Generating Figure 4: Cumulative Catchment Collapse Curves...')
dist_steps = np.linspace(100, 5000, 100)
w_dry_curve, w_mon_curve = ([], [])
s_dry_curve, s_mon_curve = ([], [])
for d in dist_steps:
    w_dry_curve.append(pop_vals[d_wash_dry <= d].sum() / 1000000.0)
    w_mon_curve.append(pop_vals[d_wash_monsoon <= d].sum() / 1000000.0)
    s_dry_curve.append(pop_vals[d_shelter_dry <= d].sum() / 1000000.0)
    s_mon_curve.append(pop_vals[d_shelter_monsoon <= d].sum() / 1000000.0)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
ax1.plot(dist_steps / 1000, w_dry_curve, color='#0284C7', linewidth=2.5, label='Dry Weather Baseline')
ax1.plot(dist_steps / 1000, w_mon_curve, color='#DC2626', linewidth=2.5, linestyle='--', label='Monsoon Inundation (DEII)')
ax1.fill_between(dist_steps / 1000, w_dry_curve, w_mon_curve, color='#EF4444', alpha=0.18, label='Catchment Collapse (Cut Off)')
w_2km_cutoff = pop_vals[d_wash_dry <= 2000].sum() - pop_vals[d_wash_monsoon <= 2000].sum()
ax1.axvline(2.0, color='#64748B', linestyle=':', linewidth=1.5)
ax1.annotate(f'2 km Service Limit\n{w_2km_cutoff:,.0f} Cut Off', xy=(2.0, 6.0), xytext=(2.2, 4.0), arrowprops=dict(facecolor='#1E293B', shrink=0.08, width=1, headwidth=5), fontsize=8.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.25', facecolor='#FEF3C7', edgecolor='#D97706'))
ax1.set_title('(a) Safe Drinking Water Points (WASH)', fontsize=11, fontweight='bold', pad=10)
ax1.set_xlabel('Travel Distance Threshold (km)', fontsize=9.5, fontweight='bold')
ax1.set_ylabel('Accessible Population (Millions)', fontsize=9.5, fontweight='bold')
ax1.set_xlim(0, 5)
ax1.set_ylim(0, 12)
ax1.grid(True, linestyle='--', alpha=0.4)
ax1.legend(loc='lower right', frameon=True, fontsize=8.5)
ax2.plot(dist_steps / 1000, s_dry_curve, color='#16A34A', linewidth=2.5, label='Dry Weather Baseline')
ax2.plot(dist_steps / 1000, s_mon_curve, color='#DC2626', linewidth=2.5, linestyle='--', label='Monsoon Inundation (DEII)')
ax2.fill_between(dist_steps / 1000, s_dry_curve, s_mon_curve, color='#EF4444', alpha=0.18, label='Catchment Collapse (Cut Off)')
s_2km_cutoff = pop_vals[d_shelter_dry <= 2000].sum() - pop_vals[d_shelter_monsoon <= 2000].sum()
ax2.axvline(2.0, color='#64748B', linestyle=':', linewidth=1.5)
ax2.annotate(f'2 km Service Limit\n{s_2km_cutoff:,.0f} Cut Off', xy=(2.0, 7.5), xytext=(2.2, 5.5), arrowprops=dict(facecolor='#1E293B', shrink=0.08, width=1, headwidth=5), fontsize=8.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.25', facecolor='#FEF3C7', edgecolor='#D97706'))
ax2.set_title('(b) Emergency Evacuation Shelters', fontsize=11, fontweight='bold', pad=10)
ax2.set_xlabel('Travel Distance Threshold (km)', fontsize=9.5, fontweight='bold')
ax2.set_ylabel('Accessible Population (Millions)', fontsize=9.5, fontweight='bold')
ax2.set_xlim(0, 5)
ax2.set_ylim(0, 12)
ax2.grid(True, linestyle='--', alpha=0.4)
ax2.legend(loc='lower right', frameon=True, fontsize=8.5)
plt.suptitle('Dynamic Environmental Inaccessibility Index (DEII): Catchment Collapse across Megacity Dhaka\n(Strict Urban Core: 11.72 Million Residents)', fontsize=12, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(str(FIG4_CURVES), dpi=300, bbox_inches='tight')
plt.close()
print(f'[SUCCESS] Figure 4 saved → {FIG4_CURVES}')
