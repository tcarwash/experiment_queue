import unittest
from campaigns import validate,count,eligible,digest
class Campaigns(unittest.TestCase):
    def test_distinct(self):
        d={'replication':{'desired_runs':2,'distinct_runners':True}}
        r=lambda runner,attempt:{'runner':runner,'attempt':attempt,'manifest':d}
        records=[r('a','1'),r('a','2')]
        self.assertEqual(count(d,records),1)
        self.assertFalse(eligible(d,records,'a'))
        self.assertTrue(eligible(d,records,'b'))
        self.assertFalse(eligible(d,records+[r('b','3')],'c'))
        self.assertEqual(count({'other':True},records),0)
    def test_invalid(self):
        for d in ({'depends_on':[1,1]},{'depends_on':[True]},{'replication':{'desired_runs':0}},{'replication':{'distinct_runners':'yes'}}):
            with self.assertRaises(ValueError): validate(d)
    def test_digest(self): self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
