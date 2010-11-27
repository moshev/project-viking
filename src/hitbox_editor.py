from __future__ import print_function, absolute_import
import time
import os
import sys
import numpy
import math
import pygame
from pygame.locals import *
import events
import components
import controls
from constants import *
from collections import defaultdict
from util import arrayify, find_datadir
import cPickle as pickle

def load_points(imagefile):
    filename = os.path.splitext(imagefile)[0] + '.points'
    if os.path.exists(filename):
        data = file(filename, 'rb')
        try:
            points = pickle.load(data)
            data.close()
            return points
        except EOFError:
            data.close()

    return {'sp': numpy.array([200, 200]),
            'hba': components.hitbox((0, 0), (10, 10)),
            'hbp': components.hitbox((0, 0), (10, 10))}

def save_points(imagefile, sp, hbp, hba):
    filename = os.path.splitext(imagefile)[0] + '.points'
    points = {'sp': sp,
              'hba': hba,
              'hbp': hbp}
    data = file(filename, 'wb')
    points = pickle.dump(points, data, 2)
    data.close()

def main():
    if len(sys.argv) == 1:
        print('Usage:', sys.argv[0], 'image1 [image2...]')
        sys.exit(1)
    pygame.init()
    frames = [pygame.image.load(filename) for filename in sys.argv[1:]]
    points = [load_points(filename) for filename in sys.argv[1:]]
    frame = 0
    refpoint = numpy.array([600, 500])
    spritepoint = [x['sp'] for x in points]
    hitbox_passive = [x['hbp'] for x in points]
    hitbox_active = [x['hba'] for x in points]
    screen = pygame.display.set_mode((1000, 600))
    def mode_rp(event):
        if event.key == K_UP:
            refpoint[1] -= 1
        elif event.key == K_DOWN:
            refpoint[1] += 1
        elif event.key == K_LEFT:
            refpoint[0] -= 1
        elif event.key == K_RIGHT:
            refpoint[0] += 1
        elif event.key in modekeys:
            return modekeys[event.key]
        return mode_rp

    def mode_sp(event):
        if event.key == K_UP:
            spritepoint[frame][1] -= 1
        elif event.key == K_DOWN:
            spritepoint[frame][1] += 1
        elif event.key == K_LEFT:
            spritepoint[frame][0] -= 1
        elif event.key == K_RIGHT:
            spritepoint[frame][0] += 1
        elif event.key in modekeys:
            return modekeys[event.key]
        return mode_sp

    def mode_hba(event):
        if event.key == K_UP:
            if event.mod & KMOD_SHIFT:
                hitbox_active[frame].size[1] -= 1
            else:
                hitbox_active[frame].point[1] -= 1
        elif event.key == K_DOWN:
            if event.mod & KMOD_SHIFT:
                hitbox_active[frame].size[1] += 1
            else:
                hitbox_active[frame].point[1] += 1
        elif event.key == K_LEFT:
            if event.mod & KMOD_SHIFT:
                hitbox_active[frame].size[0] -= 1
            else:
                hitbox_active[frame].point[0] -= 1
        elif event.key == K_RIGHT:
            if event.mod & KMOD_SHIFT:
                hitbox_active[frame].size[0] += 1
            else:
                hitbox_active[frame].point[0] += 1
        elif event.key in modekeys:
            return modekeys[event.key]
        return mode_hba

    def mode_hbp(event):
        if event.key == K_UP:
            if event.mod & KMOD_SHIFT:
                hitbox_passive[frame].size[1] -= 1
            else:
                hitbox_passive[frame].point[1] -= 1
        elif event.key == K_DOWN:
            if event.mod & KMOD_SHIFT:
                hitbox_passive[frame].size[1] += 1
            else:
                hitbox_passive[frame].point[1] += 1
        elif event.key == K_LEFT:
            if event.mod & KMOD_SHIFT:
                hitbox_passive[frame].size[0] -= 1
            else:
                hitbox_passive[frame].point[0] -= 1
        elif event.key == K_RIGHT:
            if event.mod & KMOD_SHIFT:
                hitbox_passive[frame].size[0] += 1
            else:
                hitbox_passive[frame].point[0] += 1
        elif event.key in modekeys:
            return modekeys[event.key]
        return mode_hbp

    modekeys = {K_r: mode_rp,
                K_s: mode_sp,
                K_p: mode_hbp,
                K_a: mode_hba}
    mode = mode_sp

    last_key = None
    run = True
    boxes = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    frame += 1
                    if frame >= len(frames): frame = 0
                elif event.key == K_F1:
                    boxes = not boxes
                elif event.key == K_F2:
                    i = 0
                    for filename in sys.argv[1:]:
                        save_points(filename, spritepoint[i], hitbox_passive[i], hitbox_active[i])
                        i += 1
                    del i
                else:
                    last_key = event
            elif event.type == KEYUP:
                last_key = None

        if last_key is not None:
            mode = mode(last_key)

        screen.fill((0, 0, 0))
        screen.blit(frames[frame], tuple(refpoint + spritepoint[frame]))
        if boxes:
            screen.fill((227, 227, 227), pygame.Rect(refpoint + hitbox_passive[frame].point, hitbox_passive[frame].size))
            screen.fill((255, 100, 100), pygame.Rect(refpoint + hitbox_active[frame].point, hitbox_active[frame].size))
            screen.fill((100, 255, 255), pygame.Rect(refpoint[0] - 3, refpoint[1] - 3, 6, 6))
            screen.fill((100, 100, 255), pygame.Rect(refpoint, (1, 1)))
        pygame.display.flip()
        time.sleep(0.01)

if __name__ == '__main__':
    main()

