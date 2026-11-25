import tempfile, pathlib, unittest, subprocess
from runner import Lease, manifest, matches
class Test(unittest.TestCase):
    def test_claim(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)
            def g(*a): subprocess.run(['git',*a],cwd=root,check=True,capture_output=True)
            g('init','--bare','remote'); g('clone','remote','a'); g('clone','remote','b')
            a=Lease(root/'a',1,'a'); b=Lease(root/'b',1,'b')
            self.assertTrue(a.claim()); self.assertFalse(b.claim())
            self.assertTrue(a.renew()); self.assertTrue(a.release())
            self.assertTrue(b.claim()); self.assertFalse(a.renew())
    def test_policy(self):
        d={'source':'a','execution':'scripted','timeout':10,'capabilities':['cpu']}
        p={'allowed_sources':['a'],'max_seconds':20,'capabilities':['cpu'],'allow_native':True}
        self.assertTrue(matches(d,p)); p['allow_native']=False; self.assertFalse(matches(d,p))
    def test_manifest(self):
        with self.assertRaises(ValueError): manifest('nothing')
if __name__=='__main__': unittest.main()
