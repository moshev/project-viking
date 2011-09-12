# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import util

__all__ = ['BaseAnimationState',
           'animatorium']


class BaseAnimationState(util.basestate.BaseState):
    '''
    Base class for animation states.
    An animation state is a state which has a list of associated frames
    and transitions to other animation states based on events.
    When an animation's list of frames is exhausted, the current animation state
    is sent None as an event. For looping animations, they should return themselves.

    Apart from the __transitions__ function mandated by BaseState,
    animation states must also either have a '__frames__' property containing
    an iterable of their states, or implement the __iter__ function
    and return an iterator over their frames.

    The default iterator uses the supplied list/tuple.
    '''

    def __iter__(self):
        '''
        Returns an iterator over this state's frames.
        '''
        try:
            return iter(self.__frames__)
        except AttributeError:
            return iter(())

def animatorium(initial_state):
    """
    An animatorium is a state machine working as a coroutine abusing generators.
    initial_state: a BaseAnimationState instance or subclass.
    """

    if isinstance(initial_state, type):
        if issubclass(initial_state, BaseAnimationState):
            initial_state = initial_state()
        else:
            raise TypeError(format('Expected BaseAnimationState, got {0}', initial_state))
    elif not isinstance(initial_state, BaseAnimationState):
        raise TypeError(format('Expected BaseAnimationState, got {0}',
                               initial_state.__class__))

    def main_loop():
        # init - get first event
        state = initial_state
        frames = iter(state)
        event = yield None
        switch = False

        while frames is not None and state is not None:
            if event is None:
                try:
                    event = (yield next(frames))
                except StopIteration:
                    switch = True
            else:
                switch = True

            if switch:
                newstate = state.next(event)
                if newstate is not None:
                    frames = iter(newstate)
                    state = newstate
                elif event is None:
                    # reiterate current state
                    frames = iter(state)
                event = None
                switch = False

    # Initialise generator so it will react to send() events
    loop = main_loop()
    loop.next()
    return loop

