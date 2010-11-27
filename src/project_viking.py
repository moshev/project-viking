from __future__ import print_function, absolute_import
import time
import numpy
import pygame
from pygame.locals import *
import events
import components
import controls
from constants import *
from collections import defaultdict
from util import arrayify, find_datadir
FRAME = 0.02
# g = 980 cm/s**2;
G = 4000.0 * (FRAME**2)

def ground_limiter(ground_level):
    '''
    Returns a function, that moves an entity's location, making its lower edge stay above the given horizontal line.
    '''
    def limiter(entity):
        if entity.location.point[1] + entity.location.size[1] >= ground_level:
            entity.tags.add('grounded')
            entity.location.point[1] = ground_level - entity.location.size[1]
        elif entity.location.point[1] + entity.location.size[1] < ground_level:
            if 'grounded' in entity.tags:
                entity.tags.remove('grounded')

    return limiter

def regular_physics(entity):
    '''
    Returns a physics object with added velocity and location calculators and affected by gravity.
    '''
    p = components.physics(entity)
    p.add(components.velocity_calculator, components.physics.GROUP_ACCELERATION + 1)
    p.add(components.location_calculator, components.physics.GROUP_VELOCITY + 1)
    p.add(gravity, components.physics.GROUP_ACCELERATION)
    return p

def gravity(entity):
    entity.motion.a[1] += G

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)

    player = components.entity('Player', clock, keyboard,
                               location=components.location((0, 0), (50, 100)),
                               motion=components.motion(),
                               graphics=components.graphics(None))
    regular_physics(player)
    player.physics.add(ground_limiter(400), components.physics.GROUP_LOCATION)
    # movement left/right
    controls.move_while_key_pressed(player, K_RIGHT, (0.5, 0), 50)
    controls.move_while_key_pressed(player, K_LEFT, (-0.5, 0), 50)
    # jumping
    controls.jump_when_key_pressed(player, K_UP, (0, -3.0), 10)

    while True:
        start = time.clock()

        clock.dispatch(tick_event)

        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)

        screen.fill((0, 0, 0))
        screen.fill((200, 200, 150), pygame.Rect(player.location.point, player.location.size))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < FRAME:
            time.sleep(FRAME - delta)

if __name__ == '__main__':
    main()


