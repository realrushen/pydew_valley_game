# coding=utf-8
import itertools

import pygame

from exceptions import UnsupportedDirectionException
from settings import *
from support import import_folder
from timer import Timer


class PlayerStatus:
    def __init__(self, direction, action=None):
        self._direction = direction
        self.action = action

    def get(self):
        if self.action:
            return f'{self.direction}_{self.action}'
        else:
            return self._direction

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if value in ['left', 'right', 'up', 'down']:
            self._direction = value
        else:
            raise UnsupportedDirectionException()


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer, toggle_shop):
        super().__init__(group)

        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
                           'right_hoe': [], 'left_hoe': [], 'up_hoe': [], 'down_hoe': [],
                           'right_axe': [], 'left_axe': [], 'up_axe': [], 'down_axe': [],
                           'right_water': [], 'left_water': [], 'up_water': [], 'down_water': []}

        self.import_assets()

        self.status = PlayerStatus(direction='down', action='idle')
        self.frame_index = 0

        # general setup
        self.image = self.animations[self.status.get()][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200

        # collision
        self.collision_sprites = collision_sprites
        self.hitbox = self.rect.copy().inflate(-126, -70)

        # timers
        self.timers = {
            'tool use': Timer(350, self.use_tool),
            'tool switch': Timer(200),
            'seed switch': Timer(200),
            'seed use': Timer(350, self.use_seed)
        }

        # tools
        self.tools = ['hoe', 'axe', 'water']
        self.tools_cycle = itertools.cycle(self.tools)
        self.selected_tool = next(self.tools_cycle)

        # seeds
        self.seeds = ['corn', 'tomato']
        self.seeds_cycle = itertools.cycle(self.seeds)
        self.selected_seed = next(self.seeds_cycle)

        # inventory
        self.item_inventory = {
            'wood': 20,
            'apple': 20,
            'corn': 20,
            'tomato': 20
        }
        self.seed_inventory = {
            'corn': 5,
            'tomato': 5
        }
        self.money = 200

        # interaction
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop

        # sound
        self.watering_sound = pygame.mixer.Sound('../audio/water.mp3')
        self.watering_sound.set_volume(0.1)

    def use_tool(self):
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()
        if self.selected_tool == 'water':
            self.watering_sound.play()
            self.soil_layer.water(self.target_pos)

    @property
    def target_pos(self):
        return self.rect.center + PLAYER_TOOL_OFFSET[self.status.direction]

    def use_seed(self):
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1

    def import_assets(self):

        for animation in self.animations.keys():
            full_path = f'../graphics/character/{animation}'
            self.animations[animation] = import_folder(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status.get()]):
            self.frame_index = 0
        self.image = self.animations[self.status.get()][int(self.frame_index)]

    def input(self):
        keys = pygame.key.get_pressed()

        if not self.timers['tool use'].active and not self.sleep:
            # directions
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = PlayerStatus(direction='up')
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = PlayerStatus(direction='down')
            else:
                self.direction.y = 0

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = PlayerStatus(direction='left')
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = PlayerStatus(direction='right')
            else:
                self.direction.x = 0

            # tool use
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

            # change tool
            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.selected_tool = next(self.tools_cycle)

            # seed use
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

            # change seed
            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.selected_seed = next(self.seeds_cycle)

            if keys[pygame.K_RETURN]:
                collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, dokill=False)
                if collided_interaction_sprite:
                    if collided_interaction_sprite[0].name == 'Trader':
                        self.toggle_shop()
                    else:
                        self.status = PlayerStatus(direction='left', action='idle')
                        self.sleep = True

    def get_action(self):
        # idle
        if self.direction.magnitude() == 0:
            self.status.action = 'idle'

        # tool use
        if self.timers['tool use'].active:
            self.status.action = self.selected_tool

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox') and sprite.hitbox is not None and sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # moving right
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:  # moving left
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                    self.pos.x = self.hitbox.centerx
                if direction == 'vertical':
                    if self.direction.y > 0:  # moving down
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0:  # moving up
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery
                    self.pos.y = self.hitbox.centery

    def move(self, dt):
        # normalizing direction vector to prevent faster diagonal movement
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.centerx = self.hitbox.centerx = round(self.pos.x)
        self.collision('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.rect.centery = self.hitbox.centery = round(self.pos.y)
        self.collision('vertical')

    def update(self, dt):
        self.input()
        self.get_action()
        self.update_timers()
        self.move(dt)
        self.animate(dt)
