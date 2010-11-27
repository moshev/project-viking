from __future__ import print_function, absolute_import
import numpy
import components
from pygame.locals import *
from util import arrayify

class looped_animation(object):
    '''
    loops an animation and moves the character;
    transitions to another animation on keypress.
    '''
    def __init__(self, entity, frames, acceleration, transitions=None):
        self.entity = entity
        self.frames = frames
        self.frame = 0
        self.transitions = transitions or dict()
        self.run = False
        self.a = arrayify(acceleration)
        self.entity.physics.add(self.on_physics, components.physics.GROUP_ACCELERATION)
        self.entity.keyboard.add(self.on_key)
        self.entity.clock.add(self.on_tick)

    def start(self):
        self.run = True

    def stop(self):
        self.run = False

    def on_physics(self, entity):
        if self.run:
            self.entity.motion.a += self.a

    def on_key(self, event):
        if self.run and event.type == KEYDOWN and event.key in self.transitions:
            self.stop()
            self.transitions[event.key].start()
        return self.on_key

    def on_tick(self, event):
        if self.run:
            self.entity.set_frame(self.frames[self.frame])
            self.frame += 1
            if self.frame >= len(self.frames):
                self.frame = 0
        return self.on_tick

class loop_while_keydown(looped_animation):
    def __init__(self, entity, frames, acceleration, key, next_animation=None, transitions=None):
        looped_animation.__init__(self, entity, frames, acceleration, transitions)
        self.next = next_animation
        self.key = key

    def on_key(self, event):
        if self.run and event.type == KEYUP and event.key == self.key:
            self.stop()
            self.next.start()
        else:
            looped_animation.on_key(self, event)
        return self.on_key

class animation(object):
    '''
    Displays an animation once and changes to the next animation.
    '''
    def __init__(self, entity, frames, next_animation, transitions=None):
        self.entity = entity
        self.frames = frames
        self.frame = 0
        self.next = next_animation
        self.transitions = transitions or dict()
        self.run = False
        self.entity.keyboard.add(self.on_key)
        self.entity.clock.add(self.on_tick)

    def start(self):
        self.run = True

    def stop(self):
        self.run = False
        self.frame = 0

    def on_key(self, event):
        if self.run and event.type == KEYDOWN and event.key in self.transitions:
            self.stop()
            self.transitions[event.key].start()
        return self.on_key

    def on_tick(self, event):
        if self.run:
            self.entity.set_frame(self.frames[self.frame])
            self.frame += 1
            if self.frame >= len(self.frames):
                self.stop()
                self.next.start()
        return self.on_tick
    pass

class move_while_key_pressed(object):
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
        
class jump_when_key_pressed(object):
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

