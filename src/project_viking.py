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
from entities import drake, floaty_sheep, sheep, viking
import collisions
import constants


DIRT_VS_SRC = r'''
#version 120

varying vec2 p;
const vec2 scaling_factor = vec2(0.08, 0.12);

void main() {
    p = gl_Vertex.xy * scaling_factor;
    vec4 pos = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_Position = pos;
}
'''


DIRT_FS_SRC = r'''
#version 120

uniform sampler1D palette;

uniform float perturb = 0.0;

varying vec2 p;

const vec4 base_color = vec4(0.89, 0.0, 0.0, 1.0);
const vec4 white = vec4(1.0, 1.0, 1.0, 1.0);
const float xfactor = 0.06 / 0.04;
const int N = 8;

// linear
float poly1(float x) {
    return abs(x);
}

// quadratic
float poly2(float x) {
    return (x - 1.0) * (x + 1.0) + 1.0;
//    return x * (abs(x) -1.0) * 2.0 + 0.5;
}

// cubic
float poly3(float x) {
    float invmaxhalf = 0.5 / 0.5773502691896;
    float y = 0.5 + (x + 1) * x * (x - 1) * invmaxhalf;
    return y;
}

// return x within (-1, 1)
// for x = 0 returns 1.0
// for x = 0.5 returns 0
float roll(float x) {
    return (0.5 - fract(x)) * 2.0;
}

void main() {
    float p1 = 23.0, p2 = 11.0, p3 = 109.0, p4 = 41.0;
    float period = p1 * p2 * p3 * p4 / 2000.0;
    vec2 n[N];
    n[0] = vec2(0.5, 0.015);
    n[1] = vec2(0.5015, 0.05);
    n[2] = vec2(0.04, 0.5);
    n[3] = vec2(0.0325, 0.565);
    n[4] = vec2(0.003, 0.005);
    n[5] = vec2(0.008, 0.0015);
    n[6] = vec2(0.0, 0.0);
    n[7] = vec2(0.0, 0.0);

    float x[N];
    for (int i = 0; i < N; i++)
        x[i] = roll(dot(n[i], p));

    float y[N];
    float z[N];
    for (int i = 0; i < N; i++) {
        y[i] = poly1(x[i]);
    }

    //float x3 = roll(-0.714143 * p.x + 0.7 * p.y);
    //float x4 = roll(0.7 * p.x + 0.714143 * p.y);
    float a = (y[0] + y[1] + y[2] + y[3]) * 0.15 + y[4] * y[5] * 0.85;
    //a *= poly3(x[2]) * poly3(x[3]);
    gl_FragColor = texture1D(palette, fract(a + perturb));
}
'''


def main(level_file):
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)
    screen = pygame.display.set_mode((1000, 600), pygame.OPENGL | pygame.DOUBLEBUF)

    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glViewport(0, 0, 1000, 600);
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, 1000, 600, 0, 0, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

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
    if level_file is None:
        walls = [components.hitbox((-5, -5), (10, 610)),
                 components.hitbox((995, -5), (10, 610)),
                 components.hitbox((-5, 595), (1010, 5)),]
    else:
        walls = level.load(level_file)

    # vertex positions for walls
    quads = numpy.empty((len(walls), 4, 2), dtype=numpy.float32)
    quads[:,0,:] = [w.point for w in walls]
    quads[:,2,:] = [w.size for w in walls]
    quads[:,2,:] += quads[:,0,:]
    quads[:,1,0] = quads[:,0,0]
    quads[:,1,1] = quads[:,2,1]
    quads[:,3,0] = quads[:,2,0]
    quads[:,3,1] = quads[:,0,1]
    wallbuf = GLBuffer(quads.size, numpy.float32, gl.GL_STATIC_DRAW)
    wallbuf[:] = quads
    del quads

    # contains vertex and texture positions for sprites
    entitybuf = GLBuffer(dtype=numpy.float32)

    # walls program
    wallprog = program(vertex_shader(DIRT_VS_SRC),
                       fragment_shader(DIRT_FS_SRC))
    wallprog_palette = gl.glGetUniformLocation(wallprog, 'palette')
    wallprog_perturb = gl.glGetUniformLocation(wallprog, 'perturb')
    walltex = load_texture(os.path.join(datadir, 'wallpalette.png'), dimensions=1)

    debug_draw = False
    pause = False
    do_frame = False
    ticks_done = 0
    while True:
        start = time.clock()

        key_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                key_events.append(event)

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

        dead = []

        gl.glUseProgram(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glLoadIdentity()
        gl.glBindTexture(gl.GL_TEXTURE_2D, background.texid)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, background.quad.ctypes.data)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, background.texcoords.ctypes.data)
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)

        # Now move camera
        gl.glTranslated(500 - entities[0].location[0],
                        300 - entities[0].location[1], 0.0)

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

        vertices = numpy.empty((4, 2), dtype=numpy.float32)
        texcoords = numpy.empty((4, 2), dtype=numpy.float32)
        texid = [0] * len(entities)
        with entitybuf.bound:
            for n, thing in enumerate(entities):
                vertices[:] = thing.graphics.sprite.quad
                vertices += thing.graphics.anchor
                vertices += thing.location
                texcoords[:] = thing.graphics.sprite.texcoords
                voffset = n * 8
                toffset = len(entities) * 8 + n * 8
                entitybuf[voffset:] = vertices
                entitybuf[toffset:] = texcoords
                texid[n] = thing.graphics.sprite.texid

            gl.glVertexPointer(2, gl.GL_FLOAT, 0, 0)
            gl.glTexCoordPointer(2, gl.GL_FLOAT, 0,
                                 len(entities) * 8 * entitybuf.dtype.itemsize)

            for n, t in enumerate(texid):
                gl.glBindTexture(gl.GL_TEXTURE_2D, t)
                gl.glDrawArrays(gl.GL_TRIANGLE_FAN, n * 4, 4)

        # draw walls
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glUseProgram(wallprog)
        gl.glBindTexture(gl.GL_TEXTURE_1D, walltex)
        gl.glUniform1i(wallprog_palette, 0)
        gl.glUniform1f(wallprog_perturb, (ticks_done % 1024) / 64)
        with wallbuf.bound:
            gl.glVertexPointer(2, gl.GL_FLOAT, 0, 0)
            gl.glDrawArrays(gl.GL_QUADS, 0, len(walls) * 8)
        gl.glUseProgram(0)

        if debug_draw:
            gl.glColor3f(0.89, 0.89, 0.89)
            quads = numpy.zeros((len(entities), 4, 2), dtype=numpy.float32)
            quads[:,0,:] = [thing.location + thing.hitbox_passive.point
                            for thing in entities]
            quads[:,2,:] = [thing.hitbox_passive.size for thing in entities]
            quads[:,2,:] += quads[:,0,:]
            quads[:,1,0] = quads[:,0,0]
            quads[:,1,1] = quads[:,2,1]
            quads[:,3,0] = quads[:,2,0]
            quads[:,3,1] = quads[:,0,1]
            gl.glVertexPointer(2, gl.GL_FLOAT, 0, quads.ctypes.data)
            gl.glDrawArrays(gl.GL_QUADS, 0, quads.size // 2)

        gl.glColor3f(1, 1, 1)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

        #screen.fill((120, 50, 50), pygame.Rect(0, 10, player1.hitpoints * 2, 10))
        #screen.fill((120, 50, 50), pygame.Rect(1000 - player2.hitpoints * 2, 10, player2.hitpoints * 2, 10))

        pygame.display.flip()

        delta = time.clock() - start
        if delta < constants.FRAME:
            time.sleep(constants.FRAME - delta)
        ticks_done += 1

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


