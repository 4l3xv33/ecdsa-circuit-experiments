#!/usr/bin/env python3
"""Create an isolated pinned checkout. Does not compile, score, or submit."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PIN='2120d8a20c9d277e3cfdae29639ec58a78e72e16'
p=argparse.ArgumentParser()
p.add_argument('variant',choices=['baseline','relay','guard-repair','sum-record-compact'])
p.add_argument('--source',type=Path,help='optional existing local upstream Git checkout')
a=p.parse_args()
work=ROOT/'work'/a.variant
repo=work/'ecdsafail-attempt'
if work.exists():raise SystemExit(f'Refusing existing directory: {work}')
repo.mkdir(parents=True)
def run(cmd,**kw):subprocess.run(cmd,check=True,**kw)
if a.source:
    archive=subprocess.Popen(['git','-C',str(a.source.resolve()),'archive',PIN],stdout=subprocess.PIPE)
    run(['tar','-x','-C',str(repo)],stdin=archive.stdout)
    if archive.wait():raise SystemExit('git archive failed')
else:
    run(['git','init','-q',str(repo)])
    run(['git','-C',str(repo),'remote','add','origin','https://github.com/Layr-Labs/ecdsafail-challenge.git'])
    run(['git','-C',str(repo),'fetch','--depth=1','origin',PIN])
    run(['git','-C',str(repo),'checkout','--detach','FETCH_HEAD'])
if a.variant!='baseline':
    files=json.loads((ROOT/'patches/manifest.json').read_text())[a.variant]
    for rel,m in files.items():
        dst=repo/rel
        if m['baseline_exists']:dst.write_bytes(dst.read_bytes().replace(b'\r\n',b'\n'))
    run(['git','-C',str(repo),'apply','--unidiff-zero',str(ROOT/'patches'/(a.variant+'.patch'))])
    for rel,m in files.items():
        dst=repo/rel;lines=dst.read_bytes().splitlines(True)
        for i in m['crlf_lines']:lines[i]=lines[i].removesuffix(b'\n')+b'\r\n'
        dst.write_bytes(b''.join(lines))
        assert hashlib.sha256(dst.read_bytes()).hexdigest()==m['sha256'],rel
manifest=json.loads((ROOT/'evidence/protected-files.json').read_text())['sha256']
for rel,expected in manifest.items():
    assert hashlib.sha256((repo/rel).read_bytes()).hexdigest()==expected,rel
tool=work/'ecdsafail-tooling';tool.mkdir()
for f in (ROOT/'tools').glob('*'):
    if f.is_file():shutil.copyfile(f,tool/f.name)
for f in (ROOT/'tools/models').glob('*.py'):shutil.copyfile(f,tool/f.name)
for name,m in json.loads((ROOT/'tools/derived/manifest.json').read_text()).items():
    dst=tool/m['output'];dst.write_bytes((repo/m['upstream']).read_bytes().replace(b'\r\n',b'\n'))
    run(['patch','--quiet',str(dst),str(ROOT/'tools/derived'/(name+'.patch'))])
    lines=dst.read_bytes().splitlines(True)
    for i in m['crlf_lines']:lines[i]=lines[i].removesuffix(b'\n')+b'\r\n'
    dst.write_bytes(b''.join(lines))
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==m['sha256'],name
print(f'Prepared {a.variant}; all protected file hashes match {PIN}.')
print(f'Working directory: {work}')
