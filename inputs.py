"""Pinned, explicitly approved Git inputs. No checkout filters or submodules."""
import pathlib, re, subprocess, tempfile
SHA=re.compile(r'[0-9a-f]{40}')
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')
def safe_path(s):
    if not isinstance(s,str) or not s or '\\' in s or any(ord(c)<32 for c in s):
        raise ValueError('invalid input path')
    s=s.rstrip('/')
    if any(x in ('','.','..') or x.lower()=='.git' for x in s.split('/')):
        raise ValueError('unsafe input path')
    return s
def validate(inputs):
    if not isinstance(inputs,list) or len(inputs)>16: raise ValueError('invalid inputs')
    names=set()
    for i in inputs:
        if not isinstance(i,dict) or not NAME.fullmatch(i.get('name','')) or i['name'] in names: raise ValueError('invalid or duplicate input name')
        names.add(i['name'])
        if not isinstance(i.get('repository'),str) or not SHA.fullmatch(i.get('revision','')): raise ValueError('invalid pinned input')
        paths=i.get('paths')
        if not isinstance(paths,list) or not paths or len(paths)>128: raise ValueError('explicit paths required')
        for p in paths: safe_path(p)
def approved(inputs,policy):
    return all(i['repository'] in policy.get('allowed_inputs',[]) for i in inputs)
def g(repo,*args):
    return subprocess.run(['git','-c','protocol.ext.allow=never','-c','protocol.file.allow=never',*args],cwd=repo,check=True,capture_output=True).stdout
def materialize(inputs,policy,queue_url,root):
    validate(inputs)
    if not approved(inputs,policy): raise ValueError('unapproved input repository')
    root=pathlib.Path(root); root.mkdir()
    budget=policy.get('max_input_bytes',100_000_000)
    remaining=budget
    for i in inputs:
        url=queue_url if i['repository']=='self' else i['repository']
        if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',url): raise ValueError('only explicit GitHub HTTPS inputs supported')
        with tempfile.TemporaryDirectory() as t:
            g(t,'init','--bare')
            g(t,'fetch','--no-tags','--depth=1',url,i['revision'])
            if g(t,'rev-parse','FETCH_HEAD').decode().strip()!=i['revision']: raise ValueError('revision mismatch')
            remaining=export_tree(t,i['revision'],i['paths'],root/i['name'],remaining)
def export_tree(repo,revision,paths,dest,remaining):
    paths=[safe_path(p) for p in paths]
    entries=g(repo,'ls-tree','-r','-z',revision).split(b'\0')
    selected=[]
    for entry in entries:
        if not entry: continue
        meta,raw=entry.split(b'\t',1); mode,kind,sha=meta.decode().split()
        name=raw.decode('utf-8')
        if not any(name==p or name.startswith(p+'/') for p in paths): continue
        safe_path(name)
        if kind!='blob' or mode not in ('100644','100755'): raise ValueError('symlink or submodule input rejected')
        selected.append((name,sha))
    if any(not any(n==p or n.startswith(p+'/') for n,_ in selected) for p in paths): raise ValueError('input path missing')
    dest.mkdir()
    for name,sha in selected:
        size=int(g(repo,'cat-file','-s',sha))
        if size>remaining: raise ValueError('input byte budget exceeded')
        remaining-=size
        f=dest/name; f.parent.mkdir(parents=True,exist_ok=True)
        f.write_bytes(g(repo,'cat-file','blob',sha)); f.chmod(0o444)
    return remaining
