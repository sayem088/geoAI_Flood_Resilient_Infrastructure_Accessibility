import numpy as np
import pandas as pd
import geopandas as gpd
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, brier_score_loss
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from config import TRAINING_SAMPLES_GEOJSON, GEOAI_MODEL, XGB_PARAMS, RF_PARAMS, RANDOM_SEED, N_CV_FOLDS, TABLE1_BENCHMARK, ensure_dirs
ensure_dirs()
print('=' * 75)
print('  STEP 3A: GEOAI SPATIAL MODELING — RANDOM vs. SPATIAL BLOCK CV')
print('=' * 75)
gdf = gpd.read_file(str(TRAINING_SAMPLES_GEOJSON))
print(f'Loaded {len(gdf):,} training samples')
FEATURES = ['elevation', 'slope', 'twi', 'impervious_fraction']
TARGET = 'flood_ground_truth'
X = gdf[FEATURES].values
y = gdf[TARGET].values
blocks = gdf['spatial_block'].values
print(f'  Features: {FEATURES}')
print(f'  Flooded={np.sum(y == 1):,}  Non-Flooded={np.sum(y == 0):,}')

def evaluate(y_true, y_prob, threshold: float=0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    return {'auc': roc_auc_score(y_true, y_prob), 'f1': f1_score(y_true, y_pred, zero_division=0), 'precision': precision_score(y_true, y_pred, zero_division=0), 'recall': recall_score(y_true, y_pred, zero_division=0), 'brier': brier_score_loss(y_true, y_prob)}

def mean_metrics(m_list: list[dict]) -> dict:
    return {k: float(np.mean([m[k] for m in m_list])) for k in m_list[0]}
print('\n' + '-' * 75)
print('  [PROTOCOL A] STANDARD RANDOM 4-FOLD CV  (naive / leaking)')
print('-' * 75)
rkf = KFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
rf_rand, xgb_rand = ([], [])
for fold, (tr, te) in enumerate(rkf.split(X)):
    rf = RandomForestClassifier(**RF_PARAMS).fit(X[tr], y[tr])
    xgb_m = xgb.XGBClassifier(**XGB_PARAMS).fit(X[tr], y[tr])
    rf_rand.append(evaluate(y[te], rf.predict_proba(X[te])[:, 1]))
    xgb_rand.append(evaluate(y[te], xgb_m.predict_proba(X[te])[:, 1]))
rf_rand_m = mean_metrics(rf_rand)
xgb_rand_m = mean_metrics(xgb_rand)
print(f"RF   Random: AUC={rf_rand_m['auc']:.4f}  F1={rf_rand_m['f1']:.4f}")
print(f"XGB  Random: AUC={xgb_rand_m['auc']:.4f}  F1={xgb_rand_m['f1']:.4f}")
print('\n' + '-' * 75)
print('  [PROTOCOL B] SPATIAL BLOCK 4-FOLD CV  (geospatially rigorous)')
print('-' * 75)
unique_blocks = np.unique(blocks)
rf_spat, xgb_spat = ([], [])
xgb_quad_aucs: dict[int, float] = {}
block_names = {0: 'SW', 1: 'NW', 2: 'SE', 3: 'NE'}
for b in unique_blocks:
    tr_m, te_m = (blocks != b, blocks == b)
    rf_s = RandomForestClassifier(**RF_PARAMS).fit(X[tr_m], y[tr_m])
    xgb_s = xgb.XGBClassifier(**XGB_PARAMS).fit(X[tr_m], y[tr_m])
    m_rf = evaluate(y[te_m], rf_s.predict_proba(X[te_m])[:, 1])
    m_xgb = evaluate(y[te_m], xgb_s.predict_proba(X[te_m])[:, 1])
    rf_spat.append(m_rf)
    xgb_spat.append(m_xgb)
    xgb_quad_aucs[b] = m_xgb['auc']
    print(f"  Block {b} ({block_names.get(b, '?'):>2}, n={te_m.sum():,})  RF={m_rf['auc']:.4f}  XGB={m_xgb['auc']:.4f}")
rf_spat_m = mean_metrics(rf_spat)
xgb_spat_m = mean_metrics(xgb_spat)
print(f"\nRF  Spatial Block: AUC={rf_spat_m['auc']:.4f} ± {np.std([m['auc'] for m in rf_spat]):.4f}")
print(f"XGB Spatial Block: AUC={xgb_spat_m['auc']:.4f} ± {np.std([m['auc'] for m in xgb_spat]):.4f}")
rf_gap = rf_rand_m['auc'] - rf_spat_m['auc']
xgb_gap = xgb_rand_m['auc'] - xgb_spat_m['auc']
print('\n' + '=' * 75)
print('  SPATIAL OPTIMISM GAP SUMMARY  (paper §4.1)')
print('=' * 75)
print(f"  RF   ΔAU = +{rf_gap:.4f}  ({rf_spat_m['auc']:.4f} → {rf_rand_m['auc']:.4f})  expected ≈ 0.0597")
print(f"  XGB  ΔAU = +{xgb_gap:.4f}  ({xgb_spat_m['auc']:.4f} → {xgb_rand_m['auc']:.4f})  expected ≈ 0.0571")
print('\nTraining final production XGBoost model (all data, n=20,000)…')
final_xgb = xgb.XGBClassifier(**XGB_PARAMS)
final_xgb.fit(X, y)
joblib.dump(final_xgb, str(GEOAI_MODEL))
print(f'[SUCCESS] Production model saved → {GEOAI_MODEL}')
xgb_std = float(np.std([m['auc'] for m in xgb_spat]))
rf_std = float(np.std([m['auc'] for m in rf_spat]))
tbl = f"# Table 1: Comparative Evaluation — Random vs. Spatial Block CV\n\n| Algorithm | Validation | ROC-AUC | F1 | Prec. | Recall | Brier | ΔAUC |\n|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|\n| Random Forest | Random 4-Fold | {rf_rand_m['auc']:.4f} | {rf_rand_m['f1']:.4f} | {rf_rand_m['precision']:.4f} | {rf_rand_m['recall']:.4f} | {rf_rand_m['brier']:.4f} | — |\n| | Spatial Block 4-Fold | {rf_spat_m['auc']:.4f} ± {rf_std:.4f} | {rf_spat_m['f1']:.4f} | {rf_spat_m['precision']:.4f} | {rf_spat_m['recall']:.4f} | {rf_spat_m['brier']:.4f} | **+{rf_gap:.4f}** |\n| XGBoost | Random 4-Fold | {xgb_rand_m['auc']:.4f} | {xgb_rand_m['f1']:.4f} | {xgb_rand_m['precision']:.4f} | {xgb_rand_m['recall']:.4f} | {xgb_rand_m['brier']:.4f} | — |\n| | Spatial Block 4-Fold | {xgb_spat_m['auc']:.4f} ± {xgb_std:.4f} | {xgb_spat_m['f1']:.4f} | {xgb_spat_m['precision']:.4f} | {xgb_spat_m['recall']:.4f} | {xgb_spat_m['brier']:.4f} | **+{xgb_gap:.4f}** |\n\nPer-block XGBoost AUC: {' | '.join((f'Block {b}({block_names[b]})={xgb_quad_aucs[b]:.4f}' for b in sorted(xgb_quad_aucs)))}\n\n*N = {len(gdf):,} points (1:1 balanced, seed={RANDOM_SEED}). Study area: 304.51 km² (DNCC + DSCC).*\n"
TABLE1_BENCHMARK.parent.mkdir(parents=True, exist_ok=True)
TABLE1_BENCHMARK.write_text(tbl, encoding='utf-8')
print(f'[SUCCESS] Table 1 → {TABLE1_BENCHMARK}')
print('\n[STEP 3A COMPLETE] GeoAI benchmark and production model ready.')
