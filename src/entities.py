from __future__ import print_function, absolute_import
import components
import physics
from util import *
import controls
from constants import *


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


def drake(datadir, clock):
    drake_frame = load_frame(datadir, 'drake')
    drake = components.entity('Drake', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=200)
    drake.set_frame(drake_frame)
    physics.regular_physics(drake)
    drake.physics.add(physics.apply_friction(5), components.physics.GROUP_VELOCITY)
    return drake


def floaty_sheep(datadir, clock):
    sheep_frame = load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 400),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    components.physics(sheep)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep


def sheep(datadir, clock):
    sheep_frame = load_frame(datadir, 'sheep')
    sheep = components.entity('Sheep', clock, location=(500, 0),
                              motion=components.motion(),
                              graphics=components.graphics(None),
                              hitpoints=2)
    sheep.set_frame(sheep_frame)
    physics.regular_physics(sheep)
    sheep.physics.add(physics.apply_friction(0.5), components.physics.GROUP_VELOCITY)
    return sheep
