import global_vars

DEBUG = True

global_vars.set_var('level', 'locations/' + input('level: '))
plants = []
print("Choose Plants:")
stop = False
while len(plants) < 6 and not stop:
    choice = input()
    if choice != '':
        plants.append("plants:" + choice)
    else:
        stop = True

global_vars.set_var(
    'plants', plants
)
global_vars.set_var('DEBUG', DEBUG)

import main

try:
    if global_vars.get_var("complete"):
        print("You beat: " + global_vars.get_var("level").split(":")[1] + "!")
except KeyError:
    pass
