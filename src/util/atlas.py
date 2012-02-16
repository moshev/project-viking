# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import numpy

'''
Provides functions for fitting images in a texture atlas.
'''


class Atlas(object):
    '''Holds the world (or at least enough data to fit textures)'''
    def __init__(self, w, h):
        '''Create an empty atlas with space for width by height pixels'''
        # holds how much of each column is allocated
        self.allocated = numpy.zeros((w,), dtype=numpy.int16)
        self.w = w
        self.h = h


    def add(self, w, h):
        '''Adds an image of size (w, h) to the atlas and returns the coordinates of the top-left
        corner as a tuple (x, y). If it can't fit, return None'''
        cond = self.allocated <= self.h - h
        for x in xrange(self.w - w + 1):
            if numpy.all(cond[x:x + w]):
                y = numpy.max(self.allocated[x:x + w])
                self.allocated[x:x + w] = y + h
                return (x, y)
        return None
