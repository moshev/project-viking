# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement


import components
import controls
import physics
import util
from . import shaders
from pygame.constants import KEYDOWN, KEYUP


__all__ = ['viking',
           'drake',
           'sheep',
           'floaty_sheep']


def viking(datadir, clock, keyboard, key_left, key_right, key_jump, key_punch):
    '''Make a viking controlled with the given keys'''

    from . import viking_parts

    player = components.entity('Player', clock, keyboard,
                               location=(100, 0),
                               motion=components.motion(),
                               graphics=components.graphics(None, None))

    physics.regular_physics(player)
    player.physics.add(physics.apply_friction(2.0, 1.0), components.physics.GROUP_VELOCITY)
    player.physics.add(physics.speed_limiter((10, 10000)), components.physics.GROUP_VELOCITY)

    player.controller = controls.Controller(player, viking_parts.IdleRight, viking_parts.IdleRightAnimation,
                                            {(key_left, KEYUP): 'left_release',
                                             (key_left, KEYDOWN): 'left_press',
                                             (key_right, KEYUP): 'right_release',
                                             (key_right, KEYDOWN): 'right_press',
                                             (key_jump, KEYUP): 'jump_release',
                                             (key_jump, KEYDOWN): 'jump_press',
                                             (key_punch, KEYUP): 'punch_release',
                                             (key_punch, KEYDOWN): 'punch_press',})
    return player


def drake(datadir, clock):
    '''Make an inert drake'''
    drake_frame = util.load_frame(datadir, 'drake')
    drake = components.entity('Drake', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=200)
    drake.set_frame(drake_frame)
    physics.regular_physics(drake)
    drake.physics.add(physics.apply_friction(5), components.physics.GROUP_VELOCITY)
    return drake


def sheep(datadir, clock):
    '''Make an inert sheep'''
    sheep_frame = util.load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    physics.regular_physics(sheep)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep


def floaty_sheep(datadir, clock):
    '''Make an inert sheep unaffected by gravity'''
    sheep_frame = util.load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 400),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    components.physics(sheep)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep

