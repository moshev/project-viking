# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

class BaseState(object):
    '''
    Base class for states of a state machine.
    Each state is a derivative of this class that must
    define a __transitions__() method returning a dictionary
    mapping inputs to classes.
    '''

    def __init__(self, instances=None):
        '''Create a new state machine starting from this state.'''
        self.transitions = self.__transitions__()
        if instances is None:
            instances = {}

        for key, cls in self.transitions.items():
            if cls in instances:
                state = instances[cls]
            else:
                state = cls(instances)
                instances[cls] = state

            self.transitions[key] = state


    def __transitions__(self):
        '''
        Override this method in subclasses.
        It must return a dict mapping events to classes, from this a mapping from events to
        class instances will be constructed, where across the entire state machine each class
        will have precisely one instance shared by all states which have an event that leads
        to that class.
        '''
        return {}


    def next(self, event):
        '''
        Get the next state from this, based on event. Returns None if no transition is defined.
        '''
        return self.transitions.get(event)

