#!/usr/bin/env python3
"""Link auxiliary diagnostics against an already built, pinned Rust crate."""
import argparse,subprocess,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('work',type=Path);a=p.parse_args()
work=a.work.resolve();repo=work/'ecdsafail-attempt';tool=work/'ecdsafail-tooling'
deps=repo/'target/release/deps'
extra=[]
for name in ['quantum_ecc','alloy_primitives','sha3','zstd']:
    matches=list(deps.glob('lib'+name+'-*.rlib'))
    if len(matches)!=1:raise SystemExit(f'Need exactly one release rlib for {name}; use a fresh target directory.')
    extra+=['--extern',name+'='+str(matches[0])]
for name in ['paired-audit','fixture-eval','sum-generic','relay-identity-tests','relay-planner-main']:
    args=['rustc','+1.93.0','--edition=2021','-C','opt-level=2','-C','linker=/usr/bin/gcc','-L','dependency='+str(deps),*extra]
    if name.endswith('tests'):args+=['--test']
    subprocess.run([*args,str(tool/(name+'.rs')),'-o',str(tool/name)],check=True,cwd=repo)
print('Built diagnostics. They do not replace the official evaluator.')
