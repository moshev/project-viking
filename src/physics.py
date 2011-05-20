from __future__ import print_function, absolute_import
import numpy
import math
import pygame
from pygame.locals import *
import components
from constants import *
from collections import defaultdict
from util import *



def apply_friction(friction):
    def friction_on(entity):
        if 'grounded' in entity.tags:
            if abs(entity.motion.v[0]) > friction:
                if entity.motion.v[0] > 0:
                    entity.motion.v[0] -= friction
                else:
                    entity.motion.v[0] += friction
            else:
                entity.motion.v[0] = 0
    return friction_on


def speed_limiter(limit):
    limit = arrayify(limit)
    def limiter(entity):
        for i in range(len(limit)):
            if entity.motion.v[i] > limit[i]:
                entity.motion.v[i] = limit[i]
            elif entity.motion.v[i] < -limit[i]:
                entity.motion.v[i] = -limit[i]
    return limiter


def regular_physics(entity):
    '''
    Returns a physics object with added velocity and location calculators and affected by gravity.
    '''
    p = components.physics(entity)
    return p


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

