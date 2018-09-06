import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from droprowsbyposition import render


class TestDropRowsByPosition(unittest.TestCase):
    def setUp(self):
        # Test data includes some partially and completely empty rows because
        # this tends to freak out Pandas
        self.table = pd.DataFrame({
            'A': [1, 2, 3, 4],
            'B': [2, 3, None, 5],
            'C': [None, None, None, None],
        })

    def test_old_schema_drop_first_row(self):
        out = render(self.table, {'first_row': 1, 'last_row': 1})
        assert_frame_equal(out, pd.DataFrame({
            'A': [2, 3, 4],
            'B': [3, None, 5],
            'C': [None, None, None],
        }))

    def test_old_schema_drop_middle_rows(self):
        out = render(self.table, {'first_row': 2, 'last_row': 3})
        assert_frame_equal(out, pd.DataFrame({
            'A': [1, 4],
            'B': [2.0, 5.0],
            'C': [None, None],
        }))

    def test_conflict_old_and_new_schema_new_empty(self):
        out = render(self.table, {'rows': '', 'first_row': 2, 'last_row': 3})
        assert_frame_equal(out, pd.DataFrame({
            'A': [1, 4],
            'B': [2.0, 5.0],
            'C': [None, None],
        }))

    def test_conflict_old_and_new_schema_new_wins(self):
        out = render(self.table, {'rows': '1', 'first_row': 2, 'last_row': 3})
        assert_frame_equal(out, pd.DataFrame({
            'A': [2, 3, 4],
            'B': [3, None, 5],
            'C': [None, None, None],
        }))

    def test_drop_one_row(self):
        out = render(self.table, {'rows': '2'})
        assert_frame_equal(out, pd.DataFrame({
            'A': [1, 3, 4],
            'B': [2, None, 5],
            'C': [None, None, None],
        }))

    def test_drop_first_rows(self):
        out = render(self.table, {'rows': '1-2'})
        assert_frame_equal(out, pd.DataFrame({
            'A': [3, 4],
            'B': [None, 5],
            'C': [None, None],
        }))

    def test_drop_last_rows(self):
        out = render(self.table, {'rows': '3-4'})
        assert_frame_equal(out, pd.DataFrame({
            'A': [1, 2],
            'B': [2.0, 3.0],
            'C': [None, None],
        }))

    def test_drop_multiple_interval_ranges(self):
        out = render(self.table, {'rows': '1, 3-4'})
        assert_frame_equal(out, pd.DataFrame({
            'A': [2],
            'B': [3.0],
            'C': [None],
        }))

    def test_drop_everything(self):
        out = render(self.table, {'rows': '1-4'})
        expected = pd.DataFrame({'A': [1], 'B': [1.0], 'C': [None]})[0:0]
        # Let's assert the same thing, three different ways...:
        self.assertEqual(len(out), 0)
        self.assertTrue(out.empty)
        assert_frame_equal(out, expected)

    def test_zero_gives_error(self):
        out = render(self.table, {'rows': '0-1'})
        self.assertEqual(
            out,
            'Rows must look like "1-2", "5" or "1-2, 5"; got "0-1"'
        )

    def test_drop_after_end(self):
        out = render(self.table, {'rows': '5-8'})
        assert_frame_equal(out, pd.DataFrame({
            'A': [1, 2, 3, 4],
            'B': [2, 3, None, 5],
            'C': [None, None, None, None],
        }))
