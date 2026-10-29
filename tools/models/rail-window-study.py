"""Cost-independent arithmetic diagnosis: extend window upward, preserve lower boundary."""
import json,subprocess
from pathlib import Path
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('rails','ecdsafail-tooling/rail-reference-study.py').load_module()
inputs=[]
for packet in ['fresh','candidate']:
 path=Path('ecdsafail-evidence/continued-20261029/evidence-audit')/('paired-'+packet)/'cases.jsonl.zst'
 for line in subprocess.check_output(['zstd','-q','-dc',str(path)],text=True).splitlines():
  c=json.loads(line)
  if c['baseline']==c['expected'] and c['shot']>=128:continue
  x,ox,nx=[int(q,16) for q in (c['target'][0],c['offset'][0],c['expected'][0])]
  for phase,d in [('divide',(x-ox)%m.P),('multiply',(ox-nx)%m.P)]:inputs.append((packet,c['shot'],phase,d))
for up in (0,2,4,8,16):
 out=[]
 for packet,shot,phase,d in inputs:
  w=m.walk(d,up,up)
  out.append({'packet':packet,'shot':shot,'phase':phase,'width_extra':w['max_uniform_guard_needed'],'parked':w['parked'],'endpoint':w['endpoint']})
 Path(f'ecdsafail-evidence/continued-20261029/structural-search/rail-window-up{up}.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'top_extension':up,'walks':len(out),'not_parked':sum(not x['parked'] for x in out),'width_excess':sum(x['width_extra']>0 for x in out),'max_width_excess':max(x['width_extra'] for x in out)}))
