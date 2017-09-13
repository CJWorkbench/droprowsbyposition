import pandas as pd

class Importable:
    @staticmethod
    def __init__(self):
        pass

    @staticmethod
    def event():
        pass

    @staticmethod
    def render(wf_module, table):
        first_row = wf_module.get_param_integer('first_row')
        last_row = wf_module.get_param_integer('last_row')
        if first_row >= 0 and last_row > 0:
            # index is zero-based
            # we don't need to decrement last_row because iloc does not include the upper bound
            if first_row != 0:
                first_row = first_row - 1
            if first_row == 0:
                newtab = table.iloc[last_row:]
            else:
                newtab = pd.concat([table.iloc[0:first_row], table.iloc[last_row:]])
            wf_module.set_ready(notify=False)
            return newtab
        else:
            return table