import subprocess, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
HERE = Path(__file__).parent
SCRIPTS = [HERE / 's05_compute_deii_surface.py', HERE / 's05_compute_catchment_collapse.py', HERE / 's05_generate_fig4_curves.py', HERE / 's05_generate_fig5_landfill.py', HERE / 's05_compute_vulnerable_population.py']

def run(script):
    print(f"\n{'=' * 60}\n  RUNNING -> {script.name}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(script)])
    if r.returncode != 0:
        sys.exit(f'\n[FAILED] {script.name}')
print('\n' + '=' * 60)
print('  MASTER STEP 05: DEII ROUTING & ACCESSIBILITY')
print('=' * 60)
for s in SCRIPTS:
    run(s)
print('\n' + '=' * 60)
print('  [SUCCESS] STEP 05 COMPLETE -- DEII raster, Tables 3-5, Fig 4-5 ready.')
print('=' * 60)
