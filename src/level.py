# -*- coding: utf-8 -*-
from __future__ import division, generators, print_function, with_statement

import components
import cPickle as pickle
import levelformat
import numpy

class Level(object):
    pass


def load(filename):
    '''Returns a list of hitboxes - the rects stored in the file.
    Raises IOError if file doesn't exist; LevelFormatError if format is unsupported.'''

    with open(filename) as levelfile:
        self.level.clear()
        data = pickle.load(levelfile)
        if data.version > 1:
            raise levelformat.LevelFormatError('Too high version: {0}'.format(data.version))

        # And return a list of all rects with their positions in world coordinates
        return [components.hitbox_passive((r.x + r.dx, r.y + r.dy), (r.w, r.h)) for r in data.rects]

