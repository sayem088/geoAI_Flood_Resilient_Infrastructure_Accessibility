import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rasterio_mask
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS02_WORLDPOP, FLOOD_PROB_RASTER, FIG5_LANDFILL, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 5D: FIGURE 5 — LANDFILL LEACHATE EXPOSURE MAP')
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
with rasterio.open(str(FLOOD_PROB_RASTER)) as src_prob:
    p_raw = np.array([v[0] for v in src_prob.sample(pop_coords)])
p_sampled = np.clip(np.where(p_raw == -9999.0, 0.0, p_raw), 0.0, 1.0)
landfills = [('Aminbazar Landfill (DNCC)', 233000, 2634400), ('Matuail Landfill (DSCC)', 244450, 2623300)]
print('Generating Figure 5: Landfill Leachate Exposure Map...')
fig, ax = plt.subplots(figsize=(10, 11), dpi=300)
bounds = admin_gdf.total_bounds
pad_x = 1500
pad_y = 1500
ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)
try:
    import contextily as cx
    cx.add_basemap(ax, crs='EPSG:32646', source=cx.providers.Esri.WorldGrayCanvas, alpha=0.9, zorder=1)
    print('  Added Esri WorldGrayCanvas basemap successfully.')
except Exception as e:
    print(f'  [NOTE] Basemap skipped ({e}); rendering without background tiles.')
sc = ax.scatter(xs, ys, c=p_sampled, cmap='YlOrRd', s=2.5, alpha=0.65, zorder=2, vmin=0.0, vmax=0.85)
admin_gdf.boundary.plot(ax=ax, color='#1E293B', linewidth=1.4, linestyle='-', zorder=4)
for lf_name, lx, ly in landfills:
    for r_km, col, ls, lw in [(1.0, '#DC2626', '-', 2.2), (2.0, '#EA580C', '--', 1.8), (3.0, '#CA8A04', ':', 1.5)]:
        circle = plt.Circle((lx, ly), r_km * 1000, color=col, fill=False, linestyle=ls, linewidth=lw, zorder=5)
        ax.add_patch(circle)
    ax.scatter(lx, ly, s=120, color='#7F1D1D', marker='s', edgecolors='black', linewidth=1.5, zorder=7)
    y_shift = 15 if 'Aminbazar' in lf_name else -25
    ax.annotate(f'{lf_name}\n[Active Landfill]', xy=(lx, ly), xytext=(12, y_shift), textcoords='offset points', fontsize=8, fontweight='bold', color='#7F1D1D', arrowprops=dict(facecolor='#7F1D1D', shrink=0.08, width=1, headwidth=5), bbox=dict(boxstyle='round,pad=0.25', facecolor='#FEF2F2', edgecolor='#EF4444', alpha=0.92), zorder=8)
landmarks = [('Mirpur', 233500, 2633000), ('Uttara', 239000, 2641500), ('Gulshan', 240500, 2632500), ('Mohammadpur', 233500, 2628500), ('Dhanmondi', 236000, 2626000), ('Motijheel', 240000, 2624500), ('Old Dhaka', 238500, 2622500), ('Demra', 245500, 2625000), ('Jatrabari', 243000, 2621500)]
for lname, lx, ly in landmarks:
    ax.annotate(lname, xy=(lx, ly), fontsize=7.5, fontweight='bold', color='#1E293B', bbox=dict(boxstyle='round,pad=0.18', facecolor='white', edgecolor='#94A3B8', alpha=0.88), zorder=6)
ax.plot([], [], color='#DC2626', linestyle='-', linewidth=2.2, label='1.0 km Critical Leachate Zone')
ax.plot([], [], color='#EA580C', linestyle='--', linewidth=1.8, label='2.0 km Secondary Inundation Buffer')
ax.plot([], [], color='#CA8A04', linestyle=':', linewidth=1.5, label='3.0 km Extended Dispersion Buffer')
cbar = plt.colorbar(sc, ax=ax, fraction=0.035, pad=0.02, shrink=0.75)
cbar.set_label('Flood Hazard Susceptibility ($P_{flood}$)', fontsize=9, fontweight='bold')
cbar.ax.tick_params(labelsize=8.5)
ax.set_title('Environmental Justice & Toxic Landfill Leachate Exposure Zones\nAminbazar Landfill (DNCC) & Matuail Landfill (DSCC) Buffer Radii (EPSG:32646)', fontsize=11, fontweight='bold', pad=12)
ax.set_xlabel('UTM Zone 46N Easting (meters)', fontsize=8.5)
ax.set_ylabel('UTM Zone 46N Northing (meters)', fontsize=8.5)
ax.legend(loc='lower left', frameon=True, fontsize=8, framealpha=0.92)
ax.grid(color='#94A3B8', linestyle=':', linewidth=0.5, alpha=0.35, zorder=3)
plt.tight_layout()
plt.savefig(str(FIG5_LANDFILL), dpi=300, bbox_inches='tight')
plt.close()
print(f'[SUCCESS] Figure 5 saved → {FIG5_LANDFILL}')
