import argparse
import subprocess
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
HERE = Path(__file__).parent
SCRIPTS_ALWAYS = [HERE / 's01_preprocess_admin_boundary.py', HERE / 's01_preprocess_population.py', HERE / 's01_preprocess_dem_slope_twi.py', HERE / 's01_preprocess_infrastructure.py', HERE / 's01_audit_datasets.py']
SCRIPTS_GEE = [HERE / 's01_gee_download_dem_lulc_sar.py', HERE / 's01_osm_extract_infrastructure.py']

def run(script: Path) -> None:
    print(f"\n{'=' * 60}")
    print(f'  RUNNING -> {script.name}')
    print(f"{'=' * 60}")
    result = subprocess.run([sys.executable, str(script)])
    if result.returncode != 0:
        sys.exit(f'\n[FAILED] {script.name} exited with code {result.returncode}. Aborting Step 01.')

def main() -> None:
    parser = argparse.ArgumentParser(description='Step 01: Data Collection')
    parser.add_argument('--skip-gee', action='store_true', help='Skip GEE + OSM network downloads (if datasets already exist locally)')
    args = parser.parse_args()
    print('\n' + '=' * 60)
    print('  MASTER STEP 01: DATA COLLECTION PIPELINE')
    print('=' * 60)
    if not args.skip_gee:
        for s in SCRIPTS_GEE:
            run(s)
    else:
        print('[INFO] --skip-gee: skipping GEE and OSM downloads.')
    for s in SCRIPTS_ALWAYS:
        run(s)
    print('\n' + '=' * 60)
    print('  ✓  STEP 01 COMPLETE — All 6 datasets verified.')
    print('=' * 60)
if __name__ == '__main__':
    main()
