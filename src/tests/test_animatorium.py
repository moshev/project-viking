# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import unittest
from animatorium import *


# A couple of basic animation states.
class WalkAnimation(BaseAnimationState):
    def __init__(self, *args):
        super(WalkAnimation, self).__init__(*args)
        self.__frames__ = [1, 2, 3]

    def __transitions__(self):
        return {None: WalkAnimation,
                'keyrelease': IdleAnimation}


class IdleAnimation(BaseAnimationState):
    def __init__(self, *args):
        super(IdleAnimation, self).__init__(*args)
        self.__frames__ = [4, 5]

    def __transitions__(self):
        return {None: IdleAnimation,
                'keypress': WalkAnimation}


class TestAnimatorium(unittest.TestCase):
    """Tests the animatorium system for animation"""

    def test_loop(self):
        anim = animatorium(IdleAnimation)
        self.assertEqual([4, 5, 4, 5, 4, 5],
                         [next(anim), next(anim), next(anim),
                          next(anim), next(anim), next(anim)])

    def test_transition(self):
        anim = animatorium(IdleAnimation)
        self.assertEqual([4, 5, 4,
                          1, 2, 3, 1,
                          4, 5,
                          1, 2],
                         [anim.next(), anim.next(), anim.next(),
                          anim.send('keypress'), anim.next(), anim.next(), anim.next(),
                          anim.send('keyrelease'), anim.next(),
                          anim.send('keypress'), anim.next()])

