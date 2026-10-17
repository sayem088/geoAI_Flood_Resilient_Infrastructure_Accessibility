import subprocess, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
HERE = Path(__file__).parent
SCRIPTS = [HERE / 's02_extract_training_samples.py', HERE / 's02_compute_moran_spatial_blocks.py']

def run(script):
    print(f"\n{'=' * 60}\n  RUNNING -> {script.name}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(script)])
    if r.returncode != 0:
        sys.exit(f'\n[FAILED] {script.name}')
print('\n' + '=' * 60)
print('  MASTER STEP 02: SPATIAL SAMPLING')
print('=' * 60)
for s in SCRIPTS:
    run(s)
print('\n' + '=' * 60)
print('  [SUCCESS] STEP 02 COMPLETE -- Training samples extracted.')
print('=' * 60)
