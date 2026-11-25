"""Local persistent scheduler and read-only loopback dashboard."""
import argparse, contextlib, fcntl, json, pathlib, random, sqlite3, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
ROOT=pathlib.Path(__file__).resolve().parent
class State:
    def __init__(self,path):
        self.path=pathlib.Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, repo TEXT, started REAL, finished REAL, status TEXT, log TEXT)")
    def connect(self): return sqlite3.connect(self.path,timeout=10)
    def start(self,repo):
        with self.connect() as c: return c.execute("INSERT INTO runs(repo,started,status) VALUES(?,?,'running')",(repo,time.time())).lastrowid
    def finish(self,id,status,log):
        with self.connect() as c: c.execute("UPDATE runs SET finished=?,status=?,log=? WHERE id=?",(time.time(),status,log[-16000:],id))
    def recover(self):
        with self.connect() as c: c.execute("UPDATE runs SET status='interrupted',finished=? WHERE status='running'",(time.time(),))
    def recent(self):
        with self.connect() as c:
            c.row_factory=sqlite3.Row
            return [dict(r) for r in c.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 100")]
    def used(self):
        with self.connect() as c: return c.execute("SELECT coalesce(sum(finished-started),0) FROM runs WHERE started>=?",(time.time()-86400,)).fetchone()[0]
@contextlib.contextmanager
def exclusive(path):
    with open(path,'a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
def cycle(cfg,state):
    if not cfg.get('enabled',False): return
    if cfg.get('pause_file') and pathlib.Path(cfg['pause_file']).exists(): return
    hours=cfg.get('allowed_hours',list(range(24)))
    if time.localtime().tm_hour not in hours: return
    if state.used()>=cfg.get('daily_seconds',3600): return
    for q in cfg['queues']:
        if state.used()>=cfg.get('daily_seconds',3600): break
        ident=state.start(q['repo'])
        try:
            r=subprocess.run([sys.executable,str(ROOT/'runner.py'),'--repo',q['repo'],'--checkout',q['checkout'],'--policy',q['policy'],'once'],capture_output=True,text=True)
            state.finish(ident,'ok' if r.returncode==0 else 'failed',r.stdout+'\n'+r.stderr)
        except Exception as e: state.finish(ident,'failed',type(e).__name__)
def dashboard(state,port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ('/','/api/runs'): self.send_error(404); return
            rows=state.recent()
            if self.path=='/api/runs': body=json.dumps(rows); mime='application/json'
            else:
                body='<meta charset=utf-8><meta name=viewport content="width=device-width"><title>Experiment runner</title><style>body{font:16px system-ui;max-width:960px;margin:2em auto;padding:1em}article{border-bottom:1px solid #aaa;padding:1em 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Experiment runner</h1><p>Local execution history</p>'+''.join('<article><b>'+escape(r['repo'])+'</b> — '+escape(r['status'])+'<details><summary>Log</summary><pre>'+escape(r['log'] or '')+'</pre></details></article>' for r in rows);mime='text/html; charset=utf-8'
            data=body.encode();self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'");self.end_headers();self.wfile.write(data)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
def main():
    a=argparse.ArgumentParser();a.add_argument('--config',required=True);a.add_argument('action',choices=['once','serve','dashboard','status']);a.add_argument('--port',type=int,default=8765);x=a.parse_args()
    path=pathlib.Path(x.config);cfg=json.loads(path.read_text());state=State(cfg['state'])
    if x.action=='dashboard': return dashboard(state,x.port)
    if x.action=='status': print(json.dumps(state.recent(),indent=2));return
    with exclusive(str(state.path)+'.lock'):
        state.recover()
        while True:
            cfg=json.loads(path.read_text());cycle(cfg,state)
            if x.action=='once': break
            time.sleep(max(15,cfg.get('poll_seconds',60))+random.uniform(0,5))
if __name__=='__main__': main()
