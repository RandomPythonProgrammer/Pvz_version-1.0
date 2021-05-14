global_vars = {}


def get_var(var_name):
    return global_vars[var_name]


def set_var(var_name, value):
    global_vars[var_name] = value
    return global_vars[var_name]
