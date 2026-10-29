"""Fixed-input study of smaller unrestricted shift alphabets and exact radix storage."""
import hashlib,json,time,math
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails_radix','ecdsafail-tooling/rail-radix-model.py').load_module()
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
for cap,greedy,init in [(4,False,None),(4,True,None),(5,False,None),(5,True,None),(4,True,8),(5,True,8)]:
 start=time.monotonic();bad=[];hist={}
 for i,d in enumerate(ins):
  w=m.walk(d,greedy=greedy,initial_policy=init,max_extra_shift=cap,quota=1000000);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':g})
 print(json.dumps({'max_extra_shift':cap,'greedy':greedy,'initial_cap':init,'walks':N,'not_parked':len(bad),'guard_histogram':hist,'triple_shift_storage_bits':math.ceil(math.log2((cap+1)**3)),'failures':bad,'seconds':time.monotonic()-start}),flush=True)
