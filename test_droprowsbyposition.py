import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from droprowsbyposition import migrate_params, render
from cjwmodule.testing.i18n import i18n_message


class TestMigrateParams(unittest.TestCase):
    def test_v0_with_first_row_and_last_row(self):
        # droprowsbyposition got some behavior prior to our migrate_params()
        # idea. So it actually has two logic paths....
        self.assertEqual(
            migrate_params(
                {
                    "rows": "",
                    "first_row": 2,
                    "last_row": 54,
                }
            ),
            {
                "rows": "2-54",
            },
        )

    def test_v0_with_rows(self):
        self.assertEqual(
            migrate_params(
                {
                    "rows": "1-23",
                    # first_row and last_row are 'backup' values, only for when 'rows'
                    # is not set. So they'll be dropped.
                    "first_row": 2,
                    "last_row": 54,
                }
            ),
            {
                "rows": "1-23",
            },
        )

    def test_v1(self):
        self.assertEqual(
            migrate_params(
                {
                    "rows": "1-23",
                }
            ),
            {
                "rows": "1-23",
            },
        )


class TestDropRowsByPosition(unittest.TestCase):
    def setUp(self):
        # Test data includes some partially and completely empty rows because
        # this tends to freak out Pandas
        self.table = pd.DataFrame(
            {
                "A": [1, 2, 3, 4],
                "B": [2, 3, None, 5],
                "C": [None, None, None, None],
            }
        )

    def test_default_params_NOP(self):
        out = render(self.table, {"rows": ""})
        assert_frame_equal(out, self.table)

    def test_empty_input_NOP(self):
        # https://www.pivotaltracker.com/n/projects/2132449/stories/161945860
        out = render(pd.DataFrame(), {"rows": ""})
        self.assertTrue(out.empty)

    def test_drop_one_row(self):
        out = render(self.table, {"rows": "2"})
        assert_frame_equal(
            out,
            pd.DataFrame(
                {
                    "A": [1, 3, 4],
                    "B": [2, None, 5],
                    "C": [None, None, None],
                }
            ),
        )

    def test_drop_first_rows(self):
        out = render(self.table, {"rows": "1-2"})
        assert_frame_equal(
            out,
            pd.DataFrame(
                {
                    "A": [3, 4],
                    "B": [None, 5],
                    "C": [None, None],
                }
            ),
        )

    def test_drop_last_rows(self):
        out = render(self.table, {"rows": "3-4"})
        assert_frame_equal(
            out,
            pd.DataFrame(
                {
                    "A": [1, 2],
                    "B": [2.0, 3.0],
                    "C": [None, None],
                }
            ),
        )

    def test_drop_multiple_interval_ranges(self):
        out = render(self.table, {"rows": "1, 3-4"})
        assert_frame_equal(
            out,
            pd.DataFrame(
                {
                    "A": [2],
                    "B": [3.0],
                    "C": [None],
                }
            ),
        )

    def test_drop_overlapping_interval_ranges(self):
        result = render(pd.DataFrame({"A": [1, 2, 3, 4, 5]}), {"rows": "1-2,2"})
        assert_frame_equal(result, pd.DataFrame({"A": [3, 4, 5]}))

    def test_drop_everything(self):
        out = render(self.table, {"rows": "1-4"})
        expected = pd.DataFrame({"A": [1], "B": [1.0], "C": [None]})[0:0]
        # Let's assert the same thing, three different ways...:
        self.assertEqual(len(out), 0)
        self.assertTrue(out.empty)
        assert_frame_equal(out, expected)

    def test_zero_gives_error(self):
        out = render(self.table, {"rows": "0-1"})
        self.assertEqual(
            out, i18n_message("badParam.rows.invalidRange", {"value": "0-1"})
        )

    def test_backwards_range_gives_error(self):
        out = render(self.table, {"rows": "3-1"})
        self.assertEqual(
            out, i18n_message("badParam.rows.backwardsRange", {"value": "3-1"})
        )

    def test_drop_after_end(self):
        out = render(self.table, {"rows": "5-8"})
        assert_frame_equal(
            out,
            pd.DataFrame(
                {
                    "A": [1, 2, 3, 4],
                    "B": [2, 3, None, 5],
                    "C": [None, None, None, None],
                }
            ),
        )

    def test_remove_unused_categories(self):
        result = render(
            pd.DataFrame({"A": ["a", "b", "c", "d"]}, dtype="category"), {"rows": "1-2"}
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["c", "d"]}, dtype="category"))

    def test_remove_unused_categories_for_empty_row(self):
        result = render(
            pd.DataFrame({"A": ["a", "b", "c", "d"]}, dtype="category"), {"rows": "1-4"}
        )
        assert_frame_equal(result, pd.DataFrame({"A": []}, dtype="category"))
