"""Campaign policy and accepted/pending result accounting."""
import hashlib,json,re
def digest(d):
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def validate(d):
    deps=d.get('depends_on',[])
    if not isinstance(deps,list) or len(deps)>64 or any(type(n) is not int or n<1 for n in deps) or len(set(deps))!=len(deps):
        raise ValueError('invalid dependencies')
    r=d.get('replication',{})
    if not isinstance(r,dict) or type(r.get('desired_runs',1)) is not int or not 1<=r.get('desired_runs',1)<=32 or type(r.get('distinct_runners',False)) is not bool:
        raise ValueError('invalid replication')
def target(d): return d.get('replication',{}).get('desired_runs',1)
def distinct(d): return d.get('replication',{}).get('distinct_runners',False)
def count(d,records):
    relevant=[r for r in records if r.get('manifest')==d]
    return len({r['runner'] if distinct(d) else r['attempt'] for r in relevant})
def eligible(d,records,runner):
    relevant=[r for r in records if r.get('manifest')==d]
    return count(d,relevant)<target(d) and not (distinct(d) and any(r['runner']==runner for r in relevant))
def accepted_records(repo,sha,n,git):
    records=[]
    for path in git(repo,'ls-tree','-r','--name-only',sha,'--',f'results/{n}/').stdout.splitlines():
        m=re.fullmatch(r'results/(\d+)/([a-f0-9]{32})/provenance.json',path)
        if not m or int(m[1])!=n: continue
        r=json.loads(git(repo,'show',sha+':'+path).stdout)
        if r.get('attempt')==m[2] and isinstance(r.get('runner'),str): records.append(r)
    return records
def default_sha(repo,git):
    sha=git(repo,'ls-remote','origin','HEAD').stdout.split()[0]
    git(repo,'fetch','--no-tags','origin',sha)
    return sha
def dependencies(d,n,repo,checkout,git,gh,parse):
    if n in d.get('depends_on',[]): return False
    if not d.get('depends_on'): return True
    sha=default_sha(checkout,git)
    for dep in d['depends_on']:
        issue=gh(repo,'issue','view',str(dep),'--json','state,body')
        if issue['state']!='CLOSED': return False
        try: spec=parse(issue['body'])
        except (ValueError,TypeError,KeyError): return False
        if count(spec,accepted_records(checkout,sha,dep,git))<target(spec): return False
    return True
