"""Locally provisioned execution adapters.

The adapter command, resource lock and allowed operation are set by the
contributor, not by the issue. Adapters implement their own isolation,
remote transport, device interlocks, cancellation and cleanup.
"""
import contextlib,fcntl,json,pathlib,re
def config(d,p):
    name=d.get('adapter')
    if not isinstance(name,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',name): return None
    a=p.get('adapters',{}).get(name,{})
    if not a.get('enabled') or a.get('kind')!=d.get('execution'): return None
    argv=a.get('argv')
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) and x for x in argv): return None
    if not pathlib.Path(argv[0]).is_absolute(): return None
    operation=d.get('operation')
    if not isinstance(operation,str) or operation not in a.get('allowed_operations',[]): return None
    if a['kind']=='bench' and not a.get('lock_file'): return None
    return a
@contextlib.contextmanager
def lock(d,p):
    a=config(d,p)
    if not a or not a.get('lock_file'):
        yield
        return
    with open(a['lock_file'],'a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
def argv(d,p,src,inputs,out,name):
    a=config(d,p)
    if a is None: raise ValueError('adapter not approved')
    # JSON is a data argument, never interpreted as a shell command.
    request={'operation':d['operation'],'parameters':d.get('parameters',{}),
        'source':str(src),'inputs':str(inputs),'output':str(out),'attempt':name,
        'timeout':d['timeout']}
    return [*a['argv'],json.dumps(request)]
