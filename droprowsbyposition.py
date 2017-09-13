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
        if first_row != None and last_row != None:
            # index is zero-based
            first_row = first_row - 1
            last_row = last_row - 1
            newtab = table.ix[first_row:last_row]
            wf_module.set_ready(notify=False)
            return newtab
        else:
            return table