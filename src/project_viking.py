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
    jump_delays = [3, 15, 18, 20]
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
    player.physics.add(physics.apply_friction(3), components.physics.GROUP_VELOCITY)
    player.physics.add(physics.speed_limiter((10, 10000)), components.physics.GROUP_VELOCITY)

    # movement left/right
    idle_right_state = controls.looped_animation(player, [idle_right], (0, 0))
    idle_left_state = controls.looped_animation(player, [idle_left], (0, 0))

    walk_right_state = controls.loop_while_keydown(player, run_frames_right, (5, 0), key_right, idle_right_state)
    walk_left_state = controls.loop_while_keydown(player, run_frames_left, (-5, 0), key_left, idle_left_state)

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
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    physics.regular_physics(sheep)
    sheep.physics.add(physics.ground_limiter(550), components.physics.GROUP_LOCATION)
    sheep.physics.add(wall, components.physics.GROUP_LOCATION)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep

def create_floaty_sheep(datadir, clock):
    sheep_frame = load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 400),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    components.physics(sheep)
    sheep.physics.add(physics.ground_limiter(550), components.physics.GROUP_LOCATION)
    sheep.physics.add(wall, components.physics.GROUP_LOCATION)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep

def create_drake(datadir, clock):
    drake_frame = load_frame(datadir, 'drake')
    drake = components.entity('Drake', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=200)
    drake.set_frame(drake_frame)
    physics.regular_physics(drake)
    drake.physics.add(physics.ground_limiter(550), components.physics.GROUP_LOCATION)
    drake.physics.add(wall, components.physics.GROUP_LOCATION)
    drake.physics.add(physics.apply_friction(5), components.physics.GROUP_VELOCITY)
    return drake

def collision_check(l1, s1, l2, s2):
    r1, r2 = (l1 + s1), (l2 + s2)
    return not ( l2[0] > r1[0] or r2[0] < l1[0] or l2[1] > r1[1] or r2[1] < l1[1])

def smooth_clamp_to(v, s):
    if v[0] == 0:
        return numpy.array((0.0, math.copysign(s[1], v[1])))
    elif v[1] == 0:
        return numpy.array((math.copysign(s[0], v[0]), 0.0))
    d = numpy.abs(s / v)
    if d[0] < d[1] and not (math.isnan(d[0]) or math.isinf(d[0])):
        return v * d[0]
    elif not (math.isnan(d[1]) or math.isinf(d[1])):
        return v * d[1]
    else:
        return v

def passive_passive_collisions(things):
    '''
    Returns a NxN array where element at [i, j] says if
    thing i collides with thing j with respect to their passive hitboxes.

    To see if two boxes do NOT collide, the check is if
    my left side is past the other's right side or
    my top side is past the other's bottom side

    This is done by creating one array of top-left pairs and one of bottom-right pairs.
    Then every element of top-left is compared to every element of bottom-right and
    the result is an NxN matrix of boolean pairs.

    The pairs are reduced to a single boolean by applying the or operation.
    Then the result at [i,j] is combined with the result at [j,i], giving the final
    result for each cell.

    That is negated to obtain whether two boxes cross each other.
    '''
    toplefts = numpy.array([thing.hitbox_passive.point for thing in things])
    bottomrights = toplefts + [thing.hitbox_passive.size for thing in things]
    locations = numpy.array([thing.location for thing in things])
    toplefts += locations
    bottomrights += locations
    halfnegcheck = numpy.any(toplefts[numpy.newaxis,:,:] > bottomrights[:,numpy.newaxis,:], axis=2)
    return numpy.logical_not(numpy.logical_or(halfnegcheck, halfnegcheck.T))

def active_passive_collisions(things):
    '''
    Returns an NxN array, where element at [i, j] says if
    thing i's active hitbox crosses thing j's active hitbox.
    An active hitbox isn't considered if any of its dimensions is not-positive.

    See comment for passive_passive_collisions for longer explanation.
    The main difference is that we can't cheat here and do half the checks,
    then transpose, we need to do all checks.
    '''
    locations = numpy.array([thing.location for thing in things])

    toplefts_passive = numpy.array([thing.hitbox_passive.point for thing in things])
    bottomrights_passive = toplefts_passive + [thing.hitbox_passive.size for thing in things]
    toplefts_passive += locations
    bottomrights_passive += locations
    toplefts_passive = toplefts_passive.reshape(1, -1, 2)
    bottomrights_passive = bottomrights_passive.reshape(1, -1, 2)

    toplefts_active = numpy.array([thing.hitbox_active.point for thing in things])
    bottomrights_active = toplefts_active + [thing.hitbox_active.size for thing in things]
    toplefts_active += locations
    bottomrights_active += locations
    toplefts_active = toplefts_active.reshape(-1, 1, 2)
    bottomrights_active = bottomrights_active.reshape(-1, 1, 2)

    negcheck = numpy.logical_or(numpy.any(toplefts_active > bottomrights_passive, axis=2),
                                numpy.any(bottomrights_active < toplefts_passive, axis=2))

    legible = numpy.all(numpy.greater([thing.hitbox_active.size for thing in things], 0), axis=1).reshape(-1, 1)

    return numpy.logical_and(numpy.logical_not(negcheck), legible)

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)
    datadir = find_datadir()

    player1 = create_viking(datadir, clock, keyboard, K_a, K_d, K_w, K_j)
    player2 = create_viking(datadir, clock, keyboard, K_LEFT, K_RIGHT, K_UP, K_RETURN)
    player2.location[0] = 900

    entities = [player1, player2]
    scream = pygame.mixer.Sound(os.path.join(datadir, 'wilhelm.wav'))
    background = pygame.image.load(os.path.join(datadir, 'background.png')).convert()

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
                elif event.key == K_F4:
                    entities.append(create_drake(datadir, clock))
                elif event.key == K_F5:
                    entities.append(create_floaty_sheep(datadir, clock))

        apcollisions = active_passive_collisions(entities)
        for i1, i2 in itertools.product(range(len(entities)), range(len(entities))):
            if i1 == i2:
                continue
            if apcollisions[i1, i2]:
                entities[i2].hitpoints -= 1

        ppcollisions = passive_passive_collisions(entities)
        move = numpy.zeros((len(entities), 2))
        for (thing1, thing2), (i1, i2) in zip(itertools.product(entities, entities),
                                              itertools.product(range(len(entities)), range(len(entities)))):
            if i1 >= i2:
                continue
            if ppcollisions[i1, i2]:
                p1 = thing1.hitbox_passive.point + thing1.location
                p2 = thing2.hitbox_passive.point + thing2.location
                s1 = thing1.hitbox_passive.size / 2
                s2 = thing2.hitbox_passive.size / 2
                c1 = p1 + s1
                c2 = p2 + s2
                d = c2 - c1
                d1 = smooth_clamp_to(d, s1)
                d2 = smooth_clamp_to(d, s2)
                k = (d1 + d2 - d) / 2
                move[i1] -= k
                move[i2] += k

        for thing, vector in zip(entities, move):
            thing.location += vector

        dead = []
        screen.blit(background, (0, 0))
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
            if thing.name == 'Player':
                thing.hitpoints = 100
                thing.location[:] = (500, -10)
                if thing.physics is not None:
                    thing.physics.last_position[:] = thing.location
            else:
                entities.remove(thing)

        screen.fill((120, 50, 50), pygame.Rect(0, 10, player1.hitpoints * 2, 10))
        screen.fill((120, 50, 50), pygame.Rect(1000 - player2.hitpoints * 2, 10, player2.hitpoints * 2, 10))

        pygame.display.flip()

        delta = time.clock() - start
        if delta < FRAME:
            time.sleep(FRAME - delta)

if __name__ == '__main__':
    main()


