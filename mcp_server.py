"""Minimal stdio MCP server: local configuration, no remote shell access."""
import argparse,json,sys
from runner import queue,manifest,matches
from findings import search
TOOLS=[
 {'name':'list_experiments','description':'List ready experiments and local eligibility','inputSchema':{'type':'object','properties':{}}},
 {'name':'search_findings','description':'Search locally committed research reports','inputSchema':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}
]
def dispatch(method,params,config):
    if method=='initialize': return {'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'experiment-queue','version':'0.1'}}
    if method=='ping': return {}
    if method=='tools/list': return {'tools':TOOLS}
    if method!='tools/call': raise ValueError('unknown method')
    name=params['name'];args=params.get('arguments',{})
    if name=='search_findings': result=search(config['checkout'],args['query'])
    elif name=='list_experiments':
        result=[]
        for i in queue(config['repo']):
            try: eligible=matches(manifest(i['body']),config['policy'])
            except (ValueError,TypeError,KeyError): eligible=False
            result.append({'number':i['number'],'title':i['title'],'eligible':eligible})
    else: raise ValueError('unknown tool')
    return {'content':[{'type':'text','text':json.dumps(result)}]}
def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
    with open(a.config) as f: cfg=json.load(f)
    with open(cfg['policy']) as f: cfg['policy']=json.load(f)
    for line in sys.stdin:
        try:
            req=json.loads(line)
            if 'id' not in req: continue
            try: response={'jsonrpc':'2.0','id':req['id'],'result':dispatch(req['method'],req.get('params',{}),cfg)}
            except Exception as e: response={'jsonrpc':'2.0','id':req['id'],'error':{'code':-32603,'message':type(e).__name__}}
            print(json.dumps(response),flush=True)
        except (ValueError,TypeError): continue
if __name__=='__main__': main()
