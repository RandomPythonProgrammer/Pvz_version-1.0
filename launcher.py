import global_vars

try:
    if global_vars.get_var("complete"):
        print("Win!!!!! " + global_vars.get_var("level"))
except KeyError:
    global_vars.set_var('level', 'levels:' + input('level: '))
    global_vars.set_var(
        'plants', [
            'plants:sunflower',
            'plants:peashooter',
            'plants:repeater',
            'plants:walnut',
            'plants:potatomine',
        ]
    )
    import main