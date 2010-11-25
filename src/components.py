from __future__ import print_function, absolute_import
import numpy
from util import arrayify

class graphics:
    def __init__(self, sprite, anchor=(0, 0)):
        '''
        sprite is a pygame.surface or other blittable object.
        anchor is a tuple, giving the location of the object's
        upper-left corner inside the sprite.
        '''
        self.sprite = sprite
        self.anchor = arrayify(anchor)

class motion:
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = map(arrayify, (velocity, acceleration))

class location:
    def __init__(self, point, size):
        '''
        point, size - tuples of two numbers describing the
          upper-left corner and size (width, height) of the entity
        '''
        self.point, self.size = map(arrayify, (point, size))

def velocity_calculator(entity):
    entity.motion.v += entity.motion.a

def location_calculator(entity):
    entity.location.point += entity.motion.v

class entity:
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None, location=None, motion=None, graphics=None):
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = location
        self.motion = motion
        self.graphics = graphics
        self.physics = None

