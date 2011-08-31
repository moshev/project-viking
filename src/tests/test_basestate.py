# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import unittest
import util

class BaseStateSimpleTest(unittest.TestCase):

    class State1(util.basestate.BaseState):
        def __transitions__(self):
            return {1: BaseStateSimpleTest.State1}

    class State2(util.basestate.BaseState):
        def __transitions__(self):
            return {2: BaseStateSimpleTest.State3}

    class State3(util.basestate.BaseState):
        pass

    def test_null(self):
        state = util.basestate.BaseState()
        self.assertIs(None, state.next(None))

    def test_single(self):
        state = BaseStateSimpleTest.State2()
        self.assertIs(BaseStateSimpleTest.State3, state.next(2).__class__)

        state = state.next(2)
        self.assertIs(None, state.next(5))

    def test_cyclic(self):
        state = BaseStateSimpleTest.State1()
        self.assertIs(state, state.next(1))


if __name__ == '__main__':
    unittest.main()

