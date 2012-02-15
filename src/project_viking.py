# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import itertools
import math
import os
import time
import sys
import random
import numpy
import pygame
import pyglet
import pyglet.gl
from pyglet import gl

import components
import controls
import events
import physics
import level
from util import *
from entities import drake, floaty_sheep, sheep, viking, shaders
import collisions
import constants


def handle_resize(w, h):
    screen = pygame.display.set_mode((w, h), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    gl.glViewport(0, 0, w, h)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, w, h, 0, 0, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    return screen


def main(level_file):
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

    screen = handle_resize(1000, 600)
    screen_center = (500, 300)
    camera_offset = 130
    gl.glEnable(gl.GL_TEXTURE_2D)

    gl.glEnable(gl.GL_BLEND)
    gl.glBlendEquation(gl.GL_FUNC_ADD)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glClearColor(0, 0, 0, 1)

    tick_event = pygame.event.Event(constants.TICK)
    datadir = find_datadir()
    loader = pyglet.resource.Loader(datadir)

    player1 = viking(datadir, clock, keyboard,
                     pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_j)
    player2 = viking(datadir, clock, keyboard,
                     pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_RETURN)
    player2.location[0] = 900

    entities = [player1, player2]
    scream = pygame.mixer.Sound(os.path.join(datadir, 'wilhelm.wav'))
    background = load_sprite(datadir, 'background')
    backgroundbuf = GLBuffer(4 * 4, numpy.float32, gl.GL_STATIC_DRAW)
    backgroundbuf[:] = background.xyuv
    if level_file is None:
        walls = [components.hitbox((-5, -5), (10, 610)),
                 components.hitbox((995, -5), (10, 610)),
                 components.hitbox((-5, 595), (1010, 5)), ]
    else:
        walls = level.load(level_file)

    # vertex positions for walls
    quads = numpy.empty((len(walls), 4, 2), dtype=numpy.float32)
    quads[:, 0, :] = [w.point for w in walls]
    quads[:, 2, :] = [w.size for w in walls]
    quads[:, 2, :] += quads[:, 0, :]
    quads[:, 1, 0] = quads[:, 0, 0]
    quads[:, 1, 1] = quads[:, 2, 1]
    quads[:, 3, 0] = quads[:, 2, 0]
    quads[:, 3, 1] = quads[:, 0, 1]
    wallbuf = GLBuffer(quads.size, numpy.float32, gl.GL_STATIC_DRAW)
    wallbuf[:] = quads
    del quads

    # contains vertex and texture positions for sprites
    entitybuf = GLBuffer(dtype=numpy.float32)

    # walls program
    wallprog = shaders.wall()

    spriteprog = shaders.sprite()

    dragonprog = shaders.psycho()
    dragonpalette = load_texture(os.path.join(datadir, 'wallpalette.png'), dimensions=1)
    dragonsprite_scales = load_sprite(datadir, 'dragon_scales')
    dragonsprite_contours = load_sprite(datadir, 'dragon_contours')
    dragonbuf = GLBuffer(4 * 4, numpy.float32, gl.GL_STATIC_DRAW)
    dragonbuf[:] = dragonsprite_scales.xyuv
    contourbuf = GLBuffer(4 * 4, numpy.float32, gl.GL_STATIC_DRAW)
    contourbuf[:] = dragonsprite_contours.xyuv

    debug_draw = False
    pause = False
    do_frame = False
    ticks_done = 0
    while True:
        start = time.clock()

        key_events = []
        resize_event = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                key_events.append(event)
            elif event.type == pygame.VIDEORESIZE:
                resize_event = event

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 0
                if event.key == pygame.K_F2:
                    debug_draw = not debug_draw
                elif event.key == pygame.K_F3:
                    entities.append(sheep(datadir, clock))
                elif event.key == pygame.K_F4:
                    entities.append(drake(datadir, clock))
                elif event.key == pygame.K_F5:
                    entities.append(floaty_sheep(datadir, clock))
                elif event.key == pygame.K_p:
                    pause = not pause
                elif event.key == pygame.K_PERIOD and pause:
                    do_frame = True

        if resize_event:
            screen = handle_resize(resize_event.w, resize_event.h)
            screen_center = (resize_event.w // 2, resize_event.h // 2)
            background.xyuv[:, :2] = [[0, 0], [0, resize_event.h],
                                      [resize_event.w, resize_event.h], [resize_event.w, 0]]
            backgroundbuf[:] = background.xyuv

        if (not pause) or do_frame:
            for event in key_events:
                keyboard.dispatch(event)

            for thing in entities:
                thing.motion.a[:] = (0, constants.G)

            clock.dispatch(tick_event)

            for thing in entities:
                thing.tags.discard('grounded')
                thing.motion.v += thing.motion.a

            collisions.resolve_passive_active_collisions(entities)

            attempts = 0
            resolutions = 1
            rppc = collisions.resolve_passive_passive_collisions
            rwc = collisions.resolve_wall_collisions
            while attempts < 20 and resolutions != 0:
                rwc(entities, walls)
                resolutions = rppc(entities)
                attempts += 1

            for thing in entities:
                thing.location += thing.motion.v
                numpy.round(thing.location, out=thing.location)

            do_frame = False
            ticks_done += 1

        dead = []

        gl.glLoadIdentity()
        gl.glEnableVertexAttribArray(0)
        gl.glUseProgram(spriteprog.id)
        gl.glBindTexture(gl.GL_TEXTURE_2D, background.texid)
        spriteprog['texture'] = 0

        with backgroundbuf.bound:
            gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)

        # Now move camera
        gl.glTranslated(screen_center[0] - entities[0].location[0],
                        screen_center[1] - entities[0].location[1] + camera_offset, 0.0)

        for thing in entities:
            if thing.hitpoints <= 0 or thing.location[1] > 10000:
                dead.append(thing)
                continue

        for thing in dead:
            scream.play()
            if thing.name == 'Player':
                thing.hitpoints = 100
                thing.location[:] = (500, -10)
                thing.motion.v[:] = 0
                if thing.physics is not None:
                    thing.physics.last_position[:] = thing.location
            else:
                entities.remove(thing)

        xyuv = numpy.empty((4, 4), dtype=numpy.float32)
        texid = [0] * len(entities)
        with entitybuf.bound:
            for n, thing in enumerate(entities):
                xyuv[:] = thing.graphics.sprite.xyuv
                xy = xyuv[:, 0:2]
                xy[:] += thing.graphics.anchor
                xy[:] += thing.location
                offset = n * 16
                entitybuf[offset:] = xyuv
                texid[n] = thing.graphics.sprite.texid
                #print('Loaded data for entity', n, xyuv, 'texid', texid[n])

            gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)

            for n, t in enumerate(texid):
                gl.glBindTexture(gl.GL_TEXTURE_2D, t)
                gl.glDrawArrays(gl.GL_TRIANGLE_FAN, n * 4, 4)

        # draw walls
        gl.glUseProgram(wallprog.id)
        with wallbuf.bound:
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glDrawArrays(gl.GL_QUADS, 0, len(walls) * 8)

        # draw some shaders
        gl.glUseProgram(dragonprog.id)
        gl.glBindTexture(gl.GL_TEXTURE_2D, dragonsprite_scales.texid)
        gl.glActiveTexture(gl.GL_TEXTURE0 + 1)
        gl.glBindTexture(gl.GL_TEXTURE_1D, dragonpalette)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        dragonprog['texture'] = 0
        dragonprog['palette'] = 1
        dragonprog['perturb'] = (ticks_done % 1024) / 128
        dragonprog['shift'] = ticks_done / 600
        gl.glTranslated(-100, 145, 0)
        with dragonbuf.bound:
            gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)
        
        # now draw the rest of the fuckin' dragon
        gl.glUseProgram(spriteprog.id)
        gl.glBindTexture(gl.GL_TEXTURE_2D, dragonsprite_contours.texid)
        spriteprog['texture'] = 0
        with contourbuf.bound:
            gl.glVertexAttribPointer(0, 4, gl.GL_FLOAT, gl.GL_FALSE, 0, 0)
            gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)

        if debug_draw:
            gl.glUseProgram(0)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glColor3f(0.89, 0.89, 0.89)
            quads = numpy.zeros((len(entities), 4, 2), dtype=numpy.float32)
            quads[:, 0, :] = [thing.location + thing.hitbox_passive.point
                            for thing in entities]
            quads[:, 2, :] = [thing.hitbox_passive.size for thing in entities]
            quads[:, 2, :] += quads[:, 0, :]
            quads[:, 1, 0] = quads[:, 0, 0]
            quads[:, 1, 1] = quads[:, 2, 1]
            quads[:, 3, 0] = quads[:, 2, 0]
            quads[:, 3, 1] = quads[:, 0, 1]
            gl.glVertexPointer(2, gl.GL_FLOAT, 0, quads.ctypes.data)
            gl.glDrawArrays(gl.GL_QUADS, 0, quads.size // 2)

        gl.glColor3f(1, 1, 1)
        gl.glEnable(gl.GL_TEXTURE_2D)

        #screen.fill((120, 50, 50), pygame.Rect(0, 10, player1.hitpoints * 2, 10))
        #screen.fill((120, 50, 50), pygame.Rect(1000 - player2.hitpoints * 2, 10, player2.hitpoints * 2, 10))

        pygame.display.flip()

        delta = time.clock() - start
        if delta < constants.FRAME:
            time.sleep(constants.FRAME - delta)

if __name__ == '__main__':
    # ask for a level file...
    import sys
    from Tkinter import Tk
    from tkFileDialog import askopenfilename
    level_file = None
    if len(sys.argv) == 2:
        level_file = sys.argv[1]
    else:
        Tk().withdraw()
        level_file = askopenfilename(filetypes=('Level {.level}',))
        if level_file == '':
            level_file = None
    main(level_file)
    pygame.quit()
