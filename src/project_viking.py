from __future__ import print_function, absolute_import

import itertools
import math
import os
import time
import sys

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

    tick_event = pygame.event.Event(constants.TICK)
    datadir = find_datadir()
    loader = pyglet.resource.Loader(datadir)

    player1 = viking(datadir, clock, keyboard, pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_j)
    player2 = viking(datadir, clock, keyboard, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_RETURN)
    player2.location[0] = 900

    entities = [player1, player2]
    scream = pygame.mixer.Sound(os.path.join(datadir, 'wilhelm.wav'))
    background = pygame.image.load(os.path.join(datadir, 'background.png'))
    background_texid = texture_from_image(background, gl.GL_RGBA8)
    if level_file is None:
        walls = [components.hitbox((-5, -5), (10, 610)),
                 components.hitbox((995, -5), (10, 610)),
                 components.hitbox((-5, 595), (1010, 5)),]
    else:
        pass

    # initialize static vertex data

    debug_draw = False
    pause = False
    do_frame = False
    while True:
        start = time.clock()

        key_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                key_events.append(event)

            if event.type == pygame.KEYDOWN:
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
            while attempts < 20 and resolutions != 0:
                resolutions = collisions.resolve_passive_passive_collisions(entities)
                collisions.resolve_wall_collisions(entities, walls)
                attempts += 1

            for thing in entities:
                thing.location += thing.motion.v

            do_frame = False

        dead = []

        gl.glBindTexture(gl.GL_TEXTURE_2D, background_texid)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        vertices = numpy.array((0, 0, 0, 600, 1000, 600, 1000, 0), dtype=numpy.float32)
        texcoords = numpy.array((0, 0, 0, 1, 1, 1, 1, 0), dtype=numpy.float32)
        #gl.glColor3f(0.8, 0.5, 0.2)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, vertices.ctypes.data)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, texcoords.ctypes.data)
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)
        for thing in entities:
            if thing.hitpoints <= 0 or thing.location[1] > 10000:
                dead.append(thing)
                continue
            #screen.blit(thing.graphics.sprite, map(math.trunc, thing.location + thing.graphics.anchor))
            if debug_draw:
                pass
            #screen.fill((227, 227, 227), pygame.Rect(thing.location + thing.hitbox_passive.point, thing.hitbox_passive.size))
            #screen.fill((255, 100, 100), pygame.Rect(thing.location + thing.hitbox_active.point, thing.hitbox_active.size))
            #screen.fill((100, 255, 255), pygame.Rect(thing.location[0] - 3, thing.location[1] - 3, 6, 6))
            #screen.fill((100, 100, 255), pygame.Rect(thing.location, (1, 1)))

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

        #screen.fill((120, 50, 50), pygame.Rect(0, 10, player1.hitpoints * 2, 10))
        #screen.fill((120, 50, 50), pygame.Rect(1000 - player2.hitpoints * 2, 10, player2.hitpoints * 2, 10))

        pygame.display.flip()

        delta = time.clock() - start
        if delta < constants.FRAME:
            time.sleep(constants.FRAME - delta)

if __name__ == '__main__':
    main(None)


