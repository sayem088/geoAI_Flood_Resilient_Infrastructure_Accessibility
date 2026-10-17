import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score, roc_curve
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import TRAINING_SAMPLES_GEOJSON, FIG1_ROC_CURVES, XGB_PARAMS, RF_PARAMS, RANDOM_SEED, N_CV_FOLDS, ensure_dirs
ensure_dirs()
print('=' * 65)
print('  STEP 3B: FIGURE 1 — SPATIAL LEAKAGE ROC COMPARISON')
print('=' * 65)
gdf = gpd.read_file(str(TRAINING_SAMPLES_GEOJSON))
FEATURES = ['elevation', 'slope', 'twi', 'impervious_fraction']
X = gdf[FEATURES].values
y = gdf['flood_ground_truth'].values
blocks = gdf['spatial_block'].values
rkf = KFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
tr_r, te_r = next(rkf.split(X))
rf_rand = RandomForestClassifier(**RF_PARAMS).fit(X[tr_r], y[tr_r])
xgb_rand = xgb.XGBClassifier(**XGB_PARAMS).fit(X[tr_r], y[tr_r])
tr_s = blocks != 0
te_s = blocks == 0
rf_spat = RandomForestClassifier(**RF_PARAMS).fit(X[tr_s], y[tr_s])
xgb_spat = xgb.XGBClassifier(**XGB_PARAMS).fit(X[tr_s], y[tr_s])
fpr_rf_r, tpr_rf_r, _ = roc_curve(y[te_r], rf_rand.predict_proba(X[te_r])[:, 1])
fpr_xgb_r, tpr_xgb_r, _ = roc_curve(y[te_r], xgb_rand.predict_proba(X[te_r])[:, 1])
fpr_rf_s, tpr_rf_s, _ = roc_curve(y[te_s], rf_spat.predict_proba(X[te_s])[:, 1])
fpr_xgb_s, tpr_xgb_s, _ = roc_curve(y[te_s], xgb_spat.predict_proba(X[te_s])[:, 1])
auc_xgb_r = roc_auc_score(y[te_r], xgb_rand.predict_proba(X[te_r])[:, 1])
auc_rf_r = roc_auc_score(y[te_r], rf_rand.predict_proba(X[te_r])[:, 1])
auc_xgb_s = roc_auc_score(y[te_s], xgb_spat.predict_proba(X[te_s])[:, 1])
auc_rf_s = roc_auc_score(y[te_s], rf_spat.predict_proba(X[te_s])[:, 1])
block_names = {0: 'SW', 1: 'NW', 2: 'SE', 3: 'NE'}
quad_aucs: dict[int, float] = {}
for b in sorted(np.unique(blocks)):
    tr_b, te_b = (blocks != b, blocks == b)
    m = xgb.XGBClassifier(**XGB_PARAMS).fit(X[tr_b], y[tr_b])
    quad_aucs[b] = roc_auc_score(y[te_b], m.predict_proba(X[te_b])[:, 1])
spatial_mean_auc = float(np.mean(list(quad_aucs.values())))
random_mean_auc = auc_xgb_r
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
ax1.plot(fpr_xgb_r, tpr_xgb_r, color='#2563EB', lw=2.2, label=f'XGBoost Random 4-Fold (AUC={auc_xgb_r:.4f})')
ax1.plot(fpr_rf_r, tpr_rf_r, color='#3B82F6', lw=1.8, ls='--', label=f'Random Forest Random 4-Fold (AUC={auc_rf_r:.4f})')
ax1.plot(fpr_xgb_s, tpr_xgb_s, color='#DC2626', lw=2.2, label=f'XGBoost Spatial Block (AUC={auc_xgb_s:.4f})')
ax1.plot(fpr_rf_s, tpr_rf_s, color='#EA580C', lw=1.8, ls='--', label=f'Random Forest Spatial Block (AUC={auc_rf_s:.4f})')
ax1.plot([0, 1], [0, 1], color='#9CA3AF', ls=':')
ax1.set_title(f'(a) Spatial Data Leakage Gap: +{(random_mean_auc - spatial_mean_auc) * 100:.2f}% AUC Overestimation', fontsize=11, fontweight='bold')
ax1.set_xlabel('False Positive Rate', fontsize=10)
ax1.set_ylabel('True Positive Rate', fontsize=10)
ax1.legend(loc='lower right', fontsize=8.5)
ax1.grid(True, ls='--', alpha=0.3)
labels = [f'Block {b}\n({block_names[b]})' for b in sorted(quad_aucs)]
vals = [quad_aucs[b] for b in sorted(quad_aucs)]
colors = ['#0284C7', '#0EA5E9', '#38BDF8', '#7DD3FC']
bars = ax2.bar(labels, vals, color=colors, edgecolor='#0369A1', width=0.55)
ax2.axhline(spatial_mean_auc, color='#DC2626', ls='--', lw=1.5, label=f'Spatial Mean AUC = {spatial_mean_auc:.4f}')
ax2.axhline(random_mean_auc, color='#2563EB', ls=':', lw=1.5, label=f'Random Mean AUC  = {random_mean_auc:.4f}')
for bar in bars:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, h - 0.05, f'{h:.4f}', ha='center', va='bottom', color='white', fontweight='bold', fontsize=9.5)
ax2.set_title('(b) Spatial Transferability Across Dhaka Quadrants (XGBoost)', fontsize=11, fontweight='bold')
ax2.set_ylabel('ROC-AUC Score', fontsize=10)
ax2.set_ylim(0.7, 1.0)
ax2.legend(loc='lower right', fontsize=8.5)
ax2.grid(True, ls='--', alpha=0.3)
plt.tight_layout()
plt.savefig(str(FIG1_ROC_CURVES), dpi=300, bbox_inches='tight')
plt.close()
print(f'[SUCCESS] Figure 1 → {FIG1_ROC_CURVES}')
