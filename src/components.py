from __future__ import print_function, absolute_import
import numpy
import util
from collections import defaultdict
from constants import *


class graphics(object):
    def __init__(self, sprite, anchor=(0, 0)):
        '''
        sprite is a pygame.surface or other blittable object.
        anchor is a tuple, giving the location of the sprite's
        upper-left corner, relative to the object's location.
        '''
        self.sprite = sprite
        self.anchor = util.arrayify(anchor)


class motion(object):
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = map(util.arrayify, (velocity, acceleration))


class hitbox(object):
    def __init__(self, point, size):
        '''
        point, size - tuples of two numbers describing the
          upper-left corner and size (width, height) of the entity
        '''
        self.point, self.size = map(util.arrayify, (point, size))


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
                 location=(0,0), motion=motion((0,0), (0,0)), physics=None,
                 hitbox_passive=hitbox((0, 0), (0, 0)), hitbox_active=hitbox((0, 0), (0, 0)),
                 graphics=None, hitpoints=100):
        '''
        clock, keyboard and mouse are event dispatchers
        location is a tuple of x and y coordinates
        motion, physics are instances of motion and physics
        hitbox_active and hitbox_passive are instances of hitbox
        sprite is an image
        '''

        self.name = name or self.__class__.__name__
        self.arrayid = self.allocate_array()
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = util.arrayify(location)
        self.motion_v = motion.v
        self.motion_a = motion.a
        self.graphics = graphics
        self.physics = physics
        self.hitbox_active = hitbox_active
        self.hitbox_passive = hitbox_passive
        self.tags = set()
        self.hitpoints = hitpoints
        self.controller = None


    def set_frame(self, frame):
        self.graphics.sprite = frame['sprite']
        self.graphics.anchor = frame['sp']
        self.hitbox_passive = frame['hbp']
        self.hitbox_active = frame['hba']


    def dispose(self):
        self.release_array(self.arrayid)


    @property
    def hitbox_active(self):
        point = self.active_tl - self.location
        size = self.active_br - self.active_tl
        return hitbox(point, size)


    @hitbox_active.setter
    def hitbox_active(self, value):
        p = value.point + self.location
        self.active_tl = p
        self.active_br = p + value.size


    @property
    def hitbox_passive(self):
        point = self.passive_tl - self.location
        size = self.passive_br - self.passive_tl
        return hitbox(point, size)


    @hitbox_passive.setter
    def hitbox_passive(self, value):
        p = value.point + self.location
        self.passive_tl = p
        self.passive_br = p + value.size


    class _array_property(object):
        def __init__(self, name):
            self.name = name


        def __get__(self, instance, owner):
            if instance is None:
                return entity._data[self.name]
            else:
                return entity._data[self.name][instance.arrayid]


        def __set__(self, instance, value):
            entity._data[self.name][instance.arrayid] = value


    _space = 1024
    LOCATION = intern('location')
    MOTION_A = intern('motion_a')
    MOTION_V = intern('motion_v')
    ACTIVE_TL = intern('active_tl')
    ACTIVE_BR = intern('active_br')
    PASSIVE_TL = intern('passive_tl')
    PASSIVE_BR = intern('passive_br')

    _descriptor = numpy.dtype([(LOCATION, float, (2,)),
                               (MOTION_A, float, (2,)),
                               (MOTION_V, float, (2,)),
                               (ACTIVE_TL, float, (2,)),
                               (ACTIVE_BR, float, (2,)),
                               (PASSIVE_TL, float, (2,)),
                               (PASSIVE_BR, float, (2,)),])
    _data = numpy.zeros((_space,), dtype=_descriptor)
    _mask = numpy.zeros((_space,), dtype=numpy.bool)


    location = _array_property(LOCATION)
    motion_a = _array_property(MOTION_A)
    motion_v = _array_property(MOTION_V)
    active_tl = _array_property(ACTIVE_TL)
    active_br = _array_property(ACTIVE_BR)
    passive_tl = _array_property(PASSIVE_TL)
    passive_br = _array_property(PASSIVE_BR)


    @staticmethod
    def allocate_array():
        for arrayid in xrange(entity._space):
            if not entity._mask[arrayid]:
                break
        else:
            raise RuntimeError('exhausted _space for entity shit =[')

        entity._mask[arrayid] = True
        return arrayid


    @staticmethod
    def release_array(arrayid):
        entity._data[arrayid] = numpy.zeros((1,), dtype=entity._descriptor)
        entity._mask[arrayid] = False
