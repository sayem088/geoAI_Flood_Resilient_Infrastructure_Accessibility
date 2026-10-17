import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import joblib
import shap
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import TRAINING_SAMPLES_GEOJSON, GEOAI_MODEL, FIG2_SHAP_BEESWARM, ensure_dirs
ensure_dirs()
print('=' * 65)
print('  STEP 3C: FIGURE 2 — TREESHAP BEESWARM FEATURE ATTRIBUTION')
print('=' * 65)
gdf = gpd.read_file(str(TRAINING_SAMPLES_GEOJSON))
FEATURES = ['elevation', 'slope', 'twi', 'impervious_fraction']
X = gdf[FEATURES].values
print(f'Loading production model from: {GEOAI_MODEL}')
model = joblib.load(str(GEOAI_MODEL))
print('Computing TreeSHAP values…')
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
mean_shap = np.mean(np.abs(shap_values), axis=0)
print('\n  Global Feature Importance (Mean |SHAP|):')
for feat, val in sorted(zip(FEATURES, mean_shap), key=lambda x: -x[1]):
    print(f'    {feat:<22}: {val:.4f}')
EXPECTED = {'impervious_fraction': 2.0095, 'elevation': 0.6601, 'slope': 0.1836, 'twi': 0.072}
print('\n  Validation against published paper values:')
for feat, val in zip(FEATURES, mean_shap):
    exp = EXPECTED.get(feat, None)
    if exp:
        tol = abs(exp) * 0.15
        flag = '✓' if abs(val - exp) < tol else f'⚠ expected {exp:.4f}'
        print(f'    {feat:<22}: {val:.4f}  {flag}')
fig = plt.figure(figsize=(9, 5), dpi=300)
shap.summary_plot(shap_values, X, feature_names=['Elevation (m)', 'Slope (°)', 'TWI', 'Impervious Fraction'], show=False, color_bar_label='Feature Value (Normalized)')
plt.title('TreeSHAP Global Summary: Feature Contributions to Urban Flood Susceptibility\nDhaka Urban Core (SCA26 / Springer LNNS) — N = 20,000 training points', fontsize=11, fontweight='bold', pad=14)
plt.tight_layout()
plt.savefig(str(FIG2_SHAP_BEESWARM), dpi=300, bbox_inches='tight')
plt.close()
print(f'\n[SUCCESS] Figure 2 → {FIG2_SHAP_BEESWARM}')
