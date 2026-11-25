"""Contributor-controlled GitHub experiment runner (standard library only)."""
import argparse, datetime, json, os, pathlib, re, subprocess, tempfile, time, uuid
from inputs import validate, approved, materialize
from executors import permitted, command, cleanup
from inference import report as ai_report, advise
UTC=datetime.timezone.utc
def now(): return datetime.datetime.now(UTC)
def run(*args, cwd=None, check=True, **kw):
    return subprocess.run(args,cwd=cwd,check=check,text=True,capture_output=True,**kw)
def git(repo,*args,**kw): return run('git',*args,cwd=repo,**kw)
def gh(repo,*args): return json.loads(run('gh',*args,'--repo',repo).stdout)
def manifest(body):
    m=re.search(r'```json\s*\n(.*?)\n```',body,re.S)
    if not m: raise ValueError('missing JSON manifest')
    d=json.loads(m[1])
    if d.get('schema')!='experiment/v1': raise ValueError('unsupported schema')
    if not isinstance(d.get('command'),list) or not d['command'] or not all(isinstance(x,str) and x for x in d['command']): raise ValueError('invalid command')
    if not re.fullmatch('[0-9a-f]{40}',d.get('revision','')): raise ValueError('pin full git revision')
    if not isinstance(d.get('capabilities',[]),list): raise ValueError('invalid capabilities')
    validate(d.get("inputs",[]))
    return d
def matches(d,p):
    return (set(d.get('capabilities',[])) <= set(p.get('capabilities',[]))
        and d.get('source') in p.get('allowed_sources',[])
        and approved(d.get('inputs',[]),p)
        and permitted(d,p)
        and 0 < d.get('timeout',0) <= p.get('max_seconds',0))
class Lease:
    def __init__(self,repo,issue,runner,ttl=120):
        self.repo=repo; self.ref=f'refs/heads/leases/experiment-{int(issue)}'
        self.runner=runner; self.attempt=uuid.uuid4().hex; self.ttl=ttl; self.head=None
    def read(self):
        out=git(self.repo,'ls-remote','--refs','origin',self.ref).stdout.strip()
        if not out: return None,None
        sha=out.split()[0]
        git(self.repo,'fetch','--no-tags','origin',sha)
        return sha,json.loads(git(self.repo,'show',sha+':lease.json').stdout)
    def update(self,old,state):
        blob=git(self.repo,'hash-object','-w','--stdin',input=json.dumps(state)).stdout.strip()
        tree=git(self.repo,'mktree',input=f'100644 blob {blob}\tlease.json\n').stdout.strip()
        args=['commit-tree',tree,'-m','lease '+self.attempt]
        if old: args.extend(['-p',old])
        sha=git(self.repo,*args).stdout.strip()
        p=git(self.repo,'push',f'--force-with-lease={self.ref}:{old or ""}','origin',f'{sha}:{self.ref}',check=False)
        if p.returncode: return False
        self.head=sha; return True
    def claim(self):
        old,s=self.read()
        if s and s['status']=='active' and datetime.datetime.fromisoformat(s['expires'])>now(): return False
        return self.update(old,self.state('active'))
    def state(self,status):
        return dict(runner=self.runner,attempt=self.attempt,status=status,expires=(now()+datetime.timedelta(seconds=self.ttl)).isoformat())
    def renew(self): return bool(self.head) and self.update(self.head,self.state('active'))
    def release(self): return bool(self.head) and self.update(self.head,self.state('released'))
def queue(repo):
    return gh(repo,'issue','list','--state','open','--label','experiment-ready','--limit','100','--json','number,title,body')
def comment(repo,n,message):
    run('gh','issue','comment',str(n),'--repo',repo,'--body',message)
def main():
    a=argparse.ArgumentParser()
    a.add_argument('--repo',required=True); a.add_argument('--checkout',required=True); a.add_argument('--policy',required=True)
    a.add_argument('action',choices=['list','run','review','once']); a.add_argument('--issue',type=int)
    x=a.parse_args(); p=json.loads(pathlib.Path(x.policy).read_text())
    for i in queue(x.repo):
        try: d=manifest(i['body']); eligible=matches(d,p)
        except (ValueError,TypeError,KeyError): continue
        print(f"{i['number']}: {i['title']} eligible={eligible}",flush=True)
        if x.action=='review' and i['number']==x.issue:
            draft=advise(p,'management',{'title':i['title'],'manifest':d,'eligible':eligible})
            print(draft['draft'] if draft else 'Management assistance disabled')
            return
        if not eligible or not (x.action=='once' or (x.action=='run' and i['number']==x.issue)): continue
        if execute(x,p,i,d): return
    if x.action in ('run','review'): raise SystemExit('no matching issue')
def execute(x,p,i,d):
    n=i['number']; lease=Lease(x.checkout,n,p['runner'])
    if not lease.claim():
        print('already claimed',flush=True); return False
    try:
        fresh=gh(x.repo,'issue','view',str(n),'--json','state,body,labels')
        if fresh['state']!='OPEN' or not any(l['name']=='experiment-ready' for l in fresh['labels']) or fresh['body']!=i['body']:
            print('issue changed after discovery',flush=True); return False
        comment(x.repo,n,f'Claimed by {p["runner"]}, attempt {lease.attempt}')
        with tempfile.TemporaryDirectory(prefix='experiment-',dir=p.get('staging_dir')) as tmp:
            src=pathlib.Path(tmp)/'source'; out=pathlib.Path(tmp)/'output'; out.mkdir()
            git(tmp,'clone','--no-checkout','--',d['source'],str(src))
            git(src,'checkout','--detach',d['revision'])
            input_root=pathlib.Path(tmp)/'inputs'
            materialize(d.get('inputs',[]),p,git(x.checkout,'remote','get-url','origin').stdout.strip(),input_root)
            if not lease.renew(): raise RuntimeError('lease lost during staging')
            env={'EXPERIMENT_INPUTS':str(input_root),'PATH':os.defpath,'HOME':tmp,'EXPERIMENT_OUTPUT':str(out),'LANG':'C.UTF-8'}
            started=now()
            import signal
            with open(out/'stdout.log','w') as stdout, open(out/'stderr.log','w') as stderr:
                name='experiment-'+lease.attempt
                argv=command(d,p,src,input_root,out,name)
                proc=subprocess.Popen(argv,cwd=src,env=env if d['execution']=='scripted' else None,stdout=stdout,stderr=stderr,start_new_session=True)
                deadline=time.monotonic()+d['timeout']
                renewal=time.monotonic()+30
                try:
                    while proc.poll() is None:
                        if time.monotonic()>deadline: raise TimeoutError('runtime limit')
                        if time.monotonic()>renewal:
                            if not lease.renew(): raise RuntimeError('lease lost')
                            renewal=time.monotonic()+30
                        time.sleep(.25)
                finally:
                    if proc.poll() is None:
                        os.killpg(proc.pid,signal.SIGKILL); proc.wait()
                    cleanup(d,p,name)
            if proc.returncode: raise RuntimeError(f'command exit {proc.returncode}')
            report=out/'report.md'
            if not report.is_file() or report.is_symlink() or not report.read_text().strip(): raise ValueError('missing report.md')
            if not lease.renew(): raise RuntimeError('lease lost before publication')
            try:
                draft=ai_report(p,out)
                if draft:
                    # Exclusive creation: never follow a workload-provided symlink.
                    with (out/'ai-draft.md').open('x') as f: f.write('AI draft; requires review. Backend: '+draft['backend']+'\n\n'+draft['draft'])
            except Exception as e:
                print('Optional AI report unavailable: '+type(e).__name__,flush=True)
            publish(x,lease,n,d,out,started)
    except Exception as e:
        comment(x.repo,n,f'Non-finding execution failure ({lease.attempt}): {type(e).__name__}: {e}')
        if lease.renew():
            run('gh','issue','edit',str(n),'--repo',x.repo,'--remove-label','experiment-ready')
        raise
    finally: lease.release()
    return True
def publish(x,lease,n,d,out,started):
    import hashlib, shutil
    with tempfile.TemporaryDirectory(prefix='result-') as tmp:
        git(tmp,'clone','--',git(x.checkout,'remote','get-url','origin').stdout.strip(),tmp)
        dest=pathlib.Path(tmp)/'results'/str(n)/lease.attempt; dest.mkdir(parents=True)
        hashes={}
        for f in out.iterdir():
            if f.is_symlink() or not f.is_file() or f.stat().st_size>10_000_000: raise ValueError('unsupported artifact')
            shutil.copyfile(f,dest/f.name); hashes[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
        (dest/'provenance.json').write_text(json.dumps(dict(runner=lease.runner,attempt=lease.attempt,started=started.isoformat(),finished=now().isoformat(),manifest=d,sha256=hashes),indent=2))
        git(tmp,'add','results'); git(tmp,'commit','-m',f'Result #{n} {lease.attempt}')
        if not lease.renew(): raise RuntimeError('lease lost')
        branch='results/experiment-'+str(n)+'/'+lease.attempt
        git(tmp,'push','origin',f'HEAD:refs/heads/{branch}')
        url=run('gh','pr','create','--repo',x.repo,'--head',branch,'--title',f'Result #{n}: {lease.attempt}','--body',f'Closes #{n}\n\nReview experiment evidence before merging.').stdout.strip()
        comment(x.repo,n,f'Result submitted: {url}')
        if lease.renew():
            run('gh','issue','edit',str(n),'--repo',x.repo,'--remove-label','experiment-ready')
if __name__=='__main__': main()
