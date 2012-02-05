from __future__ import print_function, absolute_import
import numpy
import components
import util
import animatorium
from pygame.locals import *


__all__ = ['BaseActionState',
           'Controller']


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
        self.controller = self

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

        return self.on_tick


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

        return self.on_key
