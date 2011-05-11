from __future__ import print_function, absolute_import

import itertools
import math
import os
import time

import numpy
import pygame

import components
import controls
import events
import physics
from constants import *
from util import *


def create_viking(datadir, clock, keyboard, key_left, key_right, key_jump, key_punch):
    idle_right = load_frame(datadir, 'model')
    idle_left = flip_frame(idle_right)

    punch_frames_right = load_frame_sequence(datadir, 'punch', 3)
    punch_frames_left = map(flip_frame, punch_frames_right)
    punch_frames_right = [idle_right] + punch_frames_right
    punch_frames_left = [idle_left] + punch_frames_left
    punch_delays = [2, 8, 6, 8, 2]
    punch_frames_right = list(repeat_each(punch_frames_right, punch_delays))
    punch_frames_left = list(repeat_each(punch_frames_left, punch_delays))

    run_frames_right = load_frame_sequence(datadir, 'run', 6)
    run_frames_left = map(flip_frame, run_frames_right)
    run_delays = [5] * 6
    run_frames_right = list(repeat_each(run_frames_right, run_delays))
    run_frames_left = list(repeat_each(run_frames_left, run_delays))

    jump_frames_right = load_frame_sequence(datadir, 'jump', 4)
    jump_frames_left = map(flip_frame, jump_frames_right)
    jump_delays = [3, 15, 18, 20]
    jump_frames_right = list(repeat_each(jump_frames_right, jump_delays))
    jump_frames_left = list(repeat_each(jump_frames_left, jump_delays))

    player = components.entity('Player', clock, keyboard,
                               location=(100, 0),
                               motion=components.motion(),
                               hitbox_passive=idle_right['hbp'],
                               hitbox_active=idle_right['hba'],
                               graphics=components.graphics(idle_right['sprite'], idle_right['sp']))
    physics.regular_physics(player)
    player.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
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
    controls.jump_when_key_pressed(player, key_jump, (0, -G - 1.6), 12)
    return player

def create_sheep(datadir, clock):
    sheep_frame = load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    physics.regular_physics(sheep)
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
    drake.physics.add(physics.apply_friction(5), components.physics.GROUP_VELOCITY)
    return drake

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
    halfnegcheck = numpy.any(toplefts[numpy.newaxis, :, :] >= bottomrights[:, numpy.newaxis, :], axis=2)
    result = numpy.logical_not(numpy.logical_or(halfnegcheck, halfnegcheck.T))

    # Remove self collisions
    result[numpy.diag_indices_from(result)] = False
    return result

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

    negcheck = numpy.logical_or(numpy.any(toplefts_active >= bottomrights_passive, axis=2),
                                numpy.any(bottomrights_active <= toplefts_passive, axis=2))

    legible = numpy.all(numpy.greater([thing.hitbox_active.size for thing in things], 0), axis=1).reshape(-1, 1)

    result = numpy.logical_and(numpy.logical_not(negcheck), legible)

    # Remove self collisions
    result[numpy.diag_indices_from(result)] = False
    return result


def passive_walls_collisions(things, walls):
    '''
    Returns a NxM array where element at [i, j] says if
    thing i collides with wall j with respect to its passive hitbox.
    '''
    toplefts_things = numpy.array([thing.hitbox_passive.point for thing in things])
    bottomrights_things = toplefts_things + [thing.hitbox_passive.size for thing in things]
    locations_things = numpy.array([thing.location for thing in things])
    toplefts_things += locations_things
    bottomrights_things += locations_things
    toplefts_things = toplefts_things.reshape(-1, 1, 2)
    bottomrights_things = bottomrights_things.reshape(-1, 1, 2);

    toplefts_walls = numpy.array([wall.point for wall in walls])
    bottomrights_walls = toplefts_walls + [wall.size for wall in walls]
    toplefts_walls = toplefts_walls.reshape(1, -1, 2)
    bottomrights_walls = bottomrights_walls.reshape(1, -1, 2);

    not_colliding = numpy.logical_or(numpy.any(toplefts_things >= bottomrights_walls, axis=2),
                                     numpy.any(bottomrights_things <= toplefts_walls, axis=2))

    return numpy.logical_not(not_colliding)

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
    walls = [components.hitbox((-5, -5), (5, 610)),
             components.hitbox((1000, -5), (5, 610)),
             components.hitbox((-5, 600), (1010, 5)),]

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
        pwcollisions = passive_walls_collisions(entities, walls);
        move = numpy.zeros((len(entities), 2))
        dv = numpy.zeros((len(entities), 2))
        for (thing1, thing2), (i1, i2) in zip(itertools.product(entities, entities),
                                              itertools.product(range(len(entities)), range(len(entities)))):
            if i1 >= i2:
                continue
            if ppcollisions[i1, i2]:
                # x0, y0 -----+
                #    |        | <- passive hitbox of thing 1
                #    |        |
                #    +-----x1, y1
                #
                # => [[x0, x1],
                #     [y0, y1]]
                rect1 = (thing1.hitbox_passive.point + thing1.location).reshape(-1, 1).repeat(2, 1)
                rect1[:,1] += thing1.hitbox_passive.size

                # x0, y0 -----+
                #    |        | <- passive hitbox of thing 2
                #    |        |
                #    +-----x1, y1
                #
                # => [[x1, x0],
                #     [y1, y0]]
                #
                # note: reversed wrt the above.
                rect2 = (thing2.hitbox_passive.point + thing2.location).reshape(-1, 1).repeat(2, 1)
                rect2[:,0] += thing2.hitbox_passive.size

                # diff[0, 0] - how much to move the two hitboxes vertically
                #              such that box1 is above box2.
                # diff[0, 1] - how much to move the two hitboxes vertically
                #              such that box2 is above box1.
                # and so on for diff[1, *] - (1 2, then 2 1)
                diff = rect2 - rect1

                # And the movement is the shortest alternative
                side = numpy.argmin(numpy.abs(diff.flat))
                diff = diff.flat[side] * 0.5
                side = side // 2

                move[i1, side] += diff
                move[i2, side] -= diff

                # Perfect elastic collision when both particles have mass = 1
                v1, v2 = thing1.motion.v, thing2.motion.v
                v1[side], v2[side] = v2[side], v1[side]

        for thing, wallcollisions, i in zip (entities, pwcollisions, xrange(len(entities))):
            if wallcollisions[0]:
                move[i, 0] -= thing.location[0] + thing.hitbox_passive.point[0]
                thing.motion.v[0] = 0

            if wallcollisions[1]:
                move[i, 0] -= thing.location[0] + thing.hitbox_passive.point[0] + thing.hitbox_passive.size[0] - 1000
                thing.motion.v[0] = 0

            if wallcollisions[2]:
                thing.tags.add('grounded')
                move[i, 1] -= thing.location[1] + thing.hitbox_passive.point[1] + thing.hitbox_passive.size[1] - 600
                thing.motion.v[1] = 0
            else:
                thing.tags.discard('grounded')

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


