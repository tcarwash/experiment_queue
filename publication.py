"""Recover result branches pushed before PR creation; reconcile replicated results."""
import json,re
from campaigns import accepted_records,default_sha,count,target
def branch_records(x,n,d,git,gh,run,lease):
    accepted=accepted_records(x.checkout,default_sha(x.checkout,git),n,git)
    seen={r['attempt'] for r in accepted}
    pending=[]
    prefix=f'refs/heads/results/experiment-{n}/'
    refs=git(x.checkout,'ls-remote','--refs','origin',prefix+'*').stdout.splitlines()
    for line in refs:
        sha,ref=line.split()
        attempt=ref.removeprefix(prefix)
        if not re.fullmatch('[a-f0-9]{32}',attempt) or attempt in seen: continue
        git(x.checkout,'fetch','--no-tags','origin',sha)
        try:
            r=json.loads(git(x.checkout,'show',sha+f':results/{n}/{attempt}/provenance.json').stdout)
        except (ValueError,RuntimeError): continue
        if r.get('attempt')!=attempt or r.get('manifest')!=d or not isinstance(r.get('runner'),str): continue
        branch=ref.removeprefix('refs/heads/')
        prs=gh(x.repo,'pr','list','--head',branch,'--state','all','--json','state,url','--limit','20')
        if not prs:
            if not lease.renew(): raise RuntimeError('lease lost before publication recovery')
            create_pr(x,n,d,attempt,branch,run)
            pending.append(r)
        elif any(p['state'] in ('OPEN','MERGED') for p in prs): pending.append(r)
    return accepted,pending
def create_pr(x,n,d,attempt,branch,run):
    body=(f'Closes #{n}' if target(d)==1 else f'Replication result for #{n}')+'\n\nReview experiment evidence before merging.'
    return run('gh','pr','create','--repo',x.repo,'--head',branch,'--title',f'Result #{n}: {attempt}','--body',body).stdout.strip()
def reconcile(x,n,d,accepted,pending,run,lease):
    if count(d,accepted)>=target(d):
        if not lease.renew(): raise RuntimeError('lease lost before close')
        run('gh','issue','close',str(n),'--repo',x.repo,'--reason','completed')
        run('gh','issue','edit',str(n),'--repo',x.repo,'--remove-label','experiment-ready')
        return True
    if count(d,accepted+pending)>=target(d):
        if not lease.renew(): raise RuntimeError('lease lost before label change')
        # Replicated issues stay discoverable until all reports are merged.
        if target(d)==1: run('gh','issue','edit',str(n),'--repo',x.repo,'--remove-label','experiment-ready')
        return True
    return False
