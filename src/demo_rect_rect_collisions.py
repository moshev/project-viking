# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import pygame
import time
from pygame.constants import *
from components import hitbox
from collisions import complete_collision

def hb2r(box):
    return pygame.Rect(box.point, box.size)

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))

    white_box = hitbox((400, 200), (200, 200))
    blue_box = hitbox((0, 0), (50, 50))
    red_box = hitbox((0, 0), (50, 50))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return 0

        blue_box.point[:] = pygame.mouse.get_pos()
        blue_box.point -= (25, 25)
        side, diff = complete_collision(blue_box, white_box)
        red_box.point[:] = blue_box.point
        red_box.point[side // 2] += diff

        screen.fill((0, 0, 0))
        screen.fill((227, 227, 227), hb2r(white_box))
        screen.fill((120, 120, 255), hb2r(blue_box))
        screen.fill((255, 180, 50), hb2r(red_box))
        pygame.display.flip()

        time.sleep(0.01)

if __name__ == '__main__':
    main()

