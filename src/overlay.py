import pygame

import settings
from settings import *


class Overlay:
    def __init__(self, player):
        # general setup
        self.show_inventory = False
        self.display_surface = pygame.display.get_surface()
        self.player = player

        # imports
        overlay_path = '../graphics/overlay/'
        self.tools_surf = {
            tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools
        }
        self.seeds_surf = {
            seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in player.seeds
        }

    def display(self):
        # tools
        tool_surf = self.tools_surf[self.player.selected_tool]
        tool_rect = tool_surf.get_rect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # seeds
        seed_surf = self.seeds_surf[self.player.selected_seed]
        seed_rect = seed_surf.get_rect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)

        # inventory
        if self.show_inventory:
            # inventory slots
            inventory_surf = pygame.image.load('../graphics/UI/inventory_slots.png').convert_alpha()
            inventory_surf = pygame.transform.scale(inventory_surf, (inventory_surf.get_width() // 3, inventory_surf.get_height() // 3))
            inventory_rect = inventory_surf.get_rect(bottomright=(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            self.display_surface.blit(inventory_surf, inventory_rect)

