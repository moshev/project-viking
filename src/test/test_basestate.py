# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import util.basestate
import unittest

class BaseStateSimpleTest(unittest.TestCase):

    def test_null(self):
        state = util.basestate.BaseState()
        self.assertEquals(None, state.next(None))

if __name__ == '__main__':
    unittest.main()

