"""Fixed common-input study of algebraically motivated low-cost GCD decisions."""
import hashlib,json,time
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails_choice','ecdsafail-tooling/rail-decision-model.py').load_module()
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
for policy in ['sym-two','source-two','swap-y','greedy-window8','sym-window8']:
 start=time.monotonic();bad=[];hist={}
 for i,d in enumerate(ins):
  w=m.walk(d,choice_policy=policy);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':g})
 print(json.dumps({'policy':policy,'walks':N,'not_parked':len(bad),'guard_histogram':hist,'failures':bad,'seconds':time.monotonic()-start}),flush=True)
