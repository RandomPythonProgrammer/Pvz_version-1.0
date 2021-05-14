import time
import pygame as pg
import json
import random

SCALE = 64
FPS = 60
SCREEN_HEIGHT = 11 * SCALE
SCREEN_WIDTH = 11 * SCALE
VOLUME = 1.2

pg.font.init()
pg.mixer.init()
window = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SCALED)
pg.display.set_caption('PVZ clone')
pg.display.set_icon(pg.image.load('data/plants/repeater/sprite0.png').convert_alpha())
clock = pg.time.Clock()

plant_sound = pg.mixer.Sound('data/other/grass/plant.mp3')
plant_sound.set_volume(VOLUME)
sun_pickup_sound = pg.mixer.Sound('data/other/sun/pickup.mp3')
sun_pickup_sound.set_volume(VOLUME)
select_sound = pg.mixer.Sound('data/other/menus/select.mp3')
select_sound.set_volume(VOLUME)
remove_sound = pg.mixer.Sound('data/other/grass/remove.mp3')
remove_sound.set_volume(VOLUME)
eat_sound = pg.mixer.Sound('data/zombies/other/eat.mp3')
eat_sound.set_volume(VOLUME)


def get_data(full_id):
    item_type, item_id = full_id.split(':')
    with open(f'data/{item_type}/{item_id}/data.json', 'r') as data_file:
        return json.load(data_file)


class Bullet:
    def __init__(self, x, y, projectile_id):
        self.x = x
        self.y = y
        self.data = get_data(projectile_id)
        self.speed = self.data['projectile_speed']
        self.damage = self.data['damage']
        self.lane = self.y / SCALE
        self.sprite = pg.image.load(self.data['sprite']).convert_alpha()
        try:
            self.hit_sound = pg.mixer.Sound(self.data['hit_sound'])
            self.hit_sound.set_volume(VOLUME)
            self.fire_sound = pg.mixer.Sound(self.data['fire_sound'])
            self.fire_sound.set_volume(VOLUME)
        except ValueError:
            pass

    def tick(self, frame_number):
        if frame_number % 2 == 0:
            self.x += self.speed
            for zombie in zombies:
                if zombie.lane == self.lane:
                    if pg.Rect(zombie.x, zombie.y, SCALE, SCALE).colliderect(pg.Rect(self.x, self.y, SCALE, SCALE)):
                        zombie.health -= self.damage
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

    def tick(self, frame_number):
        try:
            if len(self.data['tick']) > 0:
                exec("\n".join(self.data['tick']))
            else:
                exec(self.data['tick'])
        except KeyError:
            if frame_number % 3 == 0 and self.eat is None:
                self.x -= self.speed
                if self.x < 0:
                    print('lost')
                    zombies.remove(self)
            if (frame_number - self.start_time) % 50 == 0 and self.eat is not None:
                self.eat.health -= self.damage
                eat_sound.play()
                if self.eat.health <= 0:
                    try:
                        plants.remove(self.eat)
                        self.eat.tile.occupied = False
                    except ValueError:
                        self.eat.tile.occupied = False
                if self.eat not in plants:
                    self.eat = None

                    self.eat = None
            if self.health <= 0:
                zombies.remove(self)
            for plant in plants:
                if pg.Rect(plant.x, plant.y, SCALE, SCALE).colliderect(pg.Rect(self.x, self.y, SCALE, SCALE*2)) and self.lane == plant.lane:
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

        self.data = get_data(plant_id)

        self.health = self.data['health']
        self.sprite = pg.image.load(get_data(self.id)['sprite']).convert_alpha()
        self.cost = self.data['cost']
        self.state = 0
        self.countdown = 0
        self.queue = []

    def tick(self, frame_number):
        try:
            if len(self.data['tick']) > 0:
                exec("\n".join(self.data['tick']))
            else:
                exec(self.data['tick'])
        except KeyError:
            try:
                if (self.start_time - frame_number) % (1 / self.data['attack_speed']) == 0:
                    for i in range(self.data['burst']):
                        self.queue.append(self.attack)
                if frame_number % 8 == 0:
                    if len(self.queue) > 0:
                        self.queue[0]()
                        self.queue.remove(self.queue[0])
            except KeyError:
                pass

    def attack(self):
        if type(self.data['attack']) == list:
            exec(str("\n".join(self.data['attack'])))
        else:
            exec(str(self.data['attack']))

    def draw(self, surface):
        surface.blit(self.sprite, (int(self.x), int(self.y)))


class Sun:
    def __init__(self, x, y, value=25, sunflower=False):
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


class Tile:
    def __init__(self, x, y, version):
        self.x = x
        self.y = y
        self.occupied = False
        self.species = random.randint(1, 4)
        self.version = version
        self.sprite = pg.image.load(f'data/other/grass/grass{str(self.version)}-{str(self.species)}.png')

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
            surface.blit(font.render(f"{item['cost']}", False, color), (item['x'], item['y'] + SCALE))
            if item['cooldown'] > 0:
                overlay = pg.Surface((SCALE, SCALE))
                overlay.set_alpha(100)
                overlay.fill((255, 0, 0))
                surface.blit(overlay, (item['x'], item['y']))
            if self.selected == item['id']:
                surface.blit(self.selected_sprite, (item['x'], item['y']))
        surface.blit(font.render(f'Sun: {sun_count}', False, (0, 0, 0)), (0, 9 * SCALE))


run = True
tiles = []
plants = []
font = pg.font.SysFont('Comic Sans MS', 16, bold=True)
sun_count = 0
suns = []
projectiles = []
selected_plant = None
chosen_plants = ['plants:repeater', 'plants:sunflower', 'plants:potatomine', 'plants:walnut', 'plants:peashooter']
bottom_bar = BottomBar(chosen_plants)
zombies = []
cooldown_start_time = time.time()
current_level = 'levels:1-1'
zombie_queue = []
wave_mode = False
waves = get_data(current_level)['waves']
wave_time = None
level_data = get_data(current_level)
game_start = False


def tick(frame_number):
    global level_data
    global wave_mode
    global wave_time
    global game_start
    global run
    if random.randint(0, 450) == 1:
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

    if time.time() - cooldown_start_time > 25 and not wave_mode:
        if len(zombie_queue) == 0 and wave_zombie_count == 0:
            roam_zombies = level_data['roam_zombies']
            for key in list(roam_zombies.keys()):
                for i in range(roam_zombies[key]):
                    zombie_queue.append(key)

        if len(zombie_queue) > 0:
            rate = int(800-(time.time() - cooldown_start_time))
            if rate < 2:
                rate = 2
            if random.randint(0, rate) == 1:
                zombie_choice = random.choice(zombie_queue)
                zombies.append(Zombie(zombie_choice, 10*SCALE, random.randint(1, 8)*SCALE, frame))
                zombie_queue.remove(zombie_choice)
        if len(zombie_queue) == 0 and wave_zombie_count == 0:
            wave_mode = True
            wave_time = time.time()

    if wave_mode:
        if time.time() - wave_time > 5:
            try:
                wave = waves[0]
            except IndexError:
                print("win!!!!")
                run = False
            for key in list(wave.keys()):
                for i in range(wave[key]):
                    zombie_queue.append(key)
            while len(zombie_queue) > 1:
                zombie_choice = random.choice(zombie_queue)
                zombies.append(Zombie(zombie_choice, 10 * SCALE, random.randint(1, 8) * SCALE, frame, wave=True))
                zombie_queue.remove(zombie_choice)
            waves.remove(wave)
            wave_mode = False


def draw_screen(surface, frame_number):
    surface.fill((150, 150, 255))

    for tile in tiles:
        tile.draw(surface)
    for plant in plants:
        plant.draw(surface)
    for sun in suns:
        sun.draw(surface)
    for zombie in zombies:
        zombie.draw(surface)
    for projectile in projectiles:
        projectile.draw(surface)

    bottom_bar.draw(surface)

    pg.display.update()


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
while run:
    clock.tick(FPS)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_z:
                zombies.append(Zombie('zombies:basic', 10*SCALE, random.randint(1, 8)*SCALE, frame))
            if event.key == pg.K_s:
                sun_count += 500
            if event.key == pg.K_c:
                for item in bottom_bar.items:
                    item['cooldown'] = 0

    if pg.mouse.get_pressed()[0]:
        if selected_plant is not None:
            for item in bottom_bar.items:
                if item['id'] == selected_plant and item['cooldown'] <= 0 and sun_count >= get_data(selected_plant)['cost']:
                    for tile in tiles:
                        if not tile.occupied and pg.Rect(tile.x, tile.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                            tile.occupied = True
                            plants.append(Plant(selected_plant, tile, frame_num=frame))
                            sun_count -= get_data(selected_plant)['cost']
                            for item in bottom_bar.items:
                                if item['id'] == selected_plant:
                                    item['cooldown'] = get_data(item['id'])['cooldown']
                                    selected_plant = None
                                    bottom_bar.selected = None
                            plant_sound.play()

        for sun in suns:
            if pg.Rect(sun.x, sun.y, SCALE / 2, SCALE / 2).collidepoint(pg.mouse.get_pos()):
                sun_count += sun.value
                suns.remove(sun)
                sun_pickup_sound.play()

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()) and selected_plant != item['id']:
                    selected_plant = item['id']
                    bottom_bar.selected = item['id']
                    select_sound.play()

    if pg.mouse.get_pressed()[2]:
        for plant in plants:
            if pg.Rect(plant.x, plant.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                plant.tile.occupied = False
                plants.remove(plant)
                remove_sound.play()

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()) and selected_plant == item['id']:
                selected_plant = None
                bottom_bar.selected = None

    frame += 1

    if frame > FPS * 60:
        frame = 1

    tick(frame)

    draw_screen(window, frame)
