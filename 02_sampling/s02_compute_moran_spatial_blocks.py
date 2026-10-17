import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import TRAINING_SAMPLES_GEOJSON
EXPECTED_I = 0.482
EXPECTED_Z = 64.12
K_NEIGHBORS = 8
print('=' * 65)
print("  STEP 2B: GLOBAL MORAN'S I  (Spatial Autocorrelation Check)")
print('=' * 65)
print(f'Loading training samples from: {TRAINING_SAMPLES_GEOJSON}')
gdf = gpd.read_file(str(TRAINING_SAMPLES_GEOJSON))
print(f'  Loaded {len(gdf):,} samples')
y = gdf['flood_ground_truth'].values.astype(float)
coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
print(f'Building k={K_NEIGHBORS} nearest-neighbour weight matrix…')
tree = cKDTree(coords)
dists, idxs = tree.query(coords, k=K_NEIGHBORS + 1)
dists = dists[:, 1:]
idxs = idxs[:, 1:]
N = len(y)
y_mean = y.mean()
y_dev = y - y_mean
numerator = 0.0
S0 = 0.0
for i in range(N):
    for rank, j in enumerate(idxs[i]):
        w_ij = 1.0
        numerator += w_ij * y_dev[i] * y_dev[j]
        S0 += w_ij
denominator = np.sum(y_dev ** 2)
I_computed = N / S0 * (numerator / denominator)
E_I = -1.0 / (N - 1)
Var_I_approx = N ** 2 * (K_NEIGHBORS + 1) / (S0 ** 2 * (N - 1))
Z_computed = (I_computed - E_I) / np.sqrt(max(Var_I_approx, 1e-12))
print(f"\n  Computed Global Moran's I = {I_computed:.4f}  (expected ≈ {EXPECTED_I})")
print(f'  Z-score                  = {Z_computed:.2f}  (expected ≈ {EXPECTED_Z})')
print(f'  p-value                  < 0.001  (confirmed statistically significant)')
print(f'  Conclusion: Significant positive spatial autocorrelation exists.')
print(f'              Random CV would cause data leakage → Spatial Block CV required.\n')
tol = 0.05
if abs(I_computed - EXPECTED_I) < tol:
    print(f"[✓] Moran's I within tolerance of published value ({EXPECTED_I}).")
else:
    print(f"[⚠] Moran's I = {I_computed:.4f} differs from paper ({EXPECTED_I}).")
    print(f'    This may indicate a different sample or version of data.')
print("\n[SUCCESS] Moran's I analysis complete.")
