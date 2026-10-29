"""Freeze independently proved disjoint relay routes against the pinned stream."""
import hashlib,json,struct,argparse
from pathlib import Path
import zstandard
ROOT=Path(__file__).resolve().parent.parent
N=(1<<64)-1
parser=argparse.ArgumentParser()
parser.add_argument('baseline_ops',type=Path)
parser.add_argument('output_dir',type=Path)
args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=True)
plans=json.loads((ROOT/'evidence/relay/selected-relays.json').read_text())
def cx(a,t):return [8,N,a,t,N,N,N]
def swap(a,t):assert a!=t;return [10,N,a,t,N,N,N]
def clear(h):
 _,d,ps,c=h
 assert d not in ps and len(ps)==len(set(ps))
 return [cx(s,d) for s in ps]+([[6,N,N,d,N,N,N]] if c else [])
actions={}
def add(i,pre,keep):
 assert i not in actions
 actions[i]=(pre,keep)
for p in plans:
 hs=p['holds'];assert hs[0][0]==p['hmr']
 add(p['hmr'],clear(hs[0])+[swap(p['wire'],hs[0][1])],True)
 add(p['hmr']+1,[],False)
 for old,new in zip(hs,hs[1:]):
  assert new[1] not in old[2] and old[1] not in new[2]
  add(new[0],clear(new)+[swap(old[1],new[1])]+list(reversed(clear(old))),True)
 last=hs[-1]
 if last[1]==p['target']:
  assert last[2]==[] and last[3] is False
  add(p['ccx'],[],False)
 else:add(p['ccx'],[swap(last[1],p['target'])]+list(reversed(clear(last))),False)
source={};depth=0;digest=hashlib.sha3_256()
with args.baseline_ops.open('rb') as f:
 header=f.read(16);assert header[:8]==b'QECCOPSZ'
 total=struct.unpack_from('<Q',header,8)[0];prefix=total-96
 assert total==10233098
 with zstandard.ZstdDecompressor().stream_reader(f) as stream:
  i=0
  while i<total:
   buf=stream.read(56*65536)
   digest.update(buf[:max(0,min(prefix-i,len(buf)//56))*56])
   for row in struct.iter_unpack('<7Q',buf):
    if i in actions:
     assert depth==0,(i,depth)
     source[i]=list(row)
    if row[0]==15:depth+=1
    elif row[0]==16:depth-=1
    i+=1
assert depth==0 and len(source)==len(actions)
for p in plans:
 assert source[p['hmr']]==[12,N,N,p['wire'],p['bit'],N,N]
 assert source[p['hmr']+1][0]==9 and source[p['hmr']+1][5]==p['bit']
 r=source[p['ccx']];assert r[0]==13 and r[3]==p['target'] and r[5]==N
lines=[f'RELAY_CACHE {prefix} {digest.hexdigest()}']
edits=[]
for i,(pre,keep) in sorted(actions.items()):
 out=pre+([source[i]] if keep else [])
 row=[i,len(out),*source[i],*(x for op in out for x in op)]
 lines.append(' '.join(map(str,row)))
 edits.append({'index':i,'expected':source[i],'replacement':out})
(args.output_dir/'relay_cache.txt').write_text('\n'.join(lines)+'\n')
(args.output_dir/'relay-edits.json').write_text(json.dumps({'prefix_ops':prefix,'sha3_256':digest.hexdigest(),'edits':edits},indent=2)+'\n')
print(json.dumps({'routes':len(plans),'edits':len(edits),'toffoli_removed':len(plans),'op_delta':sum(len(e['replacement'])-1 for e in edits),'prefix_sha3_256':digest.hexdigest()}))
