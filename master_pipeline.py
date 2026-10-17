import argparse
import subprocess
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
ROOT = Path(__file__).parent
STEPS: dict[int, dict] = {1: {'name': 'Data Collection', 'master': ROOT / '01_data_collection' / 'master_step_01.py', 'extra_args_key': 'skip_gee'}, 2: {'name': 'Sample Extraction', 'master': ROOT / '02_sampling' / 'master_step_02.py'}, 3: {'name': 'GeoAI Modeling', 'master': ROOT / '03_modeling' / 'master_step_03.py'}, 4: {'name': 'Hazard Mapping', 'master': ROOT / '04_hazard_mapping' / 'master_step_04.py'}, 5: {'name': 'DEII Routing & Accessibility', 'master': ROOT / '05_deii_routing' / 'master_step_05.py'}}

def run_step(step_num: int, skip_gee: bool=False) -> None:
    info = STEPS[step_num]
    print(f"\n{'#' * 70}")
    print(f"  STEP {step_num:02d}: {info['name']}")
    print(f"{'#' * 70}")
    cmd = [sys.executable, str(info['master'])]
    if skip_gee and info.get('extra_args_key') == 'skip_gee':
        cmd.append('--skip-gee')
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"\n[PIPELINE ABORTED] Step {step_num} ({info['name']}) failed.")

def main() -> None:
    parser = argparse.ArgumentParser(description='GeoAI Flood Dhaka SCA26 — Full Reproducibility Pipeline')
    parser.add_argument('--step', type=int, default=None, help='Run only this specific step number (1–5).')
    parser.add_argument('--from', dest='from_step', type=int, default=1, help='Resume from this step number (default: 1 = full run).')
    parser.add_argument('--skip-gee', action='store_true', help='Skip GEE/OSM network downloads in Step 01.')
    args = parser.parse_args()
    print('\n' + '=' * 70)
    print('   GeoAI Flood Dhaka — SCA26 Reproducibility Pipeline')
    print('=' * 70)
    print('   Paper: Flood Resilient Infrastructure Accessibility in')
    print('          Megacity Dhaka: A Spatially Constrained GeoAI Approach')
    print('   Conference: SCA26 / Springer LNNS / 2026')
    print('=' * 70)
    if args.step:
        if args.step not in STEPS:
            sys.exit(f'Invalid step: {args.step}. Choose 1–5.')
        run_step(args.step, skip_gee=args.skip_gee)
    else:
        start = args.from_step
        if start not in STEPS:
            sys.exit(f'Invalid --from step: {start}. Choose 1–5.')
        for step_num in range(start, 6):
            run_step(step_num, skip_gee=args.skip_gee)
    print('\n' + '=' * 70)
    print('   ✓  PIPELINE COMPLETE — All outputs in outputs/')
    print('=' * 70)
if __name__ == '__main__':
    main()
