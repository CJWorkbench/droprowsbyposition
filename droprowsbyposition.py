import re
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd
from cjwmodule import i18n

commas = re.compile(r"\s*,\s*")
numbers = re.compile(r"(?P<first>[1-9]\d*)(?:-(?P<last>[1-9]\d*))?")


class RangeFormatError(ValueError):
    def __init__(self, value):
        self.value = value

    @property
    def i18n_message(self) -> i18n.I18nMessage:
        return i18n.trans(
            "badParam.rows.invalidRange",
            'Rows must look like "1-2", "5" or "1-2, 5"; got "{value}"',
            {"value": self.value},
        )


class BackwardsRangeError(ValueError):
    def __init__(self, value):
        self.value = value

    @property
    def i18n_message(self) -> i18n.I18nMessage:
        return i18n.trans(
            "badParam.rows.backwardsRange",
            'Row ranges must increase like "1-3", not "3-1"; got "{value}"',
            {"value": self.value},
        )


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
    RangeFormatError: Rows must look like "1-2", "5" or "1-2, 5"; got "hi"
    >>> parse_interval('12-10')
    Traceback (most recent call last):
        ...
    BackwardsRangeError: Row ranges must increase like "1-3", not "3-1"; got "12-10"
    """
    match = numbers.fullmatch(s)
    if not match:
        raise RangeFormatError(s)

    first = int(match.group("first"))
    last = int(match.group("last") or first)
    if first > last:
        raise BackwardsRangeError(s)
    return (first - 1, last)


def parse_mask(rows: str, n_rows: int) -> np.array:
    """Parse 'rows', or raise RangeFormatError or BackwardsRangeError"""
    mask = np.zeros(n_rows, np.bool)
    for s in commas.split(rows.strip()):
        if s:
            begin, end = parse_interval(s)  # raise RangeFormatError/BackwardsRangeError
            mask[begin:end] = True
    return mask


def render(table, params):
    try:
        mask = parse_mask(params["rows"], len(table))
    except (RangeFormatError, BackwardsRangeError) as err:
        return err.i18n_message

    if table.empty:
        # https://www.pivotaltracker.com/n/projects/2132449/stories/161945860
        return table

    table = table[~mask]
    table.reset_index(drop=True, inplace=True)
    for column in table.columns:
        series = table[column]
        if hasattr(series, "cat"):
            series.cat.remove_unused_categories(inplace=True)
    return table


def _migrate_params_v0_to_v1(params):
    """
    v0: optional "first_row" and "last_row" were fallback if "rows" empty.

    v1: always use "rows".

    (droprowsbyposition had some special logic and special visible_if rules
    because we changed its feature set before migrate_params() existed. That's
    why this migration handles two cases.)
    """
    if params["rows"]:
        return {"rows": params["rows"]}
    else:
        return {"rows": "%d-%d" % (params["first_row"], params["last_row"])}


def migrate_params(params):
    if "first_row" in params:
        params = _migrate_params_v0_to_v1(params)
    return params
