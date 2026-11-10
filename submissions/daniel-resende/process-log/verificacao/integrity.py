"""Read-only Git checks, scan key shapes without printing matching values."""
import re
import subprocess
from pathlib import Path
def git(*args):
    p=subprocess.run(['git',*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return p.returncode,p.stdout.strip()
print('HEAD',git('rev-parse','HEAD'))
print('original_worktree_diff',git('diff','--exit-code','--','submissions/daniel-resende'))
print('upstream_main',git('show-ref','--verify','refs/remotes/upstream/main'))
print('origin_main',git('show-ref','--verify','refs/remotes/origin/main'))
code,names=git('diff','--name-only','origin/main','HEAD')
print('origin_main_changed_paths',len(names.splitlines()),'outside_submission',[p for p in names.splitlines() if not p.startswith('submissions/daniel-resende/')], 'exit',code)
_,names=git('ls-files');files=names.splitlines()
patterns={'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----','openai_or_anthropic':rb'\bsk-(?:ant-)?[A-Za-z0-9_-]{25,}','aws_access_id':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b','github':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})','slack':rb'\bxox[baprs]-[A-Za-z0-9-]{20,}'}
hits=[];artifacts=[];scanned=0
for name in files:
    if re.search(r'(^|/)(?:\.venv|venv|__pycache__|node_modules|\.cache|out|dist|build)(/|$)|\.pyc$',name):artifacts.append(name)
    if Path(name).name.startswith('.env') or any(p in Path(name).parts for p in ['.aws','.codex','.agents']):
        hits.append((name,'sensitive_filename_not_read'));continue
    if Path(name).suffix in ['.png','.webp','.woff2']:continue
    content=Path(name).read_bytes();scanned+=1
    for kind,pat in patterns.items():
        if re.search(pat,content):hits.append((name,kind))
print('tracked_paths',len(files),'text_files_scanned',scanned,'key_shape_hits',hits,'generated_or_environment_paths',artifacts)
for n,doc in [(4,'numeros-saida.txt'),(6,'validacao-saida.txt'),(7,'confirmacao-saida.txt')]:
    actual=Path(f'.verif/command-{n}.txt').read_text().split('\n',2)[2]
    stored=Path('submissions/daniel-resende/docs',doc).read_text()
    print('saved_output_matches',doc,actual==stored)
print('requirements_bytes',Path('submissions/daniel-resende/solution/requirements.txt').stat().st_size)
