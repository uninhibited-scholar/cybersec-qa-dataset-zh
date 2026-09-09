"""Start a fresh adapter, leaving online inference and old weights unchanged."""
import subprocess
from pathlib import Path
root = Path('/Users/jiehan/cyber-agent')
assert not Path('/Users/jiehan/models/phase9-fresh-chatml-20260909').exists()
with (root/'phase9-fresh-chatml-20260909.log').open('x') as log:
    process = subprocess.Popen(['/Users/jiehan/venvs/agents-a1/bin/python','-u','-m','mlx_lm','lora',
        '--config',str(root/'phase9_fresh_chatml.yaml')],cwd=root,stdin=subprocess.DEVNULL,
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(process.pid)
