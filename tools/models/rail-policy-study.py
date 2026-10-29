"""Unbiased, fixed common-input convergence study. No score or circuit nonce involved."""
import hashlib,json
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails','ecdsafail-tooling/rail-reference-study.py').load_module()
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')% (m.P-1)+1 for i in range(N)]
for name,a,b,g in [('pinned',0,0,False),('higher-window',8,8,False),('exact-greedy',8,8,True)]:
 bad=[];counts={}
 for i,d in enumerate(ins):
  w=m.walk(d,a,b,g);e=w['max_uniform_guard_needed'];counts[e]=counts.get(e,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':e})
 print(json.dumps({'policy':name,'walks':N,'not_parked':len(bad),'guard_histogram':counts,'failure_details':bad}),flush=True)
