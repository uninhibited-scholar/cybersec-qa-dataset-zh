"""Start full clean-corpus ChatML run detached; never changes serving config."""
import subprocess
from pathlib import Path
root=Path('/Users/jiehan/cyber-agent')
out=Path('/Users/jiehan/models/phase10-clean-chatml-20260913')
if out.exists(): raise SystemExit('output exists; refusing overwrite')
with (root/'phase10-clean-chatml-20260913.log').open('x') as log:
    p=subprocess.Popen(['/Users/jiehan/venvs/agents-a1/bin/python','-u','-m','mlx_lm','lora','--config',str(root/'phase10_clean_chatml.yaml')],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(p.pid)
