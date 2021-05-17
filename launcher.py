import global_vars

DEBUG = False

global_vars.set_var('level', 'locations/' + input('level: '))
global_vars.set_var(
    'plants', [
        'plants:walnut',
        'plants:fumeshroom',
        'plants:gravebuster',
        'plants:sunshroom',
        'plants:scaredyshroom',
        'plants:puffshroom'
    ]
)
global_vars.set_var('DEBUG', DEBUG)

import main

try:
    if global_vars.get_var("complete"):
        print("You beat: " + global_vars.get_var("level").split(":")[1] + "!")
except KeyError:
    pass