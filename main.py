import pygame as pg
import json
import random

SCALE = 64
FPS = 60

pg.font.init()
window = pg.display.set_mode((13 * SCALE, 11 * SCALE), pg.SCALED)
pg.display.set_caption('PVZ clone')
pg.display.set_icon(pg.image.load('data/plants/repeater/sprite.png').convert_alpha())
clock = pg.time.Clock()


def get_data(full_id):
    item_type, item_id = full_id.split(':')
    with open(f'data/{item_type}/{item_id}/data.json', 'r') as data_file:
        return json.load(data_file)


class Zombie:
    def __init__(self, zombie_id, connected_tile, frame_num):
        self.id = zombie_id
        self.tile = connected_tile
        self.x = self.tile.x
        self.y = self.tile.y
        self.start_time = frame_num

        self.data = get_data(zombie_id)

        self.health = self.data['health']
        self.sprite = pg.image.load(get_data(self.id)['sprite']).convert_alpha()
        self.cost = self.data['cost']


class Plant:
    def __init__(self, plant_id, connected_tile, frame_num):
        self.id = plant_id
        self.tile = connected_tile
        self.x = self.tile.x
        self.y = self.tile.y
        self.start_time = frame_num

        self.data = get_data(plant_id)

        self.health = self.data['health']
        self.sprite = pg.image.load(get_data(self.id)['sprite']).convert_alpha()
        self.cost = self.data['cost']

    def tick(self, frame_number):
        try:
            if (self.start_time-frame_number) % (1/self.data['attack_speed']) == 0:
                self.attack()
        except KeyError:
            pass

    def attack(self):
        try:
            exec(str(self.data['attack']))
        except KeyError:
            pass

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))


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
        surface.blit(self.sprite, (self.x, self.y))

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
        surface.blit(self.sprite, (self.x, self.y))


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
                 'sprite': pg.image.load(get_data(item)['sprite']).convert_alpha(),
                 'cost': get_data(item)['cost'],
                 'id': item,
                 'cooldown': get_data(item)['cooldown']
                 },
            )

    def tick(self, frame_num):
        for item in self.items:
            item['cooldown'] -= 1/FPS
            if item['cooldown'] < 0:
                item['cooldown'] = 0

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))
        for item in self.items:
            surface.blit(item['sprite'], (item['x'], item['y']))
            surface.blit(font.render(f"Cost: {item['cost']}", False, (255, 200, 20)), (item['x'], item['y'] + SCALE))
            if item['cooldown'] > 0:
                overlay = pg.Surface((SCALE, SCALE))
                overlay.set_alpha(100)
                overlay.fill((255, 0, 0))
                surface.blit(overlay, (item['x'], item['y']))
            if self.selected == item['id']:
                surface.blit(self.selected_sprite, (item['x'], item['y']))
        surface.blit(font.render(f'Sun: {sun_count}', False, (255, 200, 20)), (0, 9 * SCALE))


run = True
tiles = []
plants = []
font = pg.font.SysFont('Comic Sans MS', 16)
sun_count = 0
suns = []
selected_plant = None
chosen_plants = ['plants:repeater', 'plants:sunflower']
bottom_bar = BottomBar(chosen_plants)
zombies = [[], [], [], [], [], [], []]


def tick(frame_number):
    if random.randint(0, 500) == 1:
        suns.append(Sun(random.randint(0, 10 * SCALE), random.randint(SCALE, 8 * SCALE)))
    for sun in suns:
        sun.tick(frame_number)
    for plant in plants:
        plant.tick(frame_number)
    bottom_bar.tick(frame_number)


def draw_screen(surface, frame_number):
    surface.fill((0, 0, 0))

    for tile in tiles:
        tile.draw(surface)
    for plant in plants:
        plant.draw(surface)
    for sun in suns:
        sun.draw(surface)

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

    if pg.mouse.get_pressed()[0]:
        if selected_plant is not None:
            for item in bottom_bar.items:
                if item['id'] == selected_plant and item['cooldown'] <= 0:
                    if sun_count >= get_data(selected_plant)['cost']:
                        for tile in tiles:
                            if not tile.occupied:
                                if pg.Rect(tile.x, tile.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                                    tile.occupied = True
                                    plants.append(Plant(selected_plant, tile, frame_num=frame))
                                    sun_count -= get_data(selected_plant)['cost']
                                    for item in bottom_bar.items:
                                        if item['id'] == selected_plant:
                                            item['cooldown'] = get_data(item['id'])['cooldown']

        for sun in suns:
            if pg.Rect(sun.x, sun.y, SCALE / 2, SCALE / 2).collidepoint(pg.mouse.get_pos()):
                sun_count += sun.value
                suns.remove(sun)

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                if selected_plant != item['id']:
                    selected_plant = item['id']
                    bottom_bar.selected = item['id']

    if pg.mouse.get_pressed()[2]:
        for plant in plants:
            if pg.Rect(plant.x, plant.y, SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                plant.tile.occupied = False
                plants.remove(plant)

        for item in bottom_bar.items:
            if pg.Rect(item['x'], item['y'], SCALE, SCALE).collidepoint(pg.mouse.get_pos()):
                if selected_plant == item['id']:
                    selected_plant = None
                    bottom_bar.selected = None

    frame += 1

    if frame > FPS * 60:
        frame = 1

    tick(frame)

    draw_screen(window, frame)
