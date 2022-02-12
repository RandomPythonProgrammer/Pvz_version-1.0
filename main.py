import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
import json
import random
import global_vars
import math

SCALE = 64
FPS = 60
SCREEN_HEIGHT = 11 * SCALE
SCREEN_WIDTH = 11 * SCALE
VOLUME = 1.2
LANES = 7
DEBUG = global_vars.get_var('DEBUG')

pg.font.init()
pg.mixer.init()
window = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SCALED)
pg.display.set_caption('PVZ clone')
pg.display.set_icon(pg.image.load('data/plants/repeater/sprite0.png').convert_alpha())
clock = pg.time.Clock()


def get_data(full_id):

    with open(os.path.dirname(__file__) + '/data/' + "/".join(full_id.split(':')) + '/data.json', 'r') as data_file:
        return json.load(data_file)


def get_image(full_id):
    return str('data/' + "/".join(full_id.split(':')) + '.png')


def get_sound(full_id):
    return str('data/' + "/".join(full_id.split(':')) + '.mp3')


class Drawable:
    def __init__(self, image_source, location, drawable_id):
        self.x, self.y = location
        self.location = location
        self.image = pg.image.load(image_source).convert_alpha()
        self.id = drawable_id

    def draw(self, surface):
        surface.blit(self.image, self.location)
3

class Bullet:
    def __init__(self, x, y, projectile_id, damage=None, angle=0):
        self.x = x
        self.y = y
        self.data = get_data(projectile_id)
        self.angle = angle
        self.speed = self.data['projectile_speed']
        self.change_y = math.sin((self.angle*math.pi/180))*self.speed
        self.change_x = math.cos((self.angle*math.pi/180))*self.speed
        if damage is not None:
            self.damage = damage
        else:
            self.damage = self.data['damage']
        self.lane = self.y / SCALE
        self.sprite = pg.image.load(self.data['sprite']).convert_alpha()
        try:
            self.hit_sound = Sound(self.data['hit_sound'])
            Sound(self.data['fire_sound']).play()
        except ValueError:
            pass

    def tick(self, frame_number):
        if self.x > SCREEN_WIDTH:
            projectiles.remove(self)
        if frame_number % 2 == 0:
            self.x += self.change_x
            self.y += self.change_y
            for zombie in zombies:
                if zombie.lane == self.lane:
                    if pg.Rect(zombie.x, zombie.y, SCALE, SCALE).colliderect(pg.Rect(self.x, self.y, SCALE, SCALE)):
                        zombie.shield -= self.damage
                        try:
                            self.hit_sound.play()
                        except NameError:
                            pass
                        try:
                            projectiles.remove(self)
                        except ValueError:
                            pass
            if self.x > SCREEN_WIDTH:
                projectiles.remove(self)

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))


class Fume:
    def __init__(self, x, y, projectile_id, damage=None, length=4, angle=0):
        self.x = x
        self.y = y
        self.data = get_data(projectile_id)
        if damage is None:
            self.damage = self.data['damage']
        else:
            self.damage = damage
        self.lane = self.y / SCALE
        self.length = length
        self.sprite = pg.image.load(self.data['sprite']).convert_alpha()

        try:
            self.hit_sound = Sound(self.data['hit_sound'])
            Sound(self.data['fire_sound']).play()
        except ValueError:
            pass
        self.start_time = time.time()
        for zombie in zombies:
            if zombie.lane == self.lane:
                if pg.Rect(zombie.x, zombie.y, SCALE, SCALE).colliderect(pg.Rect(self.x, self.y, self.length*SCALE, SCALE)):
                    zombie.health -= self.damage
                    try:
                        self.hit_sound.play()
                    except NameError:
                        pass

    def tick(self, frame_number):
        if time.time() - self.start_time > 1.5:
            projectiles.remove(self)

    def draw(self, surface):
        for i in range(self.length):
            surface.blit(self.sprite, (self.x + i * SCALE, self.y))


class Zombie:
    def __init__(self, zombie_id, x, y, frame_num, wave=False):
        self.id = zombie_id
        self.x = x
        self.y = y
        self.start_time = frame_num
        self.lane = self.y / SCALE
        self.wave = wave

        self.data = get_data(zombie_id)

        self.health = self.data['health']
        self.sprite = pg.image.load(get_data(self.id)['sprite']).convert_alpha()
        self.speed = self.data['speed']
        self.eat = None
        self.damage = self.data['damage']
        self.state = 0
        self.cooldown = 0
        try:
            self.shield = self.data['shield']
        except KeyError:
            self.shield = 0

    def tick(self, frame_number):
        try:
            if type(self.data['tick']) == list:
                exec("\n".join(self.data['tick']))
            else:
                exec(self.data['tick'])
        except KeyError:
            self.default_tick(frame_number)

    def default_tick(self, frame_number):
        global run
        if self.shield < 0:
            self.health -= abs(self.shield)
            self.shield = 0
        if frame_number % 3 == 0 and self.eat is None:
            self.x -= self.speed
            if self.x < 0:
                print('lost')
                if not DEBUG:
                    run = False
                zombies.remove(self)
        if (frame_number - self.start_time) % 50 == 0 and self.eat is not None:
            self.eat.health -= self.damage
            Sound('sounds:eat').play()
            if self.eat.health <= 0:
                try:
                    plants.remove(self.eat)
                    self.eat.tile.occupied = False
                except ValueError:
                    self.eat.tile.occupied = False
            if self.eat not in plants:
                self.eat = None

        if self.health <= 0:
            zombies.remove(self)
        for plant in plants:
            if pg.Rect(plant.x, plant.y, SCALE, SCALE).colliderect(
                    pg.Rect(self.x, self.y, SCALE, SCALE * 2)) and self.lane == plant.lane:
                self.eat = plant

    def attack(self):
        if type(self.data['attack']) == list:
            exec(str("\n".join(self.data['attack'])))
        else:
            exec(str(self.data['attack']))

    def draw(self, surface):
        surface.blit(self.sprite, (int(self.x), int(self.y) - SCALE))


class Plant:
    def __init__(self, plant_id, connected_tile, frame_num):
        self.id = plant_id
        self.tile = connected_tile
        self.x = self.tile.x
        self.y = self.tile.y
        self.start_time = frame_num
        self.lane = self.y / SCALE
        self.time_starting = time.time()

        self.data = get_data(plant_id)

        try:
            self.plantable = self.data['plantable']
        except KeyError:
            self.plantable = False

        self.health = self.data['health']
        self.sprite = pg.image.load(get_data(self.id)['sprite']).convert_alpha()
        self.cost = self.data['cost']
        self.state = 0
        self.queue = []
        self.return_value = None

    def tick(self, frame_number):
        try:
            if type(self.data['tick']) == list:
                exec("\n".join(self.data['tick']))
            else:
                exec(self.data['tick'])
        except KeyError:
            self.default_tick(frame_number)

    def default_tick(self, frame_number):
        try:
            if int(time.time()) - int(self.time_starting) != 0 and (int(time.time()) - int(self.time_starting)) %\
                    (self.data['attack_speed']) == 0 and frame_number % 60 == 0:
                for i in range(self.data['burst']):
                    self.queue.append(self.attack)
            if frame_number % 8 == 0:
                if len(self.queue) > 0:
                    self.queue[0]()
                    self.queue.remove(self.queue[0])
        except KeyError:
            pass

    def requirements(self):
        self.return_value = None
        try:
            if type(self.data['requirements']) == list:
                exec("\n".join(self.data['requirements']))
            else:
                exec(self.data['requirements'])
        except KeyError:
            return self.default_requirements()
        if self.return_value is not None:
            return self.return_value
        else:
            return False

    def default_requirements(self):
        try:
            self_class = get_data(self.data['class'])
        except KeyError:
            self_class = get_data('plants:classes:normal')

        self.return_value = None

        if len(self_class['requirements']) > 1:
            exec("\n".join(self_class['requirements']))

        else:
            exec(get_data(self_class['requirements']))

        if self.return_value is not None:
            return self.return_value
        else:
            return False

    def attack(self):
        if type(self.data['attack']) == list:
            exec(str("\n".join(self.data['attack'])))
        else:
            exec(str(self.data['attack']))

    def draw(self, surface):
        surface.blit(self.sprite, (int(self.x), int(self.y)))


class Sun:
    def __init__(self, x, y, value=25, sunflower=False,):
        self.x = x
        if not sunflower:
            self.dest_y = y
            self.y = 0
        else:
            self.y = y
            self.dest_y = y

        self.sprite = pg.image.load('data/other/sun/sun.png').convert_alpha()
        self.timer = 0
        self.value = value
        self.speed = 1

    def draw(self, surface):
        surface.blit(self.sprite, (int(self.x), int(self.y)))

    def tick(self, frame_number):
        if self.y < self.dest_y:
            self.y += self.speed
        self.timer += 1
        if self.timer > 10 * FPS:
            suns.remove(self)


class Sound:
    def __init__(self, sound_id):
        self.source = get_sound(sound_id)
        self.sound = pg.mixer.Sound(self.source)
        self.sound.set_volume(VOLUME)

    def play(self):
        self.sound.stop()
        self.sound.play()


class Tile:
    def __init__(self, x, y, version):
        self.x = x
        self.y = y
        self.occupied = False
        self.occupied_plant = None
        self.species = random.randint(1, 4)
        self.version = version
        self.id = 'grass'
        path = location_data['tiles'] + '/' + "tile" + str(self.version) + '-' + str(self.species) + '.png'
        self.sprite = pg.image.load(path)

    def draw(self, surface):
        surface.blit(self.sprite, (int(self.x), int(self.y)))


class BottomBar:
    def __init__(self, items):
        self.items = []
        self.x = 0
        self.y = 9 * SCALE
        self.sprite = pg.image.load('data/other/menus/bottom_bar.png').convert()
        self.selected_sprite = pg.image.load('data/other/menus/selected.png').convert_alpha()
        self.selected = None

        for item in items:
            self.items.append(
                {
                    'x': 1.25 * SCALE + items.index(item) * SCALE * 1.5,
                    'y': 9.5 * SCALE,
                    'sprite': pg.image.load(get_data(item)['display_sprite']).convert_alpha(),
                    'cost': get_data(item)['cost'],
                    'id': item,
                    'cooldown': get_data(item)['starting_cooldown'],
                },
            )

    def tick(self, frame_num):
        for item in self.items:
            item['cooldown'] -= 1 / FPS
            if item['cooldown'] < 0:
                item['cooldown'] = 0

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))
        for item in self.items:
            surface.blit(item['sprite'], (item['x'], item['y']))
            if item['cost'] > sun_count:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            surface.blit(font.render(str(item['cost']), False, color), (item['x'], item['y'] + SCALE))
            if item['cooldown'] > 0:
                overlay = pg.Surface((SCALE, SCALE))
                overlay.set_alpha(100)
                overlay.fill((255, 0, 0))
                surface.blit(overlay, (item['x'], item['y']))
            if self.selected == item['id']:
                surface.blit(self.selected_sprite, (item['x'], item['y']))
        surface.blit(font.render('Sun: ' + str(sun_count), False, (0, 0, 0)), (0, 9 * SCALE))


run = True
tiles = []
plants = []
font = pg.font.SysFont('Comic Sans MS', 16, bold=True)
sun_count = 50
suns = []
projectiles = []
selected_plant = None
chosen_plants = global_vars.get_var('plants')
bottom_bar = BottomBar(chosen_plants)
zombies = []
cooldown_start_time = time.time()
current_level = global_vars.get_var('level')
zombie_queue = []
wave_mode = False
waves = get_data(current_level)['waves']
wave_time = None
level_data = get_data(current_level)
game_start = False
drawables = []
location_data = get_data('/'.join(current_level.split(':')[:-1]))
cooldown = location_data['cooldown']
chance = location_data['chance']
sun_rate = location_data['sun_rate']
background_objects = []
wave = None


def tick(frame_number):
    global cooldown_start_time
    global chance
    global level_data
    global wave_mode
    global wave_time
    global cooldown
    global game_start
    global run
    global wave
    try:
        if type(location_data['tick']) == list:
            exec("\n".join(location_data['tick']))
        else:
            exec(location_data['tick'])
    except KeyError:
        pass
    if random.randint(0, sun_rate) == 1:
        suns.append(Sun(random.randint(0, 10 * SCALE), random.randint(SCALE, 8 * SCALE)))
    for sun in suns:
        sun.tick(frame_number)
    for plant in plants:
        plant.tick(frame_number)
    for zombie in zombies:
        zombie.tick(frame_number)
    for projectile in projectiles:
        projectile.tick(frame_number)
    bottom_bar.tick(frame_number)

    wave_zombie_count = 0

    for zombie in zombies:
        if zombie.wave:
            wave_zombie_count += 1

    if time.time() - cooldown_start_time > cooldown and not wave_mode and len(waves) > 0:
        if len(zombie_queue) == 0 and wave_zombie_count == 0:
            if DEBUG:
                print("Start Roam")
            pg.mixer.fadeout(4)
            Sound('sounds:main_theme').play()
            roam_zombies = level_data['roam_zombies']
            for key in list(roam_zombies.keys()):
                for i in range(roam_zombies[key]):
                    zombie_queue.append(key)

        if len(zombie_queue) > 0:
            rate = int(chance - 5*(time.time() - cooldown_start_time))
            if rate < 120:
                rate = 120
            if random.randint(0, rate) == 1:
                zombie_choice = random.choice(zombie_queue)
                zombies.append(Zombie(zombie_choice, 10*SCALE, random.randint(1, 8)*SCALE, frame))
                zombie_queue.remove(zombie_choice)
        if len(zombie_queue) == 0 and wave_zombie_count == 0 and wave_time is None:
            count = 0
            for drawable in drawables:
                if drawable.id == 'wave':
                    count += 1
            if count == 0:
                drawables.append(Drawable(
                    image_source='data/other/menus/wave.png',
                    location=(0, 0),
                    drawable_id='wave',
                )
                )

                wave_mode = True
                wave_time = time.time()
                pg.mixer.fadeout(4)

    if len(waves) == 0 and wave_zombie_count == 0:
        run = False
        global_vars.set_var("complete", True)

    if wave_mode and time.time() - wave_time > 5 and len(zombie_queue) == 0:
        Sound('sounds:wave_theme').play()
        for drawable in drawables:
            if drawable.id == 'wave':
                drawables.remove(drawable)
        if DEBUG:
            print("Start Wave")
        wave = waves[0]
        for key in list(wave.keys()):
            for i in range(wave[key]):
                zombie_queue.append(key)
        try:
            if type(location_data['wave']) == list:
                exec("\n".join(location_data['wave']))
            else:
                exec(location_data['wave'])
        except KeyError:
            pass
    if wave_mode and len(zombie_queue) > 0:
        if frame_number % 30 == 0:
            zombie_choice = random.choice(zombie_queue)
            zombies.append(Zombie(zombie_choice, 10 * SCALE, random.randint(1, 8) * SCALE, frame, wave=True))
            zombie_queue.remove(zombie_choice)
            try:
                waves.remove(wave)
            except ValueError:
                pass
        if len(zombie_queue) == 0:
            wave_mode = False
            cooldown = 5
            cooldown_start_time = time.time()
            wave_time = None
            chance = 800


def draw_screen(surface, frame_number):
    surface.fill(location_data['background'])

    try:
        background_image = location_data['image']
        surface.blit(pg.image.load(background_image).convert(), 0, 0)
    except KeyError:
        for tile in tiles:
            tile.draw(surface)
    for background_object in background_objects:
        background_object.draw(surface)
    for plant in plants:
        plant.draw(surface)
    for i in range(1, LANES+2):
        for zombie in zombies:
            if zombie.lane == i:
                zombie.draw(surface)
    for projectile in projectiles:
        projectile.draw(surface)
    for sun in suns:
        sun.draw(surface)
    for drawable in drawables:
        drawable.draw(surface)

    bottom_bar.draw(surface)

    pg.display.update()


try:
    if len(location_data['create_tiles']) > 1:
        exec("\n".join(location_data['create_tiles']))
    else:
        exec(location_data['create_tiles'])
except KeyError:
    for x in range(0, 11):
        for y in range(1, 9):
            if x % 2 == 0:
                if y % 2 == 0:
                    tiles.append(Tile(x * SCALE, y * SCALE, 1))
                else:
                    tiles.append(Tile(x * SCALE, y * SCALE, 2))
            else:
                if y % 2 == 0:
                    tiles.append(Tile(x * SCALE, y * SCALE, 2))
                else:
                    tiles.append(Tile(x * SCALE, y * SCALE, 1))

frame = 1

try:
    if type(location_data['start']) == list:
        exec("\n".join(location_data['start']))
    else:
        exec(location_data['start'])
except KeyError:
    pass


while run:
    clock.tick(FPS)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False

        if event.type == pg.KEYDOWN and DEBUG:
            if event.key == pg.K_z:
                zombies.append(Zombie('zombies:basic', 10*SCALE, random.randint(1, 8)*SCALE, frame))
            if event.key == pg.K_s:
                sun_count += 500
            if event.key == pg.K_c:
                for item in bottom_bar.items:
                    item['cooldown'] = 0
            if event.key == pg.K_v:
                run = False
                global_vars.set_var("complete", True)

    if pg.mouse.get_pressed()[0]:
        if selected_plant is not None:
            for item in bottom_bar.items:
                if item['id'] == selected_plant and item['cooldown'] <= 0 and sun_count >= get_data(selected_plant)['cost']:
                    for tile in tiles:
                        try:
                            plantable = get_data(tile.occupied_plant)['plantable']
                        except (KeyError, AttributeError):
                            plantable = False
                        if (not tile.occupied or plantable) and pg.Rect(tile.x, tile.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                            if Plant(selected_plant, tile, frame_num=frame).requirements():
                                tile.occupied = True
                                tile.occupied_plant = selected_plant
                                plants.append(Plant(selected_plant, tile, frame_num=frame))
                                sun_count -= get_data(selected_plant)['cost']
                                for item in bottom_bar.items:
                                    if item['id'] == selected_plant:
                                        item['cooldown'] = get_data(item['id'])['cooldown']
                                        selected_plant = None
                                        bottom_bar.selected = None
                                Sound('sounds:plant').play()

        for sun in suns:
            if pg.Rect(sun.x, sun.y, SCALE / 2, SCALE / 2).collidepoint(pg.mouse.get_pos()):
                sun_count += sun.value
                suns.remove(sun)
                Sound('sounds:pickup').play()

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()) and selected_plant != item['id']:
                selected_plant = item['id']
                bottom_bar.selected = item['id']
                Sound('sounds:select').play()

    if pg.mouse.get_pressed()[2]:
        for plant in plants:
            if pg.Rect(plant.x, plant.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                plant.tile.occupied = False
                plant.tile.occupied_plant = None
                plants.remove(plant)
                Sound('sounds:remove').play()

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()) and selected_plant == item['id']:
                selected_plant = None
                bottom_bar.selected = None

    frame += 1

    if frame > FPS * 60:
        frame = 1

    tick(frame)

    draw_screen(window, frame)
