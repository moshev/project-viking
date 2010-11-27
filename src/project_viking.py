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
import itertools
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

def create_viking(datadir, clock, keyboard, key_left, key_right, key_jump, key_punch):
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

    walk_right_state = controls.loop_while_keydown(player, run_frames_right, (10, 0), key_right, idle_right_state)
    walk_left_state = controls.loop_while_keydown(player, run_frames_left, (-10, 0), key_left, idle_left_state)

    jump_right_state = controls.animation_while_keydown(player, jump_frames_right, key_jump, idle_right_state)
    jump_left_state = controls.animation_while_keydown(player, jump_frames_left, key_jump, idle_left_state)

    jump_right_walk_state = controls.animation_while_keydown(player, jump_frames_right, key_jump, walk_right_state)
    jump_left_walk_state = controls.animation_while_keydown(player, jump_frames_left, key_jump, walk_left_state)

    punch_right_state = controls.animation(player, punch_frames_right, idle_right_state)
    punch_left_state = controls.animation(player, punch_frames_left, idle_left_state)

    idle_right_state.transitions[key_left] = walk_left_state
    idle_right_state.transitions[key_right] = walk_right_state
    idle_right_state.transitions[key_punch] = punch_right_state
    idle_right_state.transitions[key_jump] = jump_right_state

    idle_left_state.transitions[key_left] = walk_left_state
    idle_left_state.transitions[key_right] = walk_right_state
    idle_left_state.transitions[key_punch] = punch_left_state
    idle_left_state.transitions[key_jump] = jump_left_state

    walk_right_state.transitions[key_left] = walk_left_state
    walk_right_state.transitions[key_punch] = punch_right_state
    walk_right_state.transitions[key_jump] = jump_right_walk_state

    walk_left_state.transitions[key_right] = walk_right_state
    walk_left_state.transitions[key_punch] = punch_left_state
    walk_left_state.transitions[key_jump] = jump_left_walk_state

    idle_right_state.start()
    # jumping
    controls.jump_when_key_pressed(player, key_jump, (0, -3.0), 12)
    return player

def create_sheep(datadir, clock):
    sheep_frame = load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=20)
    sheep.set_frame(sheep_frame)
    physics.regular_physics(sheep)
    sheep.physics.add(physics.ground_limiter(550), components.physics.GROUP_LOCATION)
    sheep.physics.add(wall, components.physics.GROUP_LOCATION)
    sheep.physics.add(physics.apply_friction(0.2), components.physics.GROUP_VELOCITY)
    return sheep

def collision_check(l1, s1, l2, s2):
    r1, r2 = (l1 + s1), (l2 + s2)
    return not ( l2[0] > r1[0] or r2[0] < l1[0] or l2[1] > r1[1] or r2[1] < l1[1])

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)
    datadir = find_datadir()

    player1 = create_viking(datadir, clock, keyboard, K_LEFT, K_RIGHT, K_UP, K_RETURN)
    player2 = create_viking(datadir, clock, keyboard, K_a, K_d, K_w, K_j)
    player2.location[0] = 900

    entities = [player1, player2]
    scream = pygame.mixer.Sound(os.path.join(datadir, 'wilhelm.wav'))

    debug_draw = False
    while True:
        start = time.clock()

        clock.dispatch(tick_event)

        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)
            if event.type == KEYDOWN:
                if event.key == K_F2:
                    debug_draw = not debug_draw
                elif event.key == K_F3:
                    entities.append(create_sheep(datadir, clock))

        for thing1, thing2 in itertools.product(entities, entities):
            if thing1 is thing2:
                continue
            if any(thing1.hitbox_active.size <= 0):
                continue
            if collision_check(thing1.hitbox_active.point + thing1.location, thing1.hitbox_active.size,
                            thing2.hitbox_passive.point + thing2.location, thing2.hitbox_passive.size):
                thing2.hitpoints -= 1

        for thing1, thing2 in itertools.product(entities, entities):
            if thing1 is thing2:
                continue
            p1 = thing1.hitbox_passive.point + thing1.location
            p2 = thing2.hitbox_passive.point + thing2.location
            if collision_check(p1, thing1.hitbox_passive.size, p2, thing2.hitbox_passive.size):
                if thing1.location[0] < thing2.location[0]:
                    diff = (p2[0] - p1[0] - thing1.hitbox_passive.size[0]) / 2
                else:
                    diff = -(p1[0] - p2[0] - thing2.hitbox_passive.size[0]) / 2
                thing1.location[0] += diff
                thing2.location[0] -= diff

        dead = []
        screen.fill((20, 20, 20))
        for thing in entities:
            if thing.hitpoints <= 0:
                dead.append(thing)
                continue
            screen.blit(thing.graphics.sprite, map(math.trunc, thing.location + thing.graphics.anchor))
            if debug_draw:
                screen.fill((227, 227, 227), pygame.Rect(thing.location + thing.hitbox_passive.point, thing.hitbox_passive.size))
                screen.fill((255, 100, 100), pygame.Rect(thing.location + thing.hitbox_active.point, thing.hitbox_active.size))
                screen.fill((100, 255, 255), pygame.Rect(thing.location[0] - 3, thing.location[1] - 3, 6, 6))
                screen.fill((100, 100, 255), pygame.Rect(thing.location, (1, 1)))

        for thing in dead:
            scream.play()
            if thing.name != 'Sheep':
                thing.hitpoints = 100
                thing.location[:] = (500, -10)
                if thing.physics is not None:
                    thing.physics.last_position[:] = thing.location
            else:
                entities.remove(thing)

        screen.fill((120, 50, 50), pygame.Rect(0, 0, player1.hitpoints * 2, 10))
        screen.fill((120, 50, 50), pygame.Rect(1000 - player2.hitpoints * 2, 0, player2.hitpoints * 2, 10))

        pygame.display.flip()

        print("Player1 has %d hitpoints left!" % player1.hitpoints)
        print("Player2 has %d hitpoints left!" % player2.hitpoints)

        delta = time.clock() - start
        if delta < FRAME:
            time.sleep(FRAME - delta)

if __name__ == '__main__':
    main()


