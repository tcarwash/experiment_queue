import tempfile,pathlib,unittest
from findings import search
from mcp_server import dispatch
class Interfaces(unittest.TestCase):
    def test_findings(self):
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t)/'results/1/attempt';p.mkdir(parents=True);(p/'report.md').write_text('Negative finding: noise increased')
            self.assertEqual(search(t,'negative noise')[0]['issue'],'1')
            self.assertEqual(search(t,'positive'),[])
            r=dispatch('tools/call',{'name':'search_findings','arguments':{'query':'noise'}},{'checkout':t})
            self.assertIn('Negative finding',r['content'][0]['text'])
    def test_mcp(self):
        self.assertEqual(len(dispatch('tools/list',{}, {})['tools']),2)
