import concurrent.futures, pathlib, subprocess, tempfile, threading, unittest
from runner import Lease
class Concurrency(unittest.TestCase):
    def test_simultaneous_claims(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)
            def g(*a): subprocess.run(['git',*a],cwd=root,check=True,capture_output=True)
            g('init','--bare','remote')
            leases=[]
            for i in range(8):
                g('clone','remote',str(i)); leases.append(Lease(root/str(i),123,str(i)))
            barrier=threading.Barrier(len(leases))
            def claim(lease):
                barrier.wait(timeout=10)
                return lease.claim()
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results=list(pool.map(claim,leases))
            self.assertEqual(sum(results),1)
            winner=leases[results.index(True)]
            self.assertTrue(winner.release())
            other=leases[(results.index(True)+1)%len(leases)]
            self.assertTrue(other.claim());self.assertFalse(winner.renew())
    def test_expired_claim(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)
            def g(*a): subprocess.run(['git',*a],cwd=root,check=True,capture_output=True)
            g('init','--bare','remote');g('clone','remote','a');g('clone','remote','b')
            a=Lease(root/'a',9,'a',ttl=-1);b=Lease(root/'b',9,'b')
            self.assertTrue(a.claim());self.assertTrue(b.claim());self.assertFalse(a.release())
