import json,tempfile,pathlib,unittest
from adapters import config,argv,lock
class Adapters(unittest.TestCase):
    def test_policy(self):
        d={'execution':'remote','adapter':'cluster','operation':'test','timeout':10,'parameters':{'x':'$(bad)'}}
        p={'adapters':{'cluster':{'enabled':True,'kind':'remote','argv':['/usr/local/bin/adapter'],'allowed_operations':['test']}}}
        self.assertIsNotNone(config(d,p))
        a=argv(d,p,'s','i','o','n')
        self.assertEqual(a[0],'/usr/local/bin/adapter')
        self.assertEqual(json.loads(a[-1])['parameters'],d['parameters'])
        self.assertIsNone(config(dict(d,operation='unknown'),p))
        self.assertIsNone(config(d,{}))
    def test_bench_lock(self):
        with tempfile.TemporaryDirectory() as t:
            d={'execution':'bench','adapter':'radio','operation':'measure'}
            a={'enabled':True,'kind':'bench','argv':['/bin/false'],'allowed_operations':['measure']}
            p={'adapters':{'radio':a}}
            self.assertIsNone(config(d,p))
            a['lock_file']=str(pathlib.Path(t)/'bench.lock')
            with lock(d,p):
                with self.assertRaises(BlockingIOError):
                    with lock(d,p): pass
