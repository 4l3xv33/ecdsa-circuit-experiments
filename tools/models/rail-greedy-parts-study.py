import hashlib,json,time
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('prefix','ecdsafail-tooling/rail-greedy-parts-model.py').load_module()
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
for policy in ['always-deep','flags-only','greedy-v2','greedy-v3','greedy-v4']:
 start=time.monotonic();bad=[];hist={}
 for i,d in enumerate(ins):
  w=m.walk(d,sum_limit=10,decision=policy);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint']})
 print(json.dumps({'policy':policy,'inputs':N,'unfinished':len(bad),'width_excess':hist,'seconds':time.monotonic()-start,'failures':bad}),flush=True)
