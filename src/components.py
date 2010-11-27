from __future__ import print_function, absolute_import
import numpy
from collections import defaultdict
from util import arrayify
from constants import *

class graphics(object):
    def __init__(self, sprite, anchor=(0, 0)):
        '''
        sprite is a pygame.surface or other blittable object.
        anchor is a tuple, giving the location of the sprite's
        upper-left corner, relative to the object's location.point.
        '''
        self.sprite = sprite
        self.anchor = arrayify(anchor)

class motion(object):
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = map(arrayify, (velocity, acceleration))

class location(object):
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

class physics(object):
    '''
    A collection of ordered physics modifiers on an entity.
    On the start of each tick, the entity's acceleration is zeroed.
    A few standard constants are added for prioritising the modifiers.
    Modifiers are applied starting with the ones with lowest number,
    to the ones with highest number.
    Add all things that modify acceleration first,
    then a velocity-from-acceleration calculator,
    then all things that work with velocity,
    then a location-from-velocity calculator,
    then everything which limits movement.
    The modifiers are applied on each clock tick.
    '''
    GROUP_ACCELERATION = 10
    GROUP_VELOCITY = 20
    GROUP_LOCATION = 30
    GROUP_LAST = 40
     
    def __init__(self, entity):
        '''
        entity - the entity to act upon
        '''
        self.modifiers = defaultdict(list)
        self.entity = entity
        self.entity.clock.add(self.on_tick)
        assert(self.entity.physics is None)
        self.entity.physics = self
        self.last_position = numpy.array(self.entity.location.point)

    def add(self, modifier, priority):
        self.modifiers[priority].append(modifier)

    def remove(self, modifier, priority=None):
        '''
        If priority is not given, remove the modifier from all groups.
        If the modifier is not present in the given group, this is a no-op
        '''
        if priority is None:
            for priority in self.modifiers.iterkeys():
                self.remove(modifier, priority)
        else:
            try:
                self.modifiers[priority].remove(modifier)
            except ValueError:
                pass

    def on_tick(self, event):
        if event.type != TICK: return self.on_tick
        # Reset acceleration to 0 and velocity to the difference between the last two frames.
        self.entity.motion.a[:] = 0
        self.entity.motion.v[:] = self.entity.location.point - self.last_position
        self.last_position[:] = self.entity.location.point
        for priority in self.modifiers.iterkeys():
            for modifier in self.modifiers[priority]:
                modifier(self.entity)
        return self.on_tick

class entity(object):
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None, location=None, motion=None, graphics=None):
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = location
        self.motion = motion
        self.graphics = graphics
        self.physics = None
        self.tags = set()

