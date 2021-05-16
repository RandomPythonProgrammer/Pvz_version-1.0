import global_vars

global_vars.set_var('level', 'locations/' + input('level: '))
global_vars.set_var(
    'plants', [
        'plants:sunflower',
        'plants:peashooter',
        'plants:repeater',
        'plants:walnut',
        'plants:potatomine',
        'plants:puffshroom'
    ]
)
import main

try:
    if global_vars.get_var("complete"):
        print("You beat: " + global_vars.get_var("level").split(":")[1] + "!")
except KeyError:
    pass