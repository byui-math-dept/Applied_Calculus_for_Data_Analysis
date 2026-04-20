"""
Post-conversion URL swap runner. Must be run after pmwiki_to_quarto.py.

Order matters:
  1. swap_internal_assets — PDFs + example_project → local ../assets/docs/
  2. swap_qmds_to_fork    — Project pages + probability → fork paths
  3. swap_csvs            — CSV domain flip (byuistats → chaz-clark)
  4. swap_remaining_byuistats — catches any stragglers the specific scripts missed

Each sub-script is idempotent. Running this repeatedly is safe.

Usage: uv run python tools/apply_url_swaps.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    '/tmp/swap_internal_assets.py',
    '/tmp/swap_qmds_to_fork.py',
    '/tmp/swap_csvs.py',
    '/tmp/swap_remaining_byuistats.py',
]


def main():
    for script in SCRIPTS:
        if not Path(script).exists():
            print(f'SKIP (not found): {script}')
            continue
        print(f'\n=== Running {Path(script).name} ===')
        result = subprocess.run(
            ['uv', 'run', 'python', script, '--apply'],
            capture_output=True, text=True,
        )
        # Print last few lines so the summary is visible
        out = result.stdout.strip().split('\n')
        if len(out) > 6:
            print('  ...')
            print('\n'.join(out[-6:]))
        else:
            print('\n'.join(out))
        if result.returncode != 0:
            print(f'ERROR ({result.returncode}):\n{result.stderr}', file=sys.stderr)
            sys.exit(1)
    print('\n✓ All URL swaps applied')


if __name__ == '__main__':
    main()
