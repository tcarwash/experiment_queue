"""Local policy controls container invocation; manifests cannot add flags."""
import os,re,subprocess
def permitted(d,p):
    if d.get('execution')=='scripted': return p.get('allow_native',False)
    if d.get('execution')!='container': return False
    image=d.get('image','')
    return (p.get('allow_container',False) and isinstance(image,str)
        and bool(re.fullmatch(r'[A-Za-z0-9._/:+-]+@sha256:[a-f0-9]{64}|sha256:[a-f0-9]{64}',image))
        and image in p.get('allowed_images',[]))
def command(d,p,src,inputs,out,name):
    if d['execution']=='scripted': return d['command']
    if not permitted(d,p): raise ValueError('container not approved')
    runtime=p.get('container_runtime','podman')
    if runtime not in ('docker','podman'): raise ValueError('invalid runtime')
    return [runtime,'run','--rm','--name',name,'--pull=never','--network=none',
        '--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
        '--user',f'{os.getuid()}:{os.getgid()}','--pids-limit=128',
        '--cpus',str(p.get('container_cpus',2)),'--memory',str(p.get('container_memory','2g')),
        '--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=256m',
        '--mount',f'type=bind,source={src},target=/source,readonly',
        '--mount',f'type=bind,source={inputs},target=/inputs,readonly',
        '--mount',f'type=bind,source={out},target=/output',
        '--workdir','/source','--env','EXPERIMENT_INPUTS=/inputs','--env','EXPERIMENT_OUTPUT=/output',
        '--env','HOME=/tmp','--entrypoint',d['command'][0],d['image'],*d['command'][1:]]
def cleanup(d,p,name):
    if d['execution']=='container':
        subprocess.run([p.get('container_runtime','podman'),'rm','-f',name],capture_output=True,timeout=15,check=False)
