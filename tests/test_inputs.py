import pathlib,tempfile,unittest,subprocess
from inputs import validate,approved,export_tree,safe_path
class Inputs(unittest.TestCase):
    def test_paths(self):
        for p in ('../x','/etc','a/../b','a/.git/config','a\\b','a//b'):
            with self.subTest(p=p),self.assertRaises(ValueError): safe_path(p)
    def test_allowlist(self):
        i={'name':'data','repository':'self','revision':'a'*40,'paths':['fixtures/']}
        validate([i]); self.assertFalse(approved([i],{})); self.assertTrue(approved([i],{'allowed_inputs':['self']}))
        with self.assertRaises(ValueError): validate([i,i])
    def test_export(self):
        with tempfile.TemporaryDirectory() as t:
            r=pathlib.Path(t)/'repo';r.mkdir()
            def g(*args): return subprocess.check_output(['git',*args],cwd=r,stderr=subprocess.DEVNULL).decode().strip()
            g('init');(r/'fixtures').mkdir();(r/'fixtures/a').write_text('hello');(r/'secret').write_text('not selected');(r/'link').symlink_to('/etc/passwd')
            g('add','.');g('commit','-m','fixture');rev=g('rev-parse','HEAD')
            out=pathlib.Path(t)/'out'
            self.assertEqual(export_tree(r,rev,['fixtures'],out,10),5)
            self.assertEqual((out/'fixtures/a').read_text(),'hello');self.assertFalse((out/'secret').exists())
            with self.assertRaises(ValueError): export_tree(r,rev,['link'],pathlib.Path(t)/'bad',10)
            with self.assertRaises(ValueError): export_tree(r,rev,['fixtures'],pathlib.Path(t)/'small',1)
            with self.assertRaises(ValueError): export_tree(r,rev,['missing'],pathlib.Path(t)/'missing',10)
