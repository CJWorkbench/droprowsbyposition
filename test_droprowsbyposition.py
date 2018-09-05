import unittest
import pandas as pd
from droprowsbyposition import render


class TestDropRowsByPosition(unittest.TestCase):
    def setUp(self):
        # Test data includes some partially and completely empty rows because
        # this tends to freak out Pandas
        self.table = pd.DataFrame(
            [
                ['fred', 2, 3, '2018-1-12'],
                ['frederson', 5, None, '2018-1-12 08:15'],
                [None,  None,  None,  None],
                ['maggie', 8, 10, '2015-7-31']
            ],
            columns=['a', 'b', 'c', 'date']
        )

    def test_drop_first_row(self):
        params = {'first_row': 1,  'last_row': 1}
        out = render(self.table,  params)
        ref = self.table.copy().iloc[1:]
        self.assertTrue(out.equals(ref))

    def test_middle_rows(self):
        params = {'first_row': 2,  'last_row': 2}
        out = render(self.table,  params)
        ref = self.table.copy()
        ref = pd.concat([ref.iloc[0:1],  ref.iloc[2:]])
        self.assertTrue(out.equals(ref))
