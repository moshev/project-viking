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
        upper-left corner, relative to the object's location.
        '''
        self.sprite = sprite
        self.anchor = arrayify(anchor)

class motion(object):
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = map(arrayify, (velocity, acceleration))

class hitbox(object):
    def __init__(self, point, size):
        '''
        point, size - tuples of two numbers describing the
          upper-left corner and size (width, height) of the entity
        '''
        self.point, self.size = map(arrayify, (point, size))

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
    GROUP_LAST = 0
    GROUP_LOCATION = 10
    GROUP_VELOCITY = 20
    GROUP_ACCELERATION = 30

    def __init__(self, entity):
        '''
        entity - the entity to act upon
        '''
        self.modifiers = defaultdict(list)
        self.entity = entity
        self.entity.clock.add(self.on_tick)
        assert(self.entity.physics is None)
        self.entity.physics = self
        self.last_position = numpy.array(self.entity.location)

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
        self.last_position[:] = self.entity.location
        for priority in self.modifiers.iterkeys():
            for modifier in self.modifiers[priority]:
                modifier(self.entity)
        return self.on_tick

class entity(object):
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None,
                 location=None, motion=None, physics=None,
                 hitbox_passive=None, hitbox_active=None,
                 graphics=None, hitpoints=100):
        '''
        clock, keyboard and mouse are evetn dispatchers
        location is a tuple of x and y coordinates
        motion, physics are instances of motion and physics
        hitbox_active and hitbox_passive are instances of hitbox
        sprite is an image
        '''
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = arrayify(location)
        self.motion = motion
        self.graphics = graphics
        self.physics = physics
        self.hitbox_active = hitbox_active
        self.hitbox_passive = hitbox_passive
        self.tags = set()
        self.hitpoints = hitpoints

    def set_frame(self, frame):
        self.graphics.sprite = frame['sprite']
        self.graphics.anchor = frame['sp']
        self.hitbox_passive = frame['hbp']
        self.hitbox_active = frame['hba']

