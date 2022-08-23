import random

import pygame
from pytmx import load_pygame

import settings
from support import import_folder_dict, import_folder


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = settings.LAYERS['soil']


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = settings.LAYERS['soil water']


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        # setup
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered
        self.harvestable = None
        self.hitbox = None

        #  plant growing
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = settings.GROW_SPEED[plant_type]

        # sprite setup
        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = settings.LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = settings.LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(
                midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset)
            )


class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):
        self.raining = None
        self.hit_rects = None
        self.grid = None

        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfs = import_folder_dict('../graphics/soil')
        self.water_surfs = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

        # sounds
        self.hoe_sound = pygame.mixer.Sound('../audio/hoe.wav')
        self.hoe_sound.set_volume(0.2)

        self.plant_sound = pygame.mixer.Sound('../audio/plant.wav')
        self.plant_sound.set_volume(0.1)

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        v_tiles, h_tiles = ground.get_width() // settings.TILE_SIZE, ground.get_height() // settings.TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * settings.TILE_SIZE
                    y = index_row * settings.TILE_SIZE
                    rect = pygame.Rect(x, y, settings.TILE_SIZE, settings.TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()
                x = rect.x // settings.TILE_SIZE
                y = rect.y // settings.TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water(point)

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                # add 'W' entry to the soil grid
                x = soil_sprite.rect.x // settings.TILE_SIZE
                y = soil_sprite.rect.y // settings.TILE_SIZE
                self.grid[y][x].append('W')

                # create a water sprite
                random_water_surf = random.choice(self.water_surfs)
                WaterTile(soil_sprite.rect.topleft, random_water_surf, [self.all_sprites, self.water_sprites])

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * settings.TILE_SIZE
                    y = index_row * settings.TILE_SIZE
                    random_water_surf = random.choice(self.water_surfs)
                    WaterTile((x, y), random_water_surf, [self.all_sprites, self.water_sprites])

    def remove_water(self):
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // settings.TILE_SIZE
        y = pos[1] // settings.TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):

                x = soil_sprite.rect.x // settings.TILE_SIZE
                y = soil_sprite.rect.y // settings.TILE_SIZE

                if 'P' not in self.grid[y][x]:
                    self.plant_sound.play()
                    self.grid[y][x].append('P')
                    Plant(
                        plant_type=seed,
                        groups=[self.all_sprites, self.plant_sprites, self.collision_sprites],
                        soil=soil_sprite,
                        check_watered=self.check_watered
                    )

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:

                    # tile options
                    top = 'X' in self.grid[index_row - 1][index_col]
                    bottom = 'X' in self.grid[index_row + 1][index_col]
                    left = 'X' in row[index_col - 1]
                    right = 'X' in row[index_col + 1]

                    tile_type = 'o'

                    # all sides
                    if all((top, bottom, left, right)):
                        tile_type = 'x'

                    # horizontal tiles only
                    if left and not any((top, right, bottom)):
                        tile_type = 'r'
                    if right and not any((top, left, bottom)):
                        tile_type = 'l'
                    if right and left and not any((top, bottom)):
                        tile_type = 'lr'

                    # vertical only
                    if top and not any((right, left, bottom)):
                        tile_type = 'b'
                    if bottom and not any((right, left, top)):
                        tile_type = 't'
                    if bottom and top and not any((right, left)):
                        tile_type = 'tb'

                    # corners
                    if left and bottom and not any((top, right)):
                        tile_type = 'tr'
                    if left and top and not any((bottom, right)):
                        tile_type = 'br'
                    if right and bottom and not any((top, left)):
                        tile_type = 'tl'
                    if right and top and not any((bottom, left)):
                        tile_type = 'bl'

                    # T shapes
                    if all((top, bottom, right)) and not left:
                        tile_type = 'tbr'
                    if all((top, bottom, left)) and not right:
                        tile_type = 'tbl'
                    if all((left, right, bottom)) and not top:
                        tile_type = 'lrt'
                    if all((left, right, top)) and not bottom:
                        tile_type = 'lrb'

                    # FIXME: add more logic to fix not ideal tiling

                    SoilTile(
                        pos=(index_col * settings.TILE_SIZE, index_row * settings.TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites]
                    )
