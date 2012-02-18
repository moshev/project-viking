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

    DO NOT THAT: the returned matrix has True along the diagonal =[
    '''
    result = numpy.any(toplefts[numpy.newaxis, :, :] > bottomrights[:, numpy.newaxis, :], axis=2)
    numpy.logical_or(result, result.T, out=result)
    numpy.logical_not(result, out=result)
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
    passive_tl_3d = passive_tl.reshape(1, -1, 2)
    passive_br_3d = passive_br.reshape(1, -1, 2)

    active_tl_3d = active_tl.reshape(-1, 1, 2)
    active_br_3d = active_br.reshape(-1, 1, 2)

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
    N = len(passive_tl)
    M = len(walls_tl)
    result = numpy.empty((N, M), dtype=bool)
    tmp = numpy.empty((N, M, 2), dtype=bool)
    passive_tl = passive_tl.reshape(-1, 1, 2)
    passive_br = passive_br.reshape(-1, 1, 2)
    walls_tl = walls_tl.reshape(1, -1, 2)
    walls_br = walls_br.reshape(1, -1, 2)
    numpy.greater(passive_tl, walls_br, out=tmp)
    numpy.any(tmp, axis=2, out=result)
    numpy.less(passive_br, walls_tl, out=tmp)
    numpy.any(tmp, axis=2, out=tmp[...,0])
    numpy.logical_or(result, tmp[...,0], out=result)
    numpy.logical_not(result, out=result)
    return result


def complete_collision(box1_tl, box1_br, box2_tl, box2_br):
    '''Performs a complete collision between one box against several.
    Returns a tuple (which sides collide, motion vector with respect to box1)
    The first element is an array of either
    0 - box2 left of box1, 1 - box1 left of box2
    2 - box2 over box1, 3 - box1 over box2

    The second is an (N,) array for how much to move box1 in the given direction,
    so that it just touches box2.

    The returned values are arrays, each with N elements for each of the boxes'''

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
    # diff[0] - how much to move box1 vertically
    #           such that box1 is above box2.
    # diff[1] - how much to move box1 vertically
    #           such that box2 is above box1.
    # and so on for diff[3],[4] - (1 2, then 2 1)
    #
    box1_tl = box1_tl.reshape(-1, 2)
    box1_br = box1_br.reshape(-1, 2)
    box2_tl = box2_tl.reshape(-1, 2)
    box2_br = box2_br.reshape(-1, 2)
    diff = numpy.empty((max(len(box1_tl), len(box2_tl)), 4), dtype=float)
    numpy.subtract(box2_br, box1_tl, diff[:,::2])
    numpy.subtract(box2_tl, box1_br, diff[:,1::2])

    # And the movement is the shortest alternative
    side = numpy.argmin(numpy.abs(diff), axis=1)
    i = numpy.arange(len(diff))
    # now we reuse arrays like a boss
    diff[:,0] = diff[i, side]

    return (side, diff[:,0])


def resolve_wall_collisions(mask, motion_v, passive_tl, passive_br, walls_tl, walls_br):
    '''Resolves all collisions between entities and walls.
    TODO: Add inelasticity coefficients and make entities bounce around.'''

    pwcollisions = passive_walls_collisions(passive_tl, passive_br, walls_tl, walls_br);

    motion_v_to_zero = numpy.zeros(motion_v.shape, dtype=bool)
    nthings = len(mask)
    diffs = numpy.zeros((nthings, 4))
    # True if entity has collision with wall on side X
    sides = numpy.zeros((nthings, 4), dtype=bool)

    npabs = numpy.abs
    nptake = numpy.take
    from itertools import izip
    for n, do in enumerate(mask):
        if not do:
            continue
        collideswith_indices = numpy.nonzero(pwcollisions[n])[0]
        if len(collideswith_indices) == 0:
            continue
        tl = passive_tl[n]
        br = passive_br[n]
        v_one = motion_v[n]
        diff_one = diffs[n]
        side_one = sides[n]
        w_tl = nptake(walls_tl, collideswith_indices, axis=0)
        w_br = nptake(walls_br, collideswith_indices, axis=0)
        side, diff = complete_collision(tl, br, w_tl, w_br)
        for s, d in izip(side, diff):
            if not side_one[s] or npabs(d) > npabs(diff_one[s]):
                side_one[s] = True
                diff_one[s] = d
    adjust = numpy.sum(diffs.reshape(-1, 2, 2), axis=2)
    return adjust, sides

def resolve_passive_passive_collisions(mask, motion_v, passive_tl, passive_br):
    '''Makes colliding entities bounce off each other as though they were
    all the same mass.

    Returns the number of resolutions performed

    TODO: Add elasticity parameters and not this sheepy shit.'''

    nthings = len(mask)
    adjust = numpy.zeros((nthings, 2))
    diffs = numpy.zeros((nthings, 4))
    sides = numpy.zeros((nthings, 4), dtype=bool)
    received_v = numpy.array(motion_v)
    done_impulse = 0.0
    ppcollisions = passive_passive_collisions(passive_tl, passive_br)
    dv = numpy.empty((4,))

    nptake = numpy.take
    npabs = numpy.abs
    npsubtract = numpy.subtract
    npnegative = numpy.negative
    from itertools import izip
    for n, do in enumerate(mask):
        if not do:
            continue
        collideswith_indices = numpy.nonzero(ppcollisions[n])[0]
        if len(collideswith_indices) == 1:
            continue
        tl = passive_tl[n]
        br = passive_br[n]
        diff_one = diffs[n]
        side_one = sides[n]
        v_one = motion_v[n]
        other_tl = numpy.take(passive_tl, collideswith_indices, axis=0)
        other_br = numpy.take(passive_br, collideswith_indices, axis=0)
        side, diff = complete_collision(tl, br, other_tl, other_br)
        for s, d, m in izip(side, diff, collideswith_indices):
            if not mask[m] or n == m:
                continue
            v = motion_v[m]
            npsubtract(v_one, v, out=dv[::2])
            npnegative(dv[::2], out=dv[1::2])
            if dv[s] < 0:
                ax = s // 2
                received_v[m, ax] = v_one[ax]
                done_impulse += abs(v_one[ax])
                if not side_one[s] or npabs(d) > npabs(diff_one[s]):
                    side_one[s] = True
                    diff_one[s] = d

    numpy.sum(diffs.reshape(-1, 2, 2), out=adjust, axis=2)
    motion_v[:] = received_v
    return adjust, sides, done_impulse


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
