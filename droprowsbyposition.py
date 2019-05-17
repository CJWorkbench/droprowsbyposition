import re
from typing import Any, Dict, Tuple
import numpy as np
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


def parse_interval_index(rows: str) -> IntervalIndex:
    """Parse 'rows', or raise ValueError"""
    tuples = [parse_interval(s) for s in commas.split(rows.strip()) if s]
    return IntervalIndex.from_tuples(tuples, closed='both')


def render(table, params):
    try:
        index = parse_interval_index(params['rows'])
    except ValueError as err:
        return str(err)

    if table.empty:
        # https://www.pivotaltracker.com/n/projects/2132449/stories/161945860
        return table

    # index.get_indexer(table.index) breaks on overlapping index
    # (looks like pd.IntervalIndex is missing some useful stuff!)
    #
    # Simple hack: create a bitmask from the IntervalIndex
    mask = np.zeros(len(table), dtype=bool)
    for start, end in index.to_tuples():
        mask[start:end+1] = True

    table = table[~mask]
    table.reset_index(drop=True, inplace=True)
    table = table.apply(lambda s: s.cat.remove_unused_categories()
                        if hasattr(s, 'cat') else s)
    return table


def _migrate_params_v0_to_v1(params):
    """
    v0: optional "first_row" and "last_row" were fallback if "rows" empty.

    v1: always use "rows".

    (droprowsbyposition had some special logic and special visible_if rules
    because we changed its feature set before migrate_params() existed. That's
    why this migration handles two cases.)
    """
    if params['rows']:
        return {'rows': params['rows']}
    else:
        return {'rows': '%d-%d' % (params['first_row'], params['last_row'])}


def migrate_params(params):
    if 'first_row' in params:
        params = _migrate_params_v0_to_v1(params)
    return params
