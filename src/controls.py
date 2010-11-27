from __future__ import print_function, absolute_import
import numpy
import components
from pygame.locals import *
from util import arrayify

class move_while_key_pressed:
    '''
    Accelerates the entity along the given acceleration vector for some frames,
    then decelerates it when the key is released.
    '''
    def __init__(self, entity, key, vector, frames=0):
        '''
        Adds self to the entity's keyboard event dispatcher.
        Adds self to the entity's physics, in the ACCELERATION_GROUP
        If frames is 0, the acceleration is applied until the key is released.
        '''
        self.entity, self.key = entity, key
        self.entity.physics.add(self.on_physics, components.physics.GROUP_VELOCITY)
        self.entity.keyboard.add(self.on_key)
        self.frames = frames
        self.tick = 0
        self.state = self.state_none
        assert frames != 0, 'omgwtf'
        self.vectors = numpy.zeros((frames + 1, 2))
        self.vectors += arrayify(vector)
        self.vectors *= [[x, x] for x in range(0, frames + 1)]

    def state_none(self):
        return self.state_none

    def state_accelerate(self):
        self.entity.motion.v[:] -= self.vectors[self.tick]
        self.tick += 1
        if self.tick >= self.frames and self.frames != 0:
            self.tick = self.frames - 1
        self.entity.motion.v[:] += self.vectors[self.tick]
        return self.state_accelerate

    def state_decelerate(self):
        self.entity.motion.v[:] -= self.vectors[self.tick]
        self.tick -= 1
        if self.tick <= 0:
            self.tick = 0
        self.entity.motion.v[:] += self.vectors[self.tick]
        return self.state_decelerate

    def on_physics(self, entity):
        self.state = self.state()

    def on_key(self, event):
        if event.key != self.key:
            return self.on_key
        if event.type == KEYDOWN:
            self.state = self.state_accelerate
        elif event.type == KEYUP:
            self.state = self.state_decelerate
        return self.on_key
        
class jump_when_key_pressed:
    '''
    Accelerates the entity along the given acceleration vector for some frames.
    '''
    def __init__(self, entity, key, vector, frames=0):
        '''
        Adds self to the entity's keyboard event dispatcher.
        Adds self to the entity's physics, in the ACCELERATION_GROUP
        If frames is 0, the acceleration is applied until the key is released.
        '''
        self.entity, self.key, self.a = entity, key, arrayify(vector)
        self.entity.physics.add(self.on_physics, components.physics.GROUP_ACCELERATION)
        self.entity.keyboard.add(self.on_key)
        self.frames = frames
        self.tick = 0
        self.state = self.state_none

    def state_none(self):
        if self.tick > 0:
            self.tick -= 1
        return self.state_none

    def state_accelerate(self):
        self.entity.motion.a += self.a
        self.tick += 1
        if self.tick >= self.frames and self.frames != 0:
            return self.state_none
        else:
            return self.state_accelerate

    def on_physics(self, entity):
        self.state = self.state()

    def on_key(self, event):
        if event.key != self.key:
            return self.on_key
        if event.type == KEYDOWN and 'grounded' in self.entity.tags:
            self.state = self.state_accelerate
        elif event.type == KEYUP:
            self.state = self.state_none
        return self.on_key

