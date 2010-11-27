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
import physics
from constants import *
from collections import defaultdict
from util import *

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

def wall(entity):
    if entity.location[0] < 10:
        entity.location[0] = 10
    elif entity.location[0] > 990:
        entity.location[0] = 990

def create_viking(datadir, clock, keyboard):
    idle_right = load_frame(datadir, 'model')
    idle_left = flip_frame(idle_right)

    punch_frames_right = load_frame_sequence(datadir, 'punch', 3)
    punch_frames_left = map(flip_frame, punch_frames_right)
    punch_frames_right = [idle_right] + punch_frames_right
    punch_frames_left = [idle_left] + punch_frames_left
    punch_delays = [2, 8, 6, 8, 2]
    punch_frames_right = list(iterate_with_delays(punch_frames_right, punch_delays))
    punch_frames_left = list(iterate_with_delays(punch_frames_left, punch_delays))

    run_frames_right = load_frame_sequence(datadir, 'run', 6)
    run_frames_left = map(flip_frame, run_frames_right) 
    run_delays = [5] * 6
    run_frames_right = list(iterate_with_delays(run_frames_right, run_delays))
    run_frames_left = list(iterate_with_delays(run_frames_left, run_delays))

    jump_frames_right = load_frame_sequence(datadir, 'jump', 4)
    jump_frames_left = map(flip_frame, jump_frames_right) 
    jump_delays = [2, 10, 15, 20]
    jump_frames_right = list(iterate_with_delays(jump_frames_right, jump_delays))
    jump_frames_left = list(iterate_with_delays(jump_frames_left, jump_delays))

    player = components.entity('Player', clock, keyboard,
                               location=(0, 0),
                               motion=components.motion(),
                               hitbox_passive=idle_right['hbp'],
                               hitbox_active=idle_right['hba'],
                               graphics=components.graphics(idle_right['sprite'], idle_right['sp']))
    physics.regular_physics(player)
    player.physics.add(physics.ground_limiter(550), components.physics.GROUP_LOCATION)
    player.physics.add(wall, components.physics.GROUP_LOCATION)
    player.physics.add(physics.apply_friction(1), components.physics.GROUP_VELOCITY)
    player.physics.add(physics.speed_limiter((10, 10000)), components.physics.GROUP_VELOCITY)

    # movement left/right
    idle_right_state = controls.looped_animation(player, [idle_right], (0, 0))
    idle_left_state = controls.looped_animation(player, [idle_left], (0, 0))

    walk_right_state = controls.loop_while_keydown(player, run_frames_right, (10, 0), K_RIGHT, idle_right_state)
    walk_left_state = controls.loop_while_keydown(player, run_frames_left, (-10, 0), K_LEFT, idle_left_state)

    jump_right_state = controls.animation_while_keydown(player, jump_frames_right, K_UP, idle_right_state)
    jump_left_state = controls.animation_while_keydown(player, jump_frames_left, K_UP, idle_left_state)

    jump_right_walk_state = controls.animation_while_keydown(player, jump_frames_right, K_UP, walk_right_state)
    jump_left_walk_state = controls.animation_while_keydown(player, jump_frames_left, K_UP, walk_left_state)

    punch_right_state = controls.animation(player, punch_frames_right, idle_right_state)
    punch_left_state = controls.animation(player, punch_frames_left, idle_left_state)

    idle_right_state.transitions[K_LEFT] = walk_left_state
    idle_right_state.transitions[K_RIGHT] = walk_right_state
    idle_right_state.transitions[K_f] = punch_right_state
    idle_right_state.transitions[K_UP] = jump_right_state

    idle_left_state.transitions[K_LEFT] = walk_left_state
    idle_left_state.transitions[K_RIGHT] = walk_right_state
    idle_left_state.transitions[K_f] = punch_left_state
    idle_left_state.transitions[K_UP] = jump_left_state

    walk_right_state.transitions[K_LEFT] = walk_left_state
    walk_right_state.transitions[K_f] = punch_right_state
    walk_right_state.transitions[K_UP] = jump_right_walk_state

    walk_left_state.transitions[K_RIGHT] = walk_right_state
    walk_left_state.transitions[K_f] = punch_left_state
    walk_left_state.transitions[K_UP] = jump_left_walk_state

    idle_right_state.start()
    # jumping
    controls.jump_when_key_pressed(player, K_UP, (0, -3.0), 10)
    return player

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)
    datadir = find_datadir()

    player = create_viking(datadir, clock, keyboard)

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


