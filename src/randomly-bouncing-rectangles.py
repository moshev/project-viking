# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import time
import numpy
import pygame

import collisions
import components
import constants
import events


WIDTH = 800
HEIGHT = 600


def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    tick_event = pygame.event.Event(constants.TICK)

    # create room
    walls = [components.hitbox((0, 0), (WIDTH, 5)),
             components.hitbox((0, HEIGHT - 5), (WIDTH, 5)),
             components.hitbox((0, 0), (5, HEIGHT)),
             components.hitbox((WIDTH - 5, 0), (5, HEIGHT)),]

    # create some random rects
    rects = []

    pause = False
    do_frame = False
    while True:
        start = time.clock()

        key_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                key_events.append(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    pause = not pause
                elif event.key == pygame.K_PERIOD and pause:
                    do_frame = True

        if (not pause) or do_frame:
            for event in key_events:
                keyboard.dispatch(event)

            clock.dispatch(tick_event)

            do_frame = False

        screen.fill((0, 0, 0))
        for wall in walls:
            screen.fill((77, 80, 223), pygame.Rect(wall.point, wall.size))

        for thing in rects:
            screen.fill((227, 227, 227), pygame.Rect(thing.location + thing.hitbox_passive.point, thing.hitbox_passive.size))

        pygame.display.flip()

        delta = time.clock() - start
        if delta < constants.FRAME:
            time.sleep(constants.FRAME - delta)


if __name__ == '__main__':
    main()

