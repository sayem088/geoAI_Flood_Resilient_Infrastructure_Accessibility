import subprocess, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
HERE = Path(__file__).parent
SCRIPTS = [HERE / 's03_train_xgboost_rf_cv.py', HERE / 's03_generate_fig1_roc_curves.py', HERE / 's03_generate_fig2_shap_beeswarm.py']

def run(script):
    print(f"\n{'=' * 60}\n  RUNNING -> {script.name}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(script)])
    if r.returncode != 0:
        sys.exit(f'\n[FAILED] {script.name}')
print('\n' + '=' * 60)
print('  MASTER STEP 03: GEOAI MODELING')
print('=' * 60)
for s in SCRIPTS:
    run(s)
print('\n' + '=' * 60)
print('  [SUCCESS] STEP 03 COMPLETE -- Model, Fig1, Fig2, Table1 ready.')
print('=' * 60)
