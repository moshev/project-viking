# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement


import util
import animatorium
import controls
import constants


WALK_SPEED = 5
JUMP_SPEED = -(constants.G + 1.6)
JUMP_TICKS = 12
PUNCH_TICKS = 22


class IdleRight(controls.BaseActionState):
    """Right-facing idle."""
    def __init__(self):
        super(IdleRight, self).__init__('idle_right')


    def on_tick(self, entity):
        pass


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_press': WalkLeft,
                'jump_press': JumpFacingRight,
                'punch_press': PunchRightIdle}


class IdleLeft(controls.BaseActionState):
    """Left-facing idle."""
    def __init__(self):
        super(IdleLeft, self).__init__('idle_left')


    def on_tick(self, entity):
        pass


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_press': WalkLeft,
                'jump_press': JumpFacingLeft,
                'punch_press': PunchLeftIdle}


class WalkRight(controls.BaseActionState):
    """Right-facing walk."""
    def __init__(self):
        super(WalkRight, self).__init__('walk_right')


    def on_tick(self, entity):
        entity.motion.a[0] += WALK_SPEED


    def __transitions__(self):
        return {'right_release': IdleRight,
                'left_press': WalkLeft,
                'jump_press': JumpRight,
                'punch_press': PunchRightWalking}


class WalkLeft(controls.BaseActionState):
    """Left-facing walk."""
    def __init__(self):
        super(WalkLeft, self).__init__('walk_left')


    def on_tick(self, entity):
        entity.motion.a[0] -= WALK_SPEED


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_release': IdleLeft,
                'jump_press': JumpLeft,
                'punch_press': PunchLeftWalking}


class JumpRight(controls.BaseActionState):
    """Jump right."""
    def __init__(self):
        super(JumpRight, self).__init__('jump_right')
        self.__reset__()

    def __reset__(self):
        self.ticks = 0
        self.valid = False


    def on_tick(self, entity):
        if not self.valid:
            self.valid = 'grounded' in entity.tags

        if not self.valid or self.ticks > JUMP_TICKS:
            return self.next('jump_release')

        entity.motion.a += (WALK_SPEED, JUMP_SPEED)
        self.ticks += 1


    def __transitions__(self):
        return {'jump_release': WalkRight,
                'right_release': IdleRight,
                'left_press': WalkLeft}


class JumpLeft(controls.BaseActionState):
    """Jump left."""
    def __init__(self):
        super(JumpLeft, self).__init__('jump_left')
        self.__reset__()

    def __reset__(self):
        self.ticks = 0
        self.valid = False


    def on_tick(self, entity):
        if not self.valid:
            self.valid = 'grounded' in entity.tags

        if not self.valid or self.ticks > JUMP_TICKS:
            return self.next('jump_release')

        entity.motion.a += (-WALK_SPEED, JUMP_SPEED)
        self.ticks += 1


    def __transitions__(self):
        return {'jump_release': WalkLeft,
                'left_release': IdleLeft,
                'right_press': WalkRight}


class JumpFacingRight(controls.BaseActionState):
    """Right-facing jump in place."""
    def __init__(self):
        super(JumpFacingRight, self).__init__('jump_facing_right')
        self.__reset__()

    def __reset__(self):
        self.ticks = 0
        self.valid = False


    def on_tick(self, entity):
        if not self.valid:
            self.valid = 'grounded' in entity.tags

        if not self.valid or self.ticks > JUMP_TICKS:
            return self.next('jump_release')

        entity.motion.a[1] += JUMP_SPEED
        self.ticks += 1


    def __transitions__(self):
        return {'jump_release': IdleRight,
                'left_press': WalkLeft,
                'right_press': WalkRight}


class JumpFacingLeft(controls.BaseActionState):
    """Left-facing jump in place."""
    def __init__(self):
        super(JumpFacingLeft, self).__init__('jump_facing_left')
        self.__reset__()

    def __reset__(self):
        self.ticks = 0
        self.valid = False


    def on_tick(self, entity):
        if not self.valid:
            self.valid = 'grounded' in entity.tags

        if not self.valid or self.ticks > JUMP_TICKS:
            return self.next('jump_release')

        entity.motion.a[1] += JUMP_SPEED
        self.ticks += 1


    def __transitions__(self):
        return {'jump_release': IdleLeft,
                'left_press': WalkLeft,
                'right_press': WalkRight}


class PunchBaseState(controls.BaseActionState):
    '''Base state for punching'''
    def __init__(self, name):
        '''
        name - action's name.
        '''
        super(PunchBaseState, self).__init__(name)
        self.ticks = 0


    def on_tick(self, entity):
        if self.ticks > PUNCH_TICKS:
            return self.next(None)
        self.ticks += 1


    def __reset__(self):
        self.ticks = 0


class PunchLeftIdle(PunchBaseState):
    def __init__(self):
        super(PunchLeftIdle, self).__init__("punch_left")


    def __transitions__(self):
        return {None: IdleLeft,
                'left_press': WalkLeft,
                'right_press': WalkRight,
                'jump_press': JumpFacingLeft}


class PunchRightIdle(PunchBaseState):
    def __init__(self):
        super(PunchRightIdle, self).__init__("punch_right")


    def __transitions__(self):
        return {None: IdleRight,
                'left_press': WalkLeft,
                'right_press': WalkRight,
                'jump_press': JumpFacingRight}


class PunchLeftWalking(PunchBaseState):
    def __init__(self):
        super(PunchLeftWalking, self).__init__("punch_left")


    def __transitions__(self):
        return {None: WalkLeft,
                'left_release': PunchLeftIdle,
                'right_press': WalkRight,
                'jump_press': JumpLeft}


class PunchRightWalking(PunchBaseState):
    def __init__(self):
        super(PunchRightWalking, self).__init__("punch_right")


    def __transitions__(self):
        return {None: WalkRight,
                'left_press': WalkLeft,
                'right_release': PunchRightIdle,
                'jump_press': JumpRight}


class BaseAnimation(animatorium.BaseAnimationState):
    '''Defines all transitions.'''


    def __transitions__(self):
        return {None: self._none_transition,
                'idle_right': IdleRightAnimation,
                'idle_left': IdleLeftAnimation,
                'walk_right': WalkRightAnimation,
                'walk_left': WalkLeftAnimation,
                'jump_right': JumpRightAnimation,
                'jump_left': JumpLeftAnimation,
                'jump_facing_right': JumpFacingRightAnimation,
                'jump_facing_left': JumpFacingLeftAnimation,
                'punch_right': PunchRightAnimation,
                'punch_left': PunchLeftAnimation,}


class OneFrameLoopedAnimation(BaseAnimation):
    '''
    Loops one frame forever.

    frame_name - the name of the frame to loop.

    flipped - if True, flip the frame.
    '''
    def __init__(self, frame_name, flipped=False):
        self._none_transition = self.__class__
        super(OneFrameLoopedAnimation, self).__init__()
        frame = util.load_frame(util.find_datadir(), frame_name)
        if flipped:
            frame = util.flip_frame(frame)
        self.frame = frame


    def __iter__(self):
        while True:
            yield self.frame


class LoopedAnimation(BaseAnimation):
    '''
    Loops a sequence of frames forever.

    frame_name - base name of the frames

    delays - how many frames of screen time each frame takes

    flipped - if the frames should be flipped
    '''
    def __init__(self, frame_name, delays, flipped=False):
        self._none_transition = self.__class__
        super(LoopedAnimation, self).__init__()
        frames = util.load_frame_sequence(util.find_datadir(), frame_name, len(delays))
        if (flipped):
            frames = map(util.flip_frame, frames)
        self.__frames__ = list(util.repeat_each(frames, delays))


class IdleRightAnimation(OneFrameLoopedAnimation):
    def __init__(self):
        super(IdleRightAnimation, self).__init__('model', False)


class IdleLeftAnimation(OneFrameLoopedAnimation):
    def __init__(self):
        super(IdleLeftAnimation, self).__init__('model', True)


class WalkRightAnimation(LoopedAnimation):
    def __init__(self):
        super(WalkRightAnimation, self).__init__('run', [5] * 6, False)


class WalkLeftAnimation(LoopedAnimation):
    def __init__(self):
        super(WalkLeftAnimation, self).__init__('run', [5] * 6, True)


class JumpAnimation(BaseAnimation):
    '''
    Basis for jump animations.

    flipped - False for right, True for left
    '''
    def __init__(self, flipped=False):
        super(JumpAnimation, self).__init__()
        self._next_transition = None
        self._iter = None
        delays = [3, 15, 18, 20]
        frames = util.load_frame_sequence(util.find_datadir(), 'jump', 4)
        if (flipped):
            frames = map(util.flip_frame, frames)
        self.__frames__ = list(util.repeat_each(frames, delays))


    def next(self, event):
        if event is not None:
            self._next_transition = super(JumpAnimation, self).next(event)
            return self
        else:
            next = self._next_transition or super(JumpAnimation, self).next(None)
            self._next_transition = super(JumpAnimation, self).next(None)
            self._iter = None
            return next


    def __iter__(self):
        if self._iter is None:
            self._iter = super(JumpAnimation, self).__iter__()

        return self._iter


class JumpRightAnimation(JumpAnimation):
    def __init__(self):
        self._none_transition = WalkRightAnimation
        super(JumpRightAnimation, self).__init__(False)


class JumpLeftAnimation(JumpAnimation):
    def __init__(self):
        self._none_transition = WalkLeftAnimation
        super(JumpLeftAnimation, self).__init__(True)


class JumpFacingRightAnimation(JumpAnimation):
    def __init__(self):
        self._none_transition = IdleRightAnimation
        super(JumpFacingRightAnimation, self).__init__(False)


class JumpFacingLeftAnimation(JumpAnimation):
    def __init__(self):
        self._none_transition = IdleLeftAnimation
        super(JumpFacingLeftAnimation, self).__init__(True)


class PunchRightAnimation(BaseAnimation):
    '''
    Punch animation while facing right.
    '''
    def __init__(self):
        self._none_transition = IdleRightAnimation
        super(PunchRightAnimation, self).__init__()
        frames = util.load_frame_sequence(util.find_datadir(), 'punch', 3)
        self.__frames__ = list(util.repeat_each(frames, [8, 6, 8]))


    def __transitions__(self):
        t = dict(super(PunchRightAnimation, self).__transitions__())
        del t['punch_right']
        return t


class PunchLeftAnimation(BaseAnimation):
    '''
    Punch animation while facing left.
    '''
    def __init__(self):
        self._none_transition = IdleLeftAnimation
        super(PunchLeftAnimation, self).__init__()
        frames = util.load_frame_sequence(util.find_datadir(), 'punch', 3)
        frames = map(util.flip_frame, frames)
        self.__frames__ = list(util.repeat_each(frames, [8, 6, 8]))


    def __transitions__(self):
        t = dict(super(PunchLeftAnimation, self).__transitions__())
        del t['punch_left']
        return t


