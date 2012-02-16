# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement
import numpy
import itertools
import components
import random

MAX_DIFF = 5.0


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
    halfnegcheck = numpy.any(toplefts[numpy.newaxis, :, :] > bottomrights[:, numpy.newaxis, :], axis=2)
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

    negcheck = numpy.logical_or(numpy.any(toplefts_active > bottomrights_passive, axis=2),
                                numpy.any(bottomrights_active < toplefts_passive, axis=2))

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

    not_colliding = numpy.logical_or(numpy.any(toplefts_things > bottomrights_walls, axis=2),
                                     numpy.any(bottomrights_things < toplefts_walls, axis=2))

    return numpy.logical_not(not_colliding)


def complete_collision(box1, box2):
    '''Performs a complete collision between box1 and box2.
    Returns a tuple (which sides collide, motion vector with respect to box1)
    The first element is either
    0 - box2 left of box1, 1 - box1 left of box2
    2 - box2 over box1, 3 - box1 over box2

    The second is a single number - how much to move box1 in the given direction,
    so that it just touches box2.'''

    # x0, y0 -----+
    #    |        | <- passive hitbox of thing 1
    #    |        |
    #    +-----x1, y1
    #
    # => [[x0, x1],
    #     [y0, y1]]
    rect1 = box1.point.reshape(-1, 1).repeat(2, 1)
    rect1[:,1] += box1.size

    # x0, y0 -----+
    #    |        | <- passive hitbox of thing 2
    #    |        |
    #    +-----x1, y1
    #
    # => [[x1, x0],
    #     [y1, y0]]
    #
    # note: reversed wrt the above.
    rect2 = box2.point.reshape(-1, 1).repeat(2, 1)
    rect2[:,0] += box2.size

    # diff[0, 0] - how much to move the two hitboxes vertically
    #              such that box1 is above box2.
    # diff[0, 1] - how much to move the two hitboxes vertically
    #              such that box2 is above box1.
    # and so on for diff[1, *] - (1 2, then 2 1)
    diff = rect2 - rect1

    # And the movement is the shortest alternative
    side = numpy.argmin(numpy.abs(diff.flat))
    diff = diff.flat[side]

    return (side, diff)


def resolve_wall_collisions(entities, walls):
    '''Resolves all collisions between entities and walls.
    TODO: Add inelasticity coefficients and make entities bounce around.'''

    pwcollisions = passive_walls_collisions(entities, walls);
    hbp = components.hitbox((0, 0), (0, 0))

    move = numpy.zeros((len(entities), 2))
    contributors = numpy.zeros ((len(entities),), dtype=int)
    resolved = 0

    for thing, adjust, contribs, collisions in itertools.izip(entities, move, contributors, pwcollisions):
        for wall, collides in itertools.izip(walls, collisions):
            if collides:
                numpy.add(thing.hitbox_passive.point, thing.location, hbp.point)
                hbp.size[:] = thing.hitbox_passive.size

                side, diff = complete_collision(hbp, wall)

                # Set grounded flag when one is on top of the other
                if side == 3:
                    thing.tags.add('grounded')

                v = thing.motion_v[side // 2]
                if v == 0 or v * diff < 0 or (diff == 0 and (v > 0) == side % 2):
                    thing.motion_v[side // 2] = 0
                    adjust[side // 2] += diff
                    contribs += 1

                if diff != 0:
                    resolved += 1

    mask = contributors != 0
    move[mask] /= contributors.reshape((-1, 1))[mask]
    numpy.clip(move, -MAX_DIFF, MAX_DIFF, move)
    for thing, adjust in itertools.izip(entities, move):
        thing.location += adjust

    return resolved

def resolve_passive_passive_collisions(entities):
    '''Makes colliding entities bounce off each other as though they were
    all the same mass.

    Returns the number of resolutions performed.

    TODO: Add elasticity parameters and not this sheepy shit.'''

    ppcollisions = passive_passive_collisions(entities)

    # Passive hitbox of each entity in world coordinates.
    # Created here so we don't realloc for each collision.
    hbp1 = components.hitbox((0, 0), (0, 0))
    hbp2 = components.hitbox((0, 0), (0, 0))
    move = numpy.zeros((len(entities), 2))
    contributors = numpy.zeros ((len(entities),), dtype=int)
    swaps = []

    for (thing1, thing2), (i1, i2) in itertools.izip(itertools.product(entities, entities),
                                                     itertools.product(range(len(entities)), range(len(entities)))):
        if i1 >= i2:
            continue
        if ppcollisions[i1, i2]:
            # Construct hitboxes in world coordinates.
            numpy.add(thing1.hitbox_passive.point, thing1.location, hbp1.point)
            hbp1.size[:] = thing1.hitbox_passive.size

            numpy.add(thing2.hitbox_passive.point, thing2.location, hbp2.point)
            hbp2.size[:] = thing2.hitbox_passive.size

            side, diff = complete_collision(hbp1, hbp2)

            # Set grounded flag when one is on top of the other
            if side == 3:
                thing1.tags.add('grounded')
            elif side == 2:
                thing2.tags.add('grounded')

            side = side // 2
            v1, v2 = thing1.motion_v, thing2.motion_v

            # Already moving away from each other, nothing to do here.
            if (v1[side] - v2[side]) * diff > 0:
                continue

            # calculate movement
            # Move entity if it's moving against the diff
            if v1[side] * diff <= 0:
                move[i1, side] += diff
                contributors[i1] += 1

            if v2[side] * diff >= 0:
                move[i2, side] -= diff
                contributors[i2] += 1

            if v1[side] != v2[side]:
                swaps.append((side, i1, i2))

    # limit location adjustment
    mask = contributors != 0
    move[mask] /= contributors.reshape((-1, 1))[mask]
    numpy.clip(move, -MAX_DIFF, MAX_DIFF, move)
    for thing, adjust in itertools.izip(entities, move):
        thing.location += adjust

    for side, i1, i2 in swaps:
        m1 = entities[i1].motion_v[side]
        m2 = entities[i2].motion_v[side]
        entities[i1].motion_v[side] = m2
        entities[i2].motion_v[side] = m1


    return len(swaps)


def resolve_passive_active_collisions(entities):
    '''Decreases the health of each entity whose passive hitbox
    collides with another's active hitbox.

    TODO: Add damage parameter.'''

    apcollisions = active_passive_collisions(entities)
    for i1, i2 in itertools.product(xrange(len(entities)), xrange(len(entities))):
        if i1 == i2:
            continue
        if apcollisions[i1, i2]:
            entities[i2].hitpoints -= 1
