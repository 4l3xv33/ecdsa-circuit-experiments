"""Arithmetic initialization study; same 8192 common denominators, no circuit hash changes."""
import hashlib,json,time
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails_init','ecdsafail-tooling/rail-initialization-model.py').load_module()
N=8192;data=hashlib.shake_256(b'ecdsafail-structural-convergence-study-v1').digest(N*32)
ins=[int.from_bytes(data[i*32:(i+1)*32],'little')%(m.P-1)+1 for i in range(N)]
for cap,greedy in [(4,False),(8,False),(8,True)]:
 start=time.monotonic();bad=[];hist={};ev={}
 for i,d in enumerate(ins):
  w=m.walk(d,greedy=greedy,initial_policy=cap);g=w['max_uniform_guard_needed'];hist[g]=hist.get(g,0)+1;e=w['long_shift_events'];ev[e]=ev.get(e,0)+1
  if not w['parked']:bad.append({'i':i,'d':hex(d),'endpoint':w['endpoint'],'width_excess':g})
 print(json.dumps({'initial_high_shift_cap':cap,'greedy':greedy,'walks':N,'not_parked':len(bad),'guard_histogram':hist,'event_histogram':ev,'failures':bad,'seconds':time.monotonic()-start}),flush=True)
