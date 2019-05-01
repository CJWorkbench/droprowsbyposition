import re
from typing import Any, Dict, Tuple
import pandas as pd
from pandas import IntervalIndex


commas = re.compile('\\s*,\\s*')
numbers = re.compile('(?P<first>[1-9]\d*)(?:-(?P<last>[1-9]\d*))?')


def parse_interval(s: str) -> Tuple[int, int]:
    """
    Parse a string 'interval' into a tuple

    >>> parse_interval('1')
    (0, 1)
    >>> parse_interval('1-3')
    (0, 2)
    >>> parse_interval('5')
    (4, 4)
    >>> parse_interval('hi')
    Traceback (most recent call last):
        ...
    ValueError: Rows must look like "1-2", "5" or "1-2, 5"; got "hi"
    """
    match = numbers.fullmatch(s)
    if not match:
        raise ValueError(
            f'Rows must look like "1-2", "5" or "1-2, 5"; got "{s}"'
        )

    first = int(match.group('first'))
    last = int(match.group('last') or first)
    return (first - 1, last - 1)


class Form:
    def __init__(self, index: IntervalIndex):
        self.index = index

    @staticmethod
    def parse_v1(rows: str) -> 'Form':
        """Parse 'rows', or raise ValueError"""
        tuples = [parse_interval(s)
                  for s in commas.split(rows.strip())]
        return Form(IntervalIndex.from_tuples(tuples, closed='both'))

    @staticmethod
    def parse_v0(first_row: str, last_row: str) -> 'Form':
        try:
            first_row = int(first_row)
        except ValueError:
            raise ValueError(f'"{first_row}" is not a number')

        try:
            last_row = int(last_row)
        except ValueError:
            raise ValueError(f'"{last_row}" is not a number')

        if first_row <= 0 or last_row <= 0:
            raise ValueError('Row numbers cannot be below 1')

        return Form(IntervalIndex.from_tuples(
            [(first_row - 1, last_row - 1)],
            closed='both'
        ))

    @staticmethod
    def parse(d: Dict[str, Any]) -> 'Form':
        if 'rows' in d and d['rows'] != '':
            return Form.parse_v1(d['rows'])
        else:
            first = d['first_row']
            last = d['last_row']

            # Drop no rows if we have default parameter settings
            if first==0 and last==0:
                return Form(pd.interval_range(start=0, end=0))

            return Form.parse_v0(first, last)


def render(table, params):
    try:
        form = Form.parse(params)
    except ValueError as err:
        return str(err)

    if table.empty:
        # https://www.pivotaltracker.com/n/projects/2132449/stories/161945860
        return table

    mask = form.index.get_indexer(table.index) == -1
    ret = table[mask]
    ret.index = pd.RangeIndex(len(ret))
    ret = ret.apply(lambda s: s.cat.remove_unused_categories()
                    if hasattr(s, 'cat') else s)
    return ret
