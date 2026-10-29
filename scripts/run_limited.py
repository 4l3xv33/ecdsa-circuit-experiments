#!/usr/bin/env python3
"""Run one explicit command with two CPUs, nice 10, 8 GiB AS and a wall cap."""
import argparse,os,resource,subprocess
p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=300)
p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
command=a.command[1:] if a.command[:1]==['--'] else a.command
if not command:raise SystemExit('An explicit command is required.')
def limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    os.nice(10)
# GNU timeout handles the process group, including compiler children.
raise SystemExit(subprocess.run(['timeout','--signal=TERM','--kill-after=5s',str(a.seconds)+'s',*command],preexec_fn=limits).returncode)
