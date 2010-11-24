from __future__ import print_function, absolute_import
import pygame
from pygame.locals import *
import math
import Queue
import os
import time
import config

class icon_cache:
    def __init__(self, folder):
        '''
        Loads icons and caches their rotated transforms.
        folder - name of the folder containing the icons.
        '''
        self.icons = {}
        self.folder = folder

    def __getitem__(self, name_angle):
        name, angle = name_angle
        angle = math.trunc(angle / 5.0) * 5
        if name_angle in self.icons:
            return self.icons[name_angle]
        elif (name, 0) in self.icons:
            icon = pygame.transform.rotate(self.icons[name, 0], angle).convert()
            self.icons[name, angle] = icon
            return icon
        else:
            filename = os.path.join(self.folder, "%s.bmp" % name)
            surface = pygame.image.load(filename)
            surface.set_colorkey((0xf3,0x0a,0x0a))
            self.icons[name, 0] = surface.convert()
            return self[name, angle]

class world:
    def __init__(self):
        self.prev_state = {}
        self.state = {}
        self.icons = icon_cache('data')

    def set_state(self, state):
        print('actors:', len(state['actors']))
        self.state = state

    def draw(self, surface, timestamp):
        surface.fill((200, 200, 200))
        for obj in self.state['actors']:
            image = self.icons[obj.name, 270.0 - obj.angle]
            surface.blit(image, obj.location)

def run(queue_in, queue_out):
    '''
    Run the main audio/video/interface event loop.
    queue_in/put - inbound/outbound Queue to
    communicate over with the rest of the application.
    '''
    pygame.init()
    window = pygame.display.set_mode(config.resolution)
    pygame.display.set_caption("Actor Demo")
    arena = world()
    screen = pygame.display.get_surface()
    sleep_time = 5/1000.0

    while True:
        updated = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                queue_out.put(('QUIT', 0), block=False)
                return 0

        try:
            while not queue_in.empty():
                msg = queue_in.get(False)
                if msg[0] == 'WORLD_STATE':
                    arena.set_state(msg[1])
                    updated = True
                    sleep_time = msg[1]['frame_time'] / 2000.0
        except Queue.Empty:
            pass

        if updated and config.DRAW:
            arena.draw(screen, 0)
            pygame.display.flip()
        else:
            time.sleep(sleep_time)

