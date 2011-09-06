# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement


import util
import animatorium
import controls
import constants


WALK_SPEED = 5
JUMP_SPEED = -(constants.G + 1.6)
JUMP_TICKS = 12


class IdleRight(controls.BaseActionState):
    """Right-facing idle."""
    def __init__(self):
        super(IdleRight, self).__init__('idle_right')


    def on_tick(self, entity):
        pass


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_press': WalkLeft,
                'up_press': JumpFacingRight}


class IdleLeft(controls.BaseActionState):
    """Left-facing idle."""
    def __init__(self):
        super(IdleLeft, self).__init__('idle_left')


    def on_tick(self, entity):
        pass


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_press': WalkLeft,
                'up_press': JumpFacingLeft}


class WalkRight(controls.BaseActionState):
    """Right-facing walk."""
    def __init__(self):
        super(WalkRight, self).__init__('walk_right')


    def on_tick(self, entity):
        entity.motion.a[0] += WALK_SPEED


    def __transitions__(self):
        return {'right_release': IdleRight,
                'left_press': WalkLeft,
                'up_press': JumpRight}


class WalkLeft(controls.BaseActionState):
    """Left-facing walk."""
    def __init__(self):
        super(WalkLeft, self).__init__('walk_left')


    def on_tick(self, entity):
        entity.motion.a[0] -= WALK_SPEED


    def __transitions__(self):
        return {'right_press': WalkRight,
                'left_release': IdleLeft,
                'up_press': JumpLeft}


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
            return self.next('up_release')

        entity.motion.a += (WALK_SPEED, JUMP_SPEED)
        self.ticks += 1


    def __transitions__(self):
        return {'up_release': WalkRight,
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
            return self.next('up_release')

        entity.motion.a += (-WALK_SPEED, JUMP_SPEED)
        self.ticks += 1


    def __transitions__(self):
        return {'up_release': WalkLeft,
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
            return self.next('up_release')

        entity.motion.a[1] += JUMP_SPEED
        self.ticks += 1


    def __transitions__(self):
        return {'up_release': IdleRight,
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
            return self.next('up_release')

        entity.motion.a[1] += JUMP_SPEED
        self.ticks += 1


    def __transitions__(self):
        return {'up_release': IdleLeft,
                'left_press': WalkLeft,
                'right_press': WalkRight}


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
                'jump_facing_left': JumpFacingLeftAnimation,}


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


class DummyAnimation(animatorium.BaseAnimationState):
    '''just iterates a single frame'''
    def __init__(self):
        self.frame = util.load_frame(util.find_datadir(), 'model')


    def __iter__(self):
        while True:
            yield self.frame


    def next(self, event):
        return self


def viking(datadir, clock, keyboard, key_left, key_right, key_jump, key_punch):
    idle_right = load_frame(datadir, 'model')
    idle_left = flip_frame(idle_right)

    punch_frames_right = load_frame_sequence(datadir, 'punch', 3)
    punch_frames_left = map(flip_frame, punch_frames_right)
    punch_frames_right = [idle_right] + punch_frames_right
    punch_frames_left = [idle_left] + punch_frames_left
    punch_delays = [2, 8, 6, 8, 2]
    punch_frames_right = list(repeat_each(punch_frames_right, punch_delays))
    punch_frames_left = list(repeat_each(punch_frames_left, punch_delays))

    run_frames_right = load_frame_sequence(datadir, 'run', 6)
    run_frames_left = map(flip_frame, run_frames_right)
    run_delays = [5] * 6
    run_frames_right = list(repeat_each(run_frames_right, run_delays))
    run_frames_left = list(repeat_each(run_frames_left, run_delays))

    jump_frames_right = load_frame_sequence(datadir, 'jump', 4)
    jump_frames_left = map(flip_frame, jump_frames_right)
    jump_delays = [3, 15, 18, 20]
    jump_frames_right = list(repeat_each(jump_frames_right, jump_delays))
    jump_frames_left = list(repeat_each(jump_frames_left, jump_delays))

    player = components.entity('Player', clock, keyboard,
                               location=(100, 0),
                               motion=components.motion(),
                               hitbox_passive=idle_right['hbp'],
                               hitbox_active=idle_right['hba'],
                               graphics=components.graphics(idle_right['sprite'], idle_right['sp']))
    physics.regular_physics(player)
    player.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    player.physics.add(physics.speed_limiter((10, 10000)), components.physics.GROUP_VELOCITY)

    # movement left/right
    idle_right_state = controls.looped_animation(player, [idle_right], (0, 0))
    idle_left_state = controls.looped_animation(player, [idle_left], (0, 0))

    walk_right_state = controls.loop_while_keydown(player, run_frames_right, (5, 0), key_right, idle_right_state)
    walk_left_state = controls.loop_while_keydown(player, run_frames_left, (-5, 0), key_left, idle_left_state)

    jump_right_state = controls.animation_while_keydown(player, jump_frames_right, key_jump, idle_right_state)
    jump_left_state = controls.animation_while_keydown(player, jump_frames_left, key_jump, idle_left_state)

    jump_right_walk_state = controls.animation_while_keydown(player, jump_frames_right, key_jump, walk_right_state)
    jump_left_walk_state = controls.animation_while_keydown(player, jump_frames_left, key_jump, walk_left_state)

    punch_right_state = controls.animation(player, punch_frames_right, idle_right_state)
    punch_left_state = controls.animation(player, punch_frames_left, idle_left_state)

    idle_right_state.transitions[key_left] = walk_left_state
    idle_right_state.transitions[key_right] = walk_right_state
    idle_right_state.transitions[key_punch] = punch_right_state
    idle_right_state.transitions[key_jump] = jump_right_state

    idle_left_state.transitions[key_left] = walk_left_state
    idle_left_state.transitions[key_right] = walk_right_state
    idle_left_state.transitions[key_punch] = punch_left_state
    idle_left_state.transitions[key_jump] = jump_left_state

    walk_right_state.transitions[key_left] = walk_left_state
    walk_right_state.transitions[key_punch] = punch_right_state
    walk_right_state.transitions[key_jump] = jump_right_walk_state

    walk_left_state.transitions[key_right] = walk_right_state
    walk_left_state.transitions[key_punch] = punch_left_state
    walk_left_state.transitions[key_jump] = jump_left_walk_state

    idle_right_state.start()
    # jumping
    controls.jump_when_key_pressed(player, key_jump, (0, -G - 1.6), 12)
    return player
