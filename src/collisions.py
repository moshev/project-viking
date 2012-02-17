# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement
import numpy
import itertools
import components
import random

MAX_DIFF = 5.0


def passive_passive_collisions(toplefts, bottomrights):
    '''
    Returns a NxN array where element at [i, j] says if
    thing i collides with thing j with respect to their passive hitboxes.

    toplefts and bottomrights must be arrays of shape (N, 2), containing
    the global coordinates of the hitboxes' corners

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
    halfnegcheck = numpy.any(toplefts[numpy.newaxis, :, :] >= bottomrights[:, numpy.newaxis, :], axis=2)
    result = numpy.logical_not(numpy.logical_or(halfnegcheck, halfnegcheck.T))

    # Remove self collisions
    result[numpy.diag_indices_from(result)] = False
    return result


def active_passive_collisions(active_tl, active_br, passive_tl, passive_br):
    '''
    Returns an NxN array, where element at [i, j] says if
    thing i's active hitbox crosses thing j's active hitbox.
    An active hitbox isn't considered if any of its dimensions is not-positive.

    active/passive_tl/br must be arrays of shape (N, 2) - the boxes' corners in
    global coordinates

    See comment for passive_passive_collisions for longer explanation.
    The main difference is that we can't cheat here and do half the checks,
    then transpose, we need to do all checks.
    '''
    passive_tl_3d = passive_tl_3d.reshape(1, -1, 2)
    passive_br_3d = passive_br_3d.reshape(1, -1, 2)

    active_tl_3d = active_tl_3d.reshape(-1, 1, 2)
    active_br_3d = active_br_3d.reshape(-1, 1, 2)

    negcheck = numpy.logical_or(numpy.any(active_tl_3d > passive_br_3d, axis=2),
                                numpy.any(active_br_3d < passive_tl_3d, axis=2))

    legible = numpy.all(active_tl < active_br, axis=1).reshape(-1, 1)

    result = numpy.logical_and(numpy.logical_not(negcheck), legible)

    # Remove self collisions
    result[numpy.diag_indices_from(result)] = False
    return result


def passive_walls_collisions(passive_tl, passive_br, walls_tl, walls_br):
    '''
    Returns a NxM array where element at [i, j] says if
    thing i collides with wall j with respect to its passive hitbox.
    '''
    passive_tl = passive_tl.reshape(-1, 1, 2)
    passive_br = passive_br.reshape(-1, 1, 2);
    walls_tl = walls_tl.reshape(1, -1, 2)
    walls_br = walls_br.reshape(1, -1, 2);
    not_colliding = numpy.logical_or(numpy.any(passive_tl > walls_br, axis=2),
                                     numpy.any(passive_br < walls_tl, axis=2))

    return numpy.logical_not(not_colliding)


def complete_collision(box1_tl, box1_br, box2_tl, box2_br):
    '''Performs a complete collision between box1 and box2.
    Returns a tuple (which sides collide, motion vector with respect to box1)
    The first element is either
    0 - box2 left of box1, 1 - box1 left of box2
    2 - box2 over box1, 3 - box1 over box2

    The second is a single number - how much to move box1 in the given direction,
    so that it just touches box2.

    The returned values are arrays, each with N elements for each of the left elements'''

    #    tl
    #  x0, y0 ----+
    #    |        | <- passive hitbox of first "left" thing, i.e. box1_[0]
    #    |        |
    #    +----- x1, y1
    #             br
    #
    #    tl'
    # x'0, y'0 ---+
    #    |        | <- passive hitbox of first "right" thing, i.e. box2_[0]
    #    |        |
    #    +---- x'1, y'1
    #             br'
    #
    # diff = [x'1-x0, x'0-x1, y'1-y0, y'0-y1]
    #
    # diff[0] - how much to move the two hitboxes vertically
    #           such that box1 is above box2.
    # diff[1] - how much to move the two hitboxes vertically
    #           such that box2 is above box1.
    # and so on for diff[3],[4] - (1 2, then 2 1)
    #
    diff = numpy.empty((len(box1_tl), 4), dtype=float)
    numpy.subtract(box2_br, box1_tl, diff[:,::2])
    numpy.subtract(box2_tl, box1_br, diff[:,1::2])

    # And the movement is the shortest alternative
    side = numpy.argmin(numpy.abs(diff), axis=1)
    i = numpy.arange(len(diff))
    # now we reuse arrays like a boss
    diff[:,0] = diff[i, side]

    return (side, diff[:,0])


def resolve_wall_collisions(mask, location, motion_v, passive_tl, passive_br, walls_tl, walls_br):
    '''Resolves all collisions between entities and walls.
    TODO: Add inelasticity coefficients and make entities bounce around.'''

    pwcollisions = passive_walls_collisions(passive_tl, passive_br, walls_tl, walls_br);

    motion_v_to_zero = numpy.zeros(motion_v.shape, dtype=bool)
    nthings = len(location)
    move = numpy.zeros((nthings, 2))
    contributors = numpy.zeros((nthings, 2), dtype=int)
    allrows = numpy.arange(nthings)
    resolved = 0

    for wall_tl, wall_br in itertools.izip(walls_tl.reshape(-1, 1, 2), walls_br.reshape(-1, 1, 2)):
        # sidew, diffw - side and diff information for
        # all entities and ONE wall
        sidew, diffw = complete_collision(passive_tl, passive_br, wall_tl, wall_br)
        xory = sidew // 2
        aorb = sidew % 2
        v = motion_v[allrows, xory]
        vs = (v * diffw < 0) | (diffw == 0 & ((v > 0) == aorb)) | (v == 0)
        affectedrows = allrows[vs]
        xory = xory[vs]
        move[affectedrows, xory] += diffw[affectedrows]
        contributors[affectedrows, xory] += 1
        motion_v_to_zero[affectedrows, xory] = True
    del sidew, diffw, wall_tl, wall_br

    selector = contributors.flat != 0
    move.flat[selector] /= contributors.flat[selector]
    numpy.clip(move, -MAX_DIFF, MAX_DIFF, move)
    location[:] += move
    motion_v[motion_v_to_zero] = 0


def resolve_passive_passive_collisions(location, motion_v, passive_tl, passive_br):
    '''Makes colliding entities bounce off each other as though they were
    all the same mass.

    Returns the number of resolutions performed.

    TODO: Add elasticity parameters and not this sheepy shit.'''

    nthings = len(location)
    allrows = numpy.arange(nthings)
    buddy = numpy.zeros((nthings,), dtype=int)
    swapmask = numpy.zeros((nthings,), dtype=bool)
    move = numpy.zeros((nthings, 2))
    contributors = numpy.zeros((nthings,), dtype=int)

    ppcollisions = passive_passive_collisions(passive_tl, passive_br)
    lefti, righti = numpy.nonzero(ppcollisions)
    if len(lefti) == 0:
        return 0


    sides, diffs = complete_collision(numpy.take(passive_tl, lefti, axis=0),
                                      numpy.take(passive_br, lefti, axis=0),
                                      numpy.take(passive_tl, righti, axis=0),
                                      numpy.take(passive_br, righti, axis=0))

    motion_v[lefti,...] = motion_v[righti,...]
    return len(lefti)


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
