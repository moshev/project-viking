# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

class BaseState(object):
    '''
    Base class for states of a state machine.
    Each state is a derivative of this class that must
    define a __transitions__() method returning a dictionary
    mapping inputs to classes.

    Derivatives MUST have a no-args constructor.

    Do not forget to call super.__init__ in derivatives!
    '''

    def __init__(self):
        '''Create a new state machine starting from this state.'''
        self.transitions = None


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
        if self.transitions is None:
            BaseState._init_transitions(self)
        return self.transitions.get(event)


    @staticmethod
    def _init_transitions(root):
        '''
        Initialises all transition dicts starting at the root.
        '''
        instances = {root.__class__: root}
        classes = list(root.__transitions__().values())
        while len(classes) > 0:
            cls = classes.pop()
            if cls not in instances:
                state = cls()
                instances[cls] = cls()
                classes.extend(state.__transitions__().values())

        for state in instances.values():
            state.transitions = {evt: instances[cls] for evt, cls in state.__transitions__().items()}

