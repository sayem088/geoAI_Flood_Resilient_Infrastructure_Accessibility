import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DATASETS_DIR = DATA_DIR / 'datasets'
PROCESSED = DATA_DIR / 'processed'
OUTPUTS = ROOT / 'outputs'
FIGURES = OUTPUTS / 'figures'
TABLES = OUTPUTS / 'tables'
DS01_ADMIN_BOUNDARY = DATASETS_DIR / 'ds_01_admin_boundary.geojson'
DS02_WORLDPOP = DATASETS_DIR / 'ds_02_population_worldpop_100m.tif'
DS03_INFRASTRUCTURE = DATASETS_DIR / 'ds_03_critical_environmental_infrastructure.geojson'
DS04_DEM = DATASETS_DIR / 'ds_04_copernicus_dem_30m.tif'
DS05_LULC = DATASETS_DIR / 'ds_05_dynamic_world_lulc_30m.tif'
DS06_SAR = DATASETS_DIR / 'ds_06_sentinel1_sar_flood_extent_30m.tif'
TRAINING_SAMPLES_GEOJSON = PROCESSED / 'dhaka_flood_training_samples.geojson'
TRAINING_SAMPLES_CSV = PROCESSED / 'dhaka_flood_training_samples.csv'
GEOAI_MODEL = PROCESSED / 'geoai_flood_model.joblib'
FLOOD_PROB_RASTER = PROCESSED / 'dhaka_flood_susceptibility_probability_30m.tif'
DEII_RASTER = PROCESSED / 'dhaka_deii_accessibility_30m.tif'
FIG1_ROC_CURVES = FIGURES / 'fig1_spatial_leakage_comparison.png'
FIG2_SHAP_BEESWARM = FIGURES / 'fig2_shap_beeswarm.png'
FIG3_HAZARD_MAP = FIGURES / 'fig3_dhaka_flood_susceptibility_map.png'
FIG4_CURVES = FIGURES / 'fig4_catchment_collapse_curves.png'
FIG5_LANDFILL = FIGURES / 'fig5_landfill_leachate_exposure.png'
TABLE1_BENCHMARK = TABLES / 'table_1_model_benchmark.md'
TABLE2_ZONAL_STATS = TABLES / 'table_2_thana_flood_hazard_zonal_stats.md'
TABLE3_CATCHMENT = TABLES / 'table_3_catchment_collapse_and_leachate.md'
TABLE4_DEII_SENSITIVITY = TABLES / 'table_4_thana_deii_travel_distances.md'
TABLE5_CORP_BREAKDOWN = TABLES / 'table_5_thana_population_catchment_collapse.md'
GEE_PROJECT_ID = 'sundarban-489216'
GEE_BBOX_WGS84 = [90.32, 23.66, 90.52, 23.91]
MONSOON_START = '2022-07-01'
MONSOON_END = '2022-08-31'
PRE_MONSOON_START = '2022-01-01'
PRE_MONSOON_END = '2022-04-30'
TARGET_CRS = 'EPSG:32646'
TARGET_SCALE = 30
STUDY_AREA_KM2 = 304.51
TOTAL_POPULATION = 11722702
N_THANAS = 2
XGB_PARAMS = {'n_estimators': 200, 'learning_rate': 0.08, 'max_depth': 6, 'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 3, 'reg_lambda': 1.5, 'use_label_encoder': False, 'eval_metric': 'logloss', 'random_state': 42}
RF_PARAMS = {'n_estimators': 100, 'max_depth': 10, 'n_jobs': -1, 'random_state': 42}
SAMPLE_SIZE = 20000
RANDOM_SEED = 42
N_CV_FOLDS = 4
DEII_ALPHA_BASELINE = 3.0
DEII_GAMMA_BASELINE = 1.0
DEII_TAU_BASELINE = 0.7
DEII_WALKING_SPEED_KMH = 5.0
DEII_THRESHOLDS_MIN = [6, 12, 24, 36]
DEII_SCENARIOS = {'Mild': {'alpha': 1.0, 'gamma': 1.0, 'tau': 0.8}, 'Baseline': {'alpha': 3.0, 'gamma': 1.0, 'tau': 0.7}, 'Severe': {'alpha': 5.0, 'gamma': 1.0, 'tau': 0.6}}
SAR_DELTA_VH_THRESHOLD = -1.5
SAR_PERM_WATER_THRESHOLD = -18.0

def ensure_dirs() -> None:
    for d in [DATASETS_DIR, PROCESSED, FIGURES, TABLES]:
        d.mkdir(parents=True, exist_ok=True)
