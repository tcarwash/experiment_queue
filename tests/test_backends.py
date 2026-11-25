import unittest,tempfile,pathlib,sys
from executors import permitted,command
from inference import advise
class Backends(unittest.TestCase):
    def test_container(self):
        image='sha256:'+'a'*64
        d={'execution':'container','image':image,'command':['python','test.py']}
        p={'allow_container':True,'allowed_images':[image]}
        self.assertTrue(permitted(d,p))
        a=command(d,p,'/src','/inputs','/out','attempt')
        for flag in ('--network=none','--read-only','--cap-drop=ALL','--pull=never'): self.assertIn(flag,a)
        self.assertFalse(permitted(dict(d,image='python:latest'),p))
        self.assertFalse(permitted(d,{}))
    def test_ai(self):
        p={'ai':{'enabled':True,'allow_evidence_transfer':True,'roles':['report'],'backend':'fake','backends':{'fake':{'enabled':True,'argv':[sys.executable,'-c','import sys; print("draft",sys.stdin.read())']}}}}
        self.assertIsNone(advise({},'report',{}))
        self.assertIsNone(advise(p,'manage',{}))
        self.assertIn('draft',advise(p,'report',{'result':42})['draft'])
        p['ai']['allow_evidence_transfer']=False
        self.assertIsNone(advise(p,'report',{}))
