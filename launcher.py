import global_vars

DEBUG = False

global_vars.set_var('level', 'locations/' + input('level: '))
plants = []
print("Choose Plants:")
while len(plants) < 6:
    plants.append("plants:" + input())

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
