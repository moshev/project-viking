from __future__ import print_function, absolute_import
import sys
import os
import numpy

def arrayify(x):
    '''Constructs a float array from x'''
    return numpy.array(x, dtype=float)

def find_datadir():
    '''
    Returns an absolute path to the 'data' directory.
    Source and data should be laid out like so:
        +/
        |
        +--+ data
        |  | ... files ...
        |
        +--+ src
           | sys.argv[0]
    '''
    return os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'data'))

def __rk4(y, dy):
    '''
    Calculates the next value for y, given the past derivatives of y, dys.
    y must be a numpy array of shape (x,)
    dy must be a numpy array of shape (4, x).
    '''
    return y + (dy[0] + dy[1] * 2 + dy[2] * 2 + dy[3]) / 6

