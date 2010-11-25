from __future__ import print_function, absolute_import
import numpy

class graphics:
    def __init__(self, color, size):
        '''
        color is a tuple of three integers in [0; 255]
        size is a tuple of two integers
        '''
        self.color, self.size = color, size

class motion:
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = numpy.array(velocity, dtype=float), numpy.array(acceleration, dtype=float)

class entity:
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None, location=None, motion=None, graphics=None):
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = numpy.array(location, dtype=float)
        self.motion = motion
        self.graphics = graphics

