import json, pathlib, subprocess, tempfile, types, unittest
import campaigns,publication
from runner import git
class Publication(unittest.TestCase):
    def test_git_accepted_and_recover_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            def g(cwd,*args):
                return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.DEVNULL).decode().strip()
            g(root,'init','--bare','-b','main','upstream.git')
            g(root,'clone','upstream.git','checkout')
            repo=root/'checkout'
            g(repo,'config','user.name','Experiment CI')
            g(repo,'config','user.email','ci@example.invalid')
            (repo/'README.md').write_text('queue')
            g(repo,'add','.');g(repo,'commit','-m','Initialize');g(repo,'push','origin','main')
            spec={'schema':'experiment/v1','replication':{'desired_runs':2,'distinct_runners':True}}
            attempt='a'*32
            record={'attempt':attempt,'runner':'runner-a','manifest':spec}
            path=repo/'results'/'9'/attempt
            path.mkdir(parents=True);(path/'provenance.json').write_text(json.dumps(record))
            g(repo,'add','.');g(repo,'commit','-m','Add first result')
            g(repo,'push','origin','HEAD:refs/heads/results/experiment-9/'+attempt)
            # Restore checkout to published main (no result accepted).
            g(repo,'reset','--hard','origin/main')
            x=types.SimpleNamespace(checkout=repo,repo='owner/research')
            prs=[];calls=[]
            def gh(repo,*a):
                self.assertEqual(a[:2],('pr','list'))
                return prs
            def run(*a):
                calls.append(a)
                return types.SimpleNamespace(stdout='https://example.invalid/pr/1')
            class Lease:
                def renew(self): return True
            accepted,pending=publication.branch_records(x,9,spec,git,gh,run,Lease())
            self.assertEqual(len(accepted),0)
            self.assertEqual(len(pending),1)
            self.assertEqual(campaigns.count(spec,pending),1)
            self.assertEqual(len(calls),1)
            # Once merged on main, the branch must not be counted twice.
            g(repo,'fetch','origin','results/experiment-9/'+attempt)
            g(repo,'merge','--ff-only','FETCH_HEAD')
            g(repo,'push','origin','main')
            accepted,pending=publication.branch_records(x,9,spec,git,gh,run,Lease())
            self.assertEqual(len(accepted),1)
            self.assertEqual(len(pending),0)
            self.assertEqual(len(calls),1)
    def test_reconcile(self):
        spec={'replication':{'desired_runs':2,'distinct_runners':True}}
        x=types.SimpleNamespace(checkout='x',repo='owner/research')
        class Lease:
            def renew(self): return True
        calls=[]
        def run(*a): calls.append(a)
        r=lambda runner,attempt:{'runner':runner,'attempt':attempt,'manifest':spec}
        self.assertFalse(publication.reconcile(x,10,spec,[r('a','1')],[],run,Lease()))
        self.assertTrue(publication.reconcile(x,10,spec,[r('a','1'),r('b','2')],[],run,Lease()))
        self.assertEqual(len(calls),2)
        self.assertIn('close',calls[0])
        self.assertIn('--remove-label',calls[1])
        self.assertIn('experiment-ready',calls[1])
    def test_pending_skips_without_completion(self):
        spec={'replication':{'desired_runs':2,'distinct_runners':True}}
        x=types.SimpleNamespace(repo='owner/research')
        records=[{'runner':n,'attempt':str(i),'manifest':spec} for i,n in enumerate(('a','b'))]
        calls=[]
        class Lease:
            def renew(self): return True
        self.assertTrue(publication.reconcile(x,33,spec,[],records,lambda *a: calls.append(a),Lease()))
        self.assertEqual(calls,[])

