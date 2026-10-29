import hashlib,json,time
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('integrated','ecdsafail-tooling/rail-integrated-model.py').load_module()
for N,domain,policies in [(8192,b'ecdsafail-structural-convergence-study-v1',['greedy-v2','greedy-v3','interval-v2:10']),(65536,b'ecdsafail-initialization-holdout-v1',['greedy-v2','interval-v2:10'])]:
 data=hashlib.shake_256(domain).digest(N*32)
 ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
 for policy in policies:
  start=time.monotonic();bad=[];hist={}
  for i,d in enumerate(ins):
   w=m.walk(d,sum_limit=10,decision=policy);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1
   if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':g})
  print(json.dumps({'policy':policy,'domain':domain.decode(),'inputs':N,'unfinished':len(bad),'width_excess':hist,'seconds':time.monotonic()-start,'failures':bad}),flush=True)
