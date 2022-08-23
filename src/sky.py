import enum
import itertools
import random

import pygame

import settings

from sprites import Generic
from support import import_folder


class Daytime(enum.Enum):
    DAY = enum.auto()
    NIGHT = enum.auto()


class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.start_color = [255, 255, 255]
        self.current_color = [255, 255, 255]
        self.end_color = [38, 101, 189]
        self.day_transition_speed = settings.DAYTIME_TRANSITION_SPEED
        self.day_time_states = itertools.cycle([Daytime.DAY, Daytime.NIGHT])
        self.current_day_time_state = next(self.day_time_states)  # starts from 'day'

    def display(self, dt):
        for color_index, value in enumerate(self.current_color):
            if self.current_day_time_state == Daytime.DAY and value > self.end_color[color_index]:
                self.current_color[color_index] -= self.day_transition_speed * dt
            elif self.current_day_time_state == Daytime.NIGHT and value < self.start_color[color_index]:
                self.current_color[color_index] += self.day_transition_speed * dt

        is_day_end = self.current_color > self.end_color
        is_night_end = self.current_color < self.start_color

        if is_day_end:
            self.current_day_time_state = next(self.day_time_states)
        if is_night_end:
            self.current_day_time_state = next(self.day_time_states)

        self.full_surf.fill(self.current_color)
        self.display_surface.blit(self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


class Drop(Generic):
    def __init__(self, surf, pos, moving, groups, z):

        # general setup
        super().__init__(pos, surf, groups, z)
        self.lifetime = random.randint(400, 500)
        self.start_time = pygame.time.get_ticks()

        # moving
        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2, 4)
            self.speed = random.randint(200, 250)

    def update(self, dt):
        # movement
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # timer
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time >= self.lifetime:
            self.kill()


class Rain:
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        self.rain_drops = import_folder('../graphics/rain/drops')
        self.rain_floor = import_folder('../graphics/rain/floor')
        self.floor_w, self.floor_h = pygame.image.load('../graphics/world/ground.png').get_size()

    def create_floor(self):
        Drop(
            surf=random.choice(self.rain_floor),
            pos=(random.randint(0, self.floor_w), random.randint(0, self.floor_h)),
            moving=False,
            groups=self.all_sprites,
            z=settings.LAYERS['rain floor']
        )

    def create_drops(self):
        Drop(
            surf=random.choice(self.rain_drops),
            pos=(random.randint(0, self.floor_w), random.randint(0, self.floor_h)),
            moving=True,
            groups=self.all_sprites,
            z=settings.LAYERS['rain drops']
        )

    def update(self):
        self.create_floor()
        self.create_drops()
