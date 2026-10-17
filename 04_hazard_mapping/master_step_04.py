import subprocess, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
HERE = Path(__file__).parent
SCRIPTS = [HERE / 's04_predict_flood_surface.py', HERE / 's04_generate_fig3_hazard_map.py']

def run(script):
    print(f"\n{'=' * 60}\n  RUNNING -> {script.name}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(script)])
    if r.returncode != 0:
        sys.exit(f'\n[FAILED] {script.name}')
print('\n' + '=' * 60)
print('  MASTER STEP 04: FLOOD HAZARD MAPPING')
print('=' * 60)
for s in SCRIPTS:
    run(s)
print('\n' + '=' * 60)
print('  [SUCCESS] STEP 04 COMPLETE -- P_flood raster, Fig3, Table2 ready.')
print('=' * 60)
