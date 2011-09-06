# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import itertools
import unittest
import controls
import util
import animatorium
import pygame
from pygame.constants import *


class DummyAnimationState(animatorium.BaseAnimationState):
    '''
    Dummy state producing only one frame and looping forever.
    '''
    def __init__(self):
        pass


    def __iter__(self):
        while True:
            yield {'sprite': None, 'sp': None, 'hbp': None, 'hba': None}


    def next(self, event):
        return self


class AnimationStateA(animatorium.BaseAnimationState):
    """first state"""
    iters = 0

    def __transitions__(self):
        return {'stateB': AnimationStateB}


    def __iter__(self):
        AnimationStateA.iters += 1
        while True:
            yield {'sprite': None, 'sp': None, 'hbp': None, 'hba': None}


class AnimationStateB(animatorium.BaseAnimationState):
    """first state"""
    iters = 0

    def __transitions__(self):
        return {'stateA': AnimationStateA}


    def __iter__(self):
        AnimationStateB.iters += 1
        while True:
            yield {'sprite': None, 'sp': None, 'hbp': None, 'hba': None}


class ActionStateA(util.basestate.BaseState):
    ticks = 0


    def __transitions__(self):
        return {'b': ActionStateB}


    def on_tick(self, entity):
        ActionStateA.ticks += 1


    @property
    def name(self):
        return 'stateA'


class ActionStateB(util.basestate.BaseState):
    ticks = 0


    def __transitions__(self):
        return {'a': ActionStateA}


    def on_tick(self, entity):
        ActionStateB.ticks += 1


    @property
    def name(self):
        return 'stateB'


class DummyEvent(object):
    """Dummy event"""
    def __init__(self, key, type):
        self.key = key
        self.type = type


class DummyEntity(object):
    """Dummy entity - does nothing"""
    def __init__(self):
        self.keyboard = set()
        self.clock = set()
        self.frame = None


    def set_frame(self, frame):
        self.frame = frame


class TestController(unittest.TestCase):
    def setUp(self):
        print('setup')
        ActionStateA.ticks = 0
        ActionStateB.ticks = 0
        AnimationStateA.iters = 0
        AnimationStateB.iters = 0
        self.c = controls.Controller(DummyEntity(), ActionStateA, AnimationStateA,
                                     {(K_a, KEYDOWN): 'a',
                                      (K_b, KEYDOWN): 'b'})


    def test_two_ticks(self):
        self.c.on_tick(None)
        self.c.on_tick(None)
        self.assertEquals(2, ActionStateA.ticks)
        self.assertEquals(1, AnimationStateA.iters)


    def test_keyress(self):
        self.c.on_tick(None)
        self.c.on_tick(None)
        self.assertEquals(2, ActionStateA.ticks)
        self.assertEquals(1, AnimationStateA.iters)
        self.c.on_key(DummyEvent(K_b, KEYDOWN))
        self.assertEquals(0, AnimationStateB.iters)
        self.c.on_tick(None)
        self.assertEquals(1, AnimationStateB.iters)
        self.assertEquals(2, ActionStateA.ticks)
