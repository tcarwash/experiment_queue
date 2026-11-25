import tempfile,pathlib,unittest
from unittest.mock import patch
from service import State,cycle,exclusive
class Service(unittest.TestCase):
    def test_state(self):
        with tempfile.TemporaryDirectory() as t:
            s=State(pathlib.Path(t)/'state')
            i=s.start('owner/repo');s.finish(i,'ok','done')
            s.start('owner/second');s.recover()
            self.assertEqual([x['status'] for x in s.recent()],['interrupted','ok'])
            self.assertGreaterEqual(s.used(),0)
    def test_disabled(self):
        with tempfile.TemporaryDirectory() as t:
            s=State(pathlib.Path(t)/'state')
            with patch('service.subprocess.run') as run:
                cycle({'enabled':False},s);run.assert_not_called()
    def test_lock(self):
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t)/'lock'
            with exclusive(p):
                with self.assertRaises(BlockingIOError):
                    with exclusive(p): pass
