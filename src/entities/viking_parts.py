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
