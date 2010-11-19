import pygame
from pygame.locals import *

def run(queue_in, queue_out):
    '''
    Run the main audio/video/interface event loop.
    queue_in/put - inbound/outbound Queue to
    communicate over with the rest of the application.
    '''
    pygame.init()
    window = pygame.display.set_mode((496,496))
    pygame.display.set_caption("Actor Demo")

