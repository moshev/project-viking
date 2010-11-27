from __future__ import print_function, absolute_import
import time
import os
import numpy
import math
import pygame
from pygame.locals import *
import events
import components
import controls
from constants import *
from collections import defaultdict
from util import *
FRAME = 0.02
# g = 980 cm/s**2;
G = 4000.0 * (FRAME**2)

def ground_limiter(ground_level):
    '''
    Returns a function, that moves an entity's location, making its lower edge stay above the given horizontal line.
    '''
    def limiter(entity):
        dist = ground_level - (entity.location[1])# + entity.hitbox_passive.point[1] + entity.hitbox_passive.size[1])
        if dist <= 0:
            entity.tags.add('grounded')
            entity.location[1] += dist
        elif dist > 0:
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

def iterate_with_delays(frames, delays):
    '''
    Frames is a list of tuples (image, 
    frame_times is a list of numbers - how many ticks to wait before returning the given frame.
    '''
    tick = 0
    frame = 0
    while frame < len(frames):
        yield frames[frame]
        tick += 1
        if tick >= delays[frame]:
            tick = 0
            frame += 1

class animation(object):
    '''
    Activates an animation when key is pressed.
    '''
    def __init__(self, entity, frames):
        '''
        frames is an iterable from which the frames are taken.
        '''
        self.entity = entity
        self.entity.clock.add(self.on_tick)
        self.frames = frames
        self.run = True

    def on_tick(self, event):
        if not self.run:
            return None
        try:
            frame = next(self.frames)
            self.entity.graphics.sprite = frame['sprite']
            self.entity.graphics.anchor = frame['sp']
            self.entity.hitbox_passive = frame['hbp']
            self.entity.hitbox_active = frame['hba']
            return self.on_tick
        except StopIteration:
            return None

class animate_on_key(object):
    '''
    Creates an animation when key is pressed.
    '''
    def __init__(self, entity, key, frames_func):
        '''
        frames_func is called to return the frames parameter for the animation class's constructor.
        '''
        self.entity = entity
        self.key = key
        self.func = frames_func
        self.entity.keyboard.add(self.on_key)

    def on_key(self, event):
        if event.type == KEYDOWN and event.key == self.key:
            animation(self.entity, self.func())
        return self.on_key

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)
    datadir = find_datadir()
    idle_pose = load_frame(datadir, 'model')
    idle_flipped = flip_frame(idle_pose)
    punch_frames = load_frame_sequence(datadir, 'punch', 3)
    punch_frames.append(idle_pose)
    punch_delays = [8, 6, 8, 2]

    player = components.entity('Player', clock, keyboard,
                               location=(0, 0),
                               motion=components.motion(),
                               hitbox_passive=idle_pose['hbp'],
                               hitbox_active=idle_pose['hba'],
                               graphics=components.graphics(idle_pose['sprite'], idle_pose['sp']))
    regular_physics(player)
    player.physics.add(ground_limiter(400), components.physics.GROUP_LOCATION)

    # movement left/right
    controls.move_while_key_pressed(player, K_RIGHT, (1, 0), 20)
    animate_on_key(player, K_RIGHT, lambda: iter([idle_pose]))
    controls.move_while_key_pressed(player, K_LEFT, (-1, 0), 20)
    animate_on_key(player, K_LEFT, lambda: iter([idle_flipped]))

    # jumping
    controls.jump_when_key_pressed(player, K_UP, (0, -3.0), 10)

    # Epic Punch
    animate_on_key(player, K_f, lambda: iterate_with_delays(punch_frames, punch_delays))

    debug_draw = False
    while True:
        start = time.clock()

        clock.dispatch(tick_event)

        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)
            if event.type == KEYDOWN and event.key == K_F2:
                debug_draw = not debug_draw

        screen.fill((20, 20, 20))
        screen.blit(player.graphics.sprite, map(math.trunc, player.location + player.graphics.anchor))
        if debug_draw:
            screen.fill((227, 227, 227), pygame.Rect(player.location + player.hitbox_passive.point, player.hitbox_passive.size))
            screen.fill((255, 100, 100), pygame.Rect(player.location + player.hitbox_active.point, player.hitbox_active.size))
            screen.fill((100, 255, 255), pygame.Rect(player.location[0] - 3, player.location[1] - 3, 6, 6))
            screen.fill((100, 100, 255), pygame.Rect(player.location, (1, 1)))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < FRAME:
            time.sleep(FRAME - delta)

if __name__ == '__main__':
    main()


