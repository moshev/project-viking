# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement


import components
import controls
import physics
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
    player.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    player.physics.add(physics.speed_limiter((10, 10000)), components.physics.GROUP_VELOCITY)

    player.controller = controls.Controller(player, viking_parts.IdleRight, viking_parts.DummyAnimation,
                                            {(key_left, KEYUP): 'left_release',
                                             (key_left, KEYDOWN): 'left_press',
                                             (key_right, KEYUP): 'right_release',
                                             (key_right, KEYDOWN): 'right_press',
                                             (key_jump, KEYUP): 'up_release',
                                             (key_jump, KEYDOWN): 'up_press',})
    return player


def drake(datadir, clock):
    '''Make an inert drake'''
    raise RuntimeError('Not implemented')


def sheep(datadir, clock):
    '''Make an inert sheep'''
    raise RuntimeError('Not implemented')


def floaty_sheep(datadir, clock):
    '''Make an inert sheep unaffected by gravity'''
    raise RuntimeError('Not implemented')

