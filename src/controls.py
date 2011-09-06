from __future__ import print_function, absolute_import
import numpy
import components
import util
import animatorium
from pygame.locals import *


class BaseActionState(util.basestate.BaseState):
    '''
    An action state has an on_tick(entity) method which must return
    the next action state if this one has finished, plus a "name".
    The name will be used as an event for the animation framework.

    If the subclass defines a __reset__(self) method, it
    will be called before returning the next state from the next() method.
    '''
    def __init__(self, name):
        '''
        Initialise an action state.

        name - state's name
        '''
        super(BaseActionState, self).__init__()
        self.name = name


    def on_tick(self, entity):
        raise NotImplementedError


    def __reset__(self):
        pass


    def next(self, event):
        next = super(BaseActionState, self).next(event)
        if next:
            next.__reset__()
        return next


class Controller(object):
    '''
    Takes keyboard and clock input from an entity and
    takes care to drive the action and animation states.
    '''
    def __init__(self, entity, initial_action, initial_animation, keymap=None):
        '''
        entity - a controllable entity

        initial_action - initial action state
        An action state must define an on_tick method,
        which is called once per frame with the entity as its sole argument and must
        return a next action state if this action has been completed.

        initial_animation - initial animation state

        keymap - a dict mapping key events to events for the action loop
        may be set to None and the entity would be not controllable.
        A "key event" is a tuple of (keycode, type) with type in {KEYDOWN, KEYUP}.
        '''

        self.entity = entity

        # Allow passing a class or an instance
        if isinstance(initial_action, type):
            initial_action = initial_action()
        self.action = initial_action

        self.animation = animatorium.animatorium(initial_animation)
        self.animation_event = None

        if entity.keyboard is not None and keymap:
            self.keymap = keymap
            entity.keyboard.add(self.on_key)
        entity.clock.add(self.on_tick)


    def on_tick(self, event):
        frame = self.animation.send(self.animation_event)
        self.entity.set_frame(frame)
        next_action = self.action.on_tick(self.entity)
        if next_action is not None:
            self.animation_event = next_action.name
            self.action = next_action
        else:
            self.animation_event = None


    def on_key(self, event):
        try:
            event_name = self.keymap[(event.key, event.type)]
            next_action = self.action.next(event_name)
            if next_action is not None:
                self.animation_event = next_action.name
                self.action = next_action
            else:
                self.animation_event = None
        except KeyError:
            # Key not in map. So do nothing.
            pass


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
        if self.entity.keyboard is not None:
            self.entity.keyboard.add(self.on_key)
        self.entity.clock.add(self.on_tick)

    def start(self):
        self.run = True

    def stop(self):
        self.run = False

    def on_physics(self, entity):
        if self.run:
            self.entity.motion.v += self.a

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

class animation_while_keydown(animation):
    '''
    Displays an animation once, stops when key is released.
    '''
    def __init__(self, entity, frames, key, next_animation, transitions=None):
        animation.__init__(self, entity, frames, next_animation, transitions)
        self.key = key
        self.entity.keyboard.add(self.on_key)

    def on_key(self, event):
        if self.run and event.type == KEYUP and event.key == self.key:
            self.stop()
            self.next.start()
        return self.on_key

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
        self.tick = min(self.tick + 1, self.frames - 1)
        self.entity.motion.v[:] += self.vectors[self.tick]
        return self.state_accelerate

    def state_decelerate(self):
        self.entity.motion.v[:] -= self.vectors[self.tick]
        self.tick = max(self.tick - 1, 0)
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
        self.entity.motion.a[:] += self.a
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

