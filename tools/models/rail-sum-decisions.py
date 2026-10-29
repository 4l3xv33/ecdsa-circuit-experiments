"""Exact-storage alternative: three exponents in 0..7 with sum<=10 have 256 states."""
import hashlib,json,time,itertools
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails_sum','ecdsafail-tooling/rail-sum-decision-model.py').load_module()
allowed=[v for v in itertools.product(range(8),repeat=3) if sum(v)<=10]
assert len(allowed)==256
# Complement pairs partition all 512 strings, one admissible representative each.
assert all((sum(v)<=10)!=(sum(7-x for x in v)<=10) for v in itertools.product(range(8),repeat=3))
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
for decision in ['sym-full','sym-window','flags8','deep8','flags12']:
 greedy,init=False,None
 start=time.monotonic();bad=[];hist={}
 for i,d in enumerate(ins):
  w=m.walk(d,greedy=greedy,initial_policy=init,sum_limit=10,decision=decision);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':g})
 print(json.dumps({'sum_limit':10,'decision':decision,'greedy':greedy,'initial_cap':init,'walks':N,'not_parked':len(bad),'guard_histogram':hist,'triple_storage_states':len(allowed),'failures':bad,'seconds':time.monotonic()-start}),flush=True)
