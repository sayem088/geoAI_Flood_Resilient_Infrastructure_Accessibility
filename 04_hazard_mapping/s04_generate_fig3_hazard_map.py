import os
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import rasterio
from rasterio.mask import mask as rasterio_mask
import contextily as cx
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import DS01_ADMIN_BOUNDARY, DS03_INFRASTRUCTURE, FLOOD_PROB_RASTER, FIG3_HAZARD_MAP, TABLE2_ZONAL_STATS, ensure_dirs
ensure_dirs()
print('=' * 65)
print('  STEP 4B: FIGURE 3 — FLOOD HAZARD CARTOGRAPHIC MAP')
print('=' * 65)
admin_gdf = gpd.read_file(str(DS01_ADMIN_BOUNDARY)).to_crs(epsg=32646)
admin_union = admin_gdf.union_all()
with rasterio.open(str(FLOOD_PROB_RASTER)) as src:
    meta = src.meta.copy()
    transform = src.transform
    height, width = src.shape
    prob_map = src.read(1)
valid_mask = (prob_map != -9999.0) & np.isfinite(prob_map) & (prob_map >= 0)
prob_valid = prob_map[valid_mask]
zonal = []
for _, row in admin_gdf.iterrows():
    with rasterio.open(str(FLOOD_PROB_RASTER)) as src:
        c_data, _ = rasterio_mask(src, [row.geometry], crop=True)
    v = c_data[0]
    v = v[(v != -9999.0) & np.isfinite(v) & (v >= 0)]
    if len(v):
        area_km2 = len(v) * 0.0009
        zonal.append({'City Corporation': row['adm3_name'], 'Area (km²)': area_km2, 'Mean P_flood': float(v.mean()), 'High Hazard km²': float((v >= 0.5).sum() * 0.0009), 'High Hazard %': float((v >= 0.5).sum() / len(v) * 100)})
        print(f"  {row['adm3_name']}: {area_km2:.2f} km² | Mean P={v.mean():.3f} | High {(v >= 0.5).sum() * 0.0009:.2f} km²")
hazard_cmap = mcolors.LinearSegmentedColormap.from_list('hazard', ['#10B981', '#FBBF24', '#F97316', '#DC2626', '#7F1D1D'], N=256)
hazard_cmap.set_bad(alpha=0.0)
fig, ax = plt.subplots(figsize=(11, 13), dpi=300)
bounds = admin_gdf.total_bounds
pad = 1500
ax.set_xlim(bounds[0] - pad, bounds[2] + pad)
ax.set_ylim(bounds[1] - pad, bounds[3] + pad)
try:
    cx.add_basemap(ax, crs='EPSG:32646', source=cx.providers.Esri.WorldGrayCanvas, alpha=0.9, zorder=1)
    print('  Basemap: Esri WorldGrayCanvas loaded.')
except Exception as e:
    print(f'  Basemap warning: {e}')
extent = [transform[2], transform[2] + width * transform[0], transform[5] + height * transform[4], transform[5]]
masked_prob = np.ma.masked_where((prob_map == -9999.0) | ~valid_mask, prob_map)
im = ax.imshow(masked_prob, extent=extent, cmap=hazard_cmap, vmin=0.0, vmax=0.85, alpha=0.78, zorder=2)
admin_gdf.boundary.plot(ax=ax, color='#1E293B', lw=1.6, ls='-', zorder=4)
for _, row in admin_gdf.iterrows():
    pt = row.geometry.representative_point()
    name = 'Dhaka North City Corp (DNCC)' if 'North' in row['adm3_name'] else 'Dhaka South City Corp (DSCC)'
    y_off = 1800 if 'North' in row['adm3_name'] else -1200
    ax.annotate(name, xy=(pt.x, pt.y + y_off), ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F172A', bbox=dict(boxstyle='square,pad=0.35', fc='#F8FAFC', ec='#334155', lw=1.2, alpha=0.92), zorder=6)
LANDMARKS = [('Uttara', 239000, 2641500), ('Mirpur', 233500, 2633000), ('Pallabi', 234500, 2636500), ('Gulshan', 240500, 2632500), ('Banani', 239000, 2632500), ('Mohammadpur', 233500, 2628500), ('Tejgaon', 238000, 2629000), ('Badda', 242000, 2630500), ('Khilkhet', 242000, 2637000), ('Dhanmondi', 236000, 2626000), ('Motijheel', 240000, 2624500), ('Shahbagh', 238000, 2625500), ('Old Dhaka', 238500, 2622500), ('Lalbagh', 236500, 2622500), ('Kamrangirchar', 234000, 2621500), ('Jatrabari', 243000, 2621500), ('Demra', 245500, 2625000)]
for name, lx, ly in LANDMARKS:
    ax.scatter(lx, ly, s=20, color='#1E293B', marker='o', zorder=5)
    ax.annotate(name, xy=(lx, ly), xytext=(4, 4), textcoords='offset points', fontsize=7.5, fontweight='bold', color='#1E293B', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#94A3B8', alpha=0.88), zorder=6)
for r_name, rx, ry, rot in [('Turag River', 230500, 2636000, -65), ('Buriganga River', 236500, 2620000, 15), ('Balu River', 245000, 2638000, 70)]:
    ax.text(rx, ry, r_name, fontsize=8.5, fontweight='bold', fontstyle='italic', color='#0284C7', rotation=rot, ha='center', va='center', zorder=5, bbox=dict(boxstyle='round,pad=0.2', fc='#F0F9FF', ec='#BAE6FD', alpha=0.85))
for lf_name, lfx, lfy in [('Aminbazar Landfill', 233000, 2634400), ('Matuail Landfill', 244450, 2623300)]:
    ax.scatter(lfx, lfy, s=90, color='#DC2626', marker='s', edgecolors='black', lw=1.5, zorder=7)
    ax.annotate(f'{lf_name}\n[Toxic Leachate Risk]', xy=(lfx, lfy), xytext=(12, -15), textcoords='offset points', fontsize=7.5, fontweight='bold', color='#991B1B', arrowprops=dict(fc='#DC2626', shrink=0.08, width=1, headwidth=5), bbox=dict(boxstyle='round,pad=0.25', fc='#FEF2F2', ec='#EF4444', alpha=0.95), zorder=8)
cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02, shrink=0.75)
cbar.set_label('GeoAI Flood Hazard Susceptibility ($P_{flood}$)', fontsize=9.5, fontweight='bold', labelpad=8)
cbar.ax.tick_params(labelsize=8.5)
ax.set_title('Dhaka Megacity Urban Core: Continuous Flood Hazard Susceptibility Map (30m Grid)\nStrict Jurisdiction: Dhaka North (DNCC) & Dhaka South (DSCC) City Corporations (304.51 km²)', fontsize=11.5, fontweight='bold', pad=12)
ax.set_xlabel('UTM Zone 46N Easting (meters)', fontsize=9)
ax.set_ylabel('UTM Zone 46N Northing (meters)', fontsize=9)
ax.grid(color='#94A3B8', ls=':', lw=0.5, alpha=0.4, zorder=3)
try:
    raw_p = DS01_ADMIN_BOUNDARY.parent.parent / 'data' / 'raw' / 'admin_boundary.geojson'
    if raw_p.exists():
        ax_ins = inset_axes(ax, width='25%', height='25%', loc='lower left', borderpad=2)
        raw_gdf = gpd.read_file(str(raw_p)).to_crs(epsg=32646)
        dhaka_dist = raw_gdf[raw_gdf['adm2_name'] == 'Dhaka']
        dhaka_dist.plot(ax=ax_ins, color='#E2E8F0', edgecolor='#64748B', lw=0.6)
        admin_gdf.plot(ax=ax_ins, color='#DC2626', edgecolor='#991B1B', lw=1.0)
        ax_ins.set_title('Study Area in Dhaka District', fontsize=7, fontweight='bold', pad=2)
        ax_ins.set_xticks([])
        ax_ins.set_yticks([])
except Exception as e:
    print(f'  Inset map: {e}')
plt.tight_layout()
plt.savefig(str(FIG3_HAZARD_MAP), dpi=300, bbox_inches='tight')
plt.close()
print(f'[SUCCESS] Figure 3 → {FIG3_HAZARD_MAP}')
tbl = '# Table 2: Zonal Flood Hazard Statistics — DNCC & DSCC\n\n'
tbl += '| City Corporation | Area (km²) | Mean P_flood | High Hazard (≥0.50) km² | High Hazard % |\n'
tbl += '|:---|:---:|:---:|:---:|:---:|\n'
for z in zonal:
    tbl += f"| **{z['City Corporation']}** | {z['Area (km²)']:.2f} | {z['Mean P_flood']:.3f} | {z['High Hazard km²']:.2f} | {z['High Hazard %']:.1f}% |\n"
total_area = sum((z['Area (km²)'] for z in zonal))
total_high = sum((z['High Hazard km²'] for z in zonal))
tbl += f'| **Combined Urban Core** | {total_area:.2f} | {float(np.mean(prob_valid)):.3f} | {total_high:.2f} | {total_high / total_area * 100:.1f}% |\n'
tbl += '\n*XGBoost wall-to-wall inference at 30m on DNCC + DSCC dry-land pixels.*\n'
TABLE2_ZONAL_STATS.write_text(tbl, encoding='utf-8')
print(f'[SUCCESS] Table 2 → {TABLE2_ZONAL_STATS}')
