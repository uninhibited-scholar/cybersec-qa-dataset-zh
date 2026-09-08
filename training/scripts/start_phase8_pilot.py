"""Launch once, detached from SSH; never switch the serving adapter."""
import subprocess
from pathlib import Path

root = Path('/Users/jiehan/cyber-agent')
output = Path('/Users/jiehan/models/phase8-neutral-pilot-20260908')
if output.exists():
    raise SystemExit('Output already exists; inspect before starting another run')
log = root / 'phase8-neutral-pilot-20260908.log'
with log.open('x') as handle:
    process = subprocess.Popen(
        ['/Users/jiehan/venvs/agents-a1/bin/python', '-u', '-m', 'mlx_lm',
         'lora', '--config', str(root / 'phase8_neutral_pilot.yaml')],
        cwd=root, stdin=subprocess.DEVNULL, stdout=handle,
        stderr=subprocess.STDOUT, start_new_session=True,
    )
print(f'Training PID: {process.pid}; log: {log}')
