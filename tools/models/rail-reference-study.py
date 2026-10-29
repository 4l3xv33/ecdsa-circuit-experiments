"""Diagnostic Python port of pinned a2_ref::walk_t0; no circuit or scorer changes.
Reports untruncated signed rail widths and parked endpoints, not proof of full circuit correctness.
"""
import json, subprocess
from pathlib import Path
root=Path('ecdsafail-attempt/src/point_add')
P=2**256-2**32-977
rows=[list(map(int,l.split())) for l in (root/'leapfrog_data/a2_R122_steps.txt').read_text().splitlines() if l and not l.startswith('#')]
anchors=list(map(int,(root/'leapfrog_data/a2_R122_anch.txt').read_text().strip().split(',')))
L=[(0,22),(1,13),(4,17),(9,22),(81,19),(91,17),(102,15),(107,13),(113,11)]
def bit(x,i):return (x>>i)&1
def sw(x):return (x if x>=0 else ~x).bit_length()+1
def walk(d, anchor_extra=0, window_extra=0, greedy=False, quota=None, group=3, lookahead=None, rounds_override=None):
 r0=d if d&1 else d-P
 rr=[r0,(r0+P if bit(r0,1) else r0-P)//2]
 schedule=rows[:rounds_override] if rounds_override else rows
 pfx=0; events=0; excess=[]; max_extra=0
 def check(t,site,x,w):
  nonlocal max_extra
  extra=sw(x)-w
  if extra>0:excess.append((t,site,extra,sw(x),w))
  max_extra=max(max_extra,extra)
 rail_masks=[sum(1<<(2*i+r) for i in range(group)) for r in range(2)]
 for t,row in enumerate(schedule):
  a=t%2; b=rr[1-a]; tk=rr[a]; w,n0,n1,n2,nb=row
  wn=rows[min(t+1,len(schedule)-1)][0]
  check(t,'entry-target',tk,w);check(t,'entry-source',b,w)
  ss=[]; added=flipped=False
  for i,nk in enumerate([] if t==len(schedule)-1 else [n0,n1]):
   check(t,'forced-target',tk,nk);check(t,'forced-source',b,nk)
   s=bit(tk,1)==bit(b,1)
   xx=tk+b if s else tk-b
   ad=(tk<0)==((b<0)^(not s))
   new=xx//2; fl=(not ad) and ((new<0)!=(tk<0))
   if i==1:added,flipped=ad,fl
   tk=new;ss.append(not s)
  check(t,'choice-target',tk,n2);check(t,'choice-source',b,n2)
  sd=bit(tk,1)!=bit(b,1)
  xd,xf=(tk+b,tk-b) if sd else (tk-b,tk+b)
  v=(abs(xd)&-abs(xd)).bit_length()-1 if xd else 99
  eq=xd!=0 and ((tk<0)==((b<0)^(not sd)))
  if t%(2*group)==0:pfx=0
  cap=3 if t in (0,len(schedule)-1) else 7
  mask=pfx|1<<(t%(2*group))
  if cap>3 and ((quota is not None and events>=quota) or (quota is None and any((mask&rm).bit_count()>1 for rm in rail_masks))):cap=3
  l=next(l for f,l in reversed(L) if t>=f)+window_extra;h=max(0,anchors[t]+anchor_extra-(l-2))
  wa=((tk if tk>=0 else ~tk)>>h)&((1<<l)-1)
  wb=((b if b>=0 else ~b)>>h)&((1<<l)-1)
  deep=False
  if v<=cap+1:
   if t==len(schedule)-1:deep=not(eq and v==2) or wa>(wb<<2)
   elif t==0:
    # t0_m_on's exact window-defined veto: source magnitude top 12 versus p/3 or p/5.
    mag=(b if b>=0 else ~b);const=0x555 if ss[0] else 0x333
    mh=(not ss[1]) and ((mag>>244)&0xfff)>const
    deep=not(v==2 and ((not mh)^sd))
   elif not eq:deep=True
   elif v==2:deep=wa>(wb<<1) or flipped
   elif v==3:deep=wa>(wb<<1) or not added
   else:deep=True
  if greedy and 0<t<len(schedule)-1 and v<=cap+1:
   deep=abs(xd)//(1<<v) < abs(xf)//2
  if lookahead and 0<t<len(schedule)-1 and v<=cap+1:
   # Both current choices are valid odd-rail updates. Inspect one next tick
   # to study whether a different reversible choice can accelerate convergence.
   def score(value,event):
    tt=b;bb=value; nt=t+1
    for _ in range(0 if nt==len(schedule)-1 else 2):
     tt=(tt+bb if bit(tt,1)==bit(bb,1) else tt-bb)//2
    sd2=bit(tt,1)!=bit(bb,1)
    dd,ff=(tt+bb,tt-bb) if sd2 else (tt-bb,tt+bb)
    vv=(abs(dd)&-abs(dd)).bit_length()-1 if dd else 99
    pf=(pfx|(1<<(t%(2*group)) if event else 0)) if nt%(2*group) else 0
    mm=pf|1<<(nt%(2*group)); cp=3 if nt==len(schedule)-1 else 7
    if cp>3 and ((quota is not None and events+event>=quota) or (quota is None and any((mm&rm).bit_count()>1 for rm in rail_masks))):cp=3
    vals=[ff//2]
    if vv<=cp+1:vals.append(dd//(1<<vv))
    def objective(z):
     aa,bbv=abs(value),abs(z)
     return (max(aa,bbv),aa+bbv) if lookahead=='max' else (aa*bbv,max(aa,bbv))
    return min(objective(z) for z in vals)
   deep=score(xd//(1<<v),v-1>=4)<score(xf//2,False)
  if deep and v-1>=4:pfx|=1<<(t%(2*group));events+=1
  mid=(xd if deep else xf)//2
  check(t,'pre-barrel-target',mid,nb+1)
  rr[a]=xd//2**v if deep else xf//2
  check(t,'exit-target',rr[a],wn);check(t,'exit-source',b,wn)
 return {'long_shift_events':events,'max_uniform_guard_needed':max_extra,'overflows':excess,'parked':all(abs(x)==1 for x in rr),'endpoint':[str(x) for x in rr]}
if __name__=='__main__':
 out=[]
 for packet in ['fresh','candidate']:
  path=Path('ecdsafail-evidence/continued-20261029/evidence-audit')/('paired-'+packet)/'cases.jsonl.zst'
  raw=subprocess.check_output(['zstd','-q','-dc',str(path)],text=True)
  for line in raw.splitlines():
   c=json.loads(line);bad=c['baseline']!=c['expected']
   if not bad and c['shot']>=128:continue
   x=int(c['target'][0],16);ox=int(c['offset'][0],16);nx=int(c['expected'][0],16)
   row={'packet':packet,'shot':c['shot'],'classical_bad':bad}
   row['divide']=walk((x-ox)%P);row['multiply_if_divide_correct']=walk((ox-nx)%P);out.append(row)
 Path('ecdsafail-evidence/continued-20261029/structural-search/rail-reference-study.json').write_text(json.dumps({'scope':'Untruncated reference walk and width requirements. Does not simulate payload approximations or prove circuit equivalence.','cases':out},indent=2)+'\n')
 for c in out:
  if c['classical_bad']:
   print(json.dumps({k:v for k,v in c.items() if k not in ['divide','multiply_if_divide_correct']}|{k:{a:c[k][a] for a in ['max_uniform_guard_needed','parked','endpoint']} for k in ['divide','multiply_if_divide_correct']}))
