from __future__ import print_function, absolute_import
import time
import numpy
import pygame
from pygame.locals import *
import events
import components
from constants import *

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    frame_time = 0.02
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)
    while True:
        start = time.clock()

        clock.dispatch(tick_event)

        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)

        screen.fill((0, 0, 0))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < frame_time:
            time.sleep(frame_time - delta)

if __name__ == '__main__':
    main()


