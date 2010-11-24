from __future__ import print_function, absolute_import
import time
import pygame
from pygame.locals import *

TICK=88

class event_dispatcher:
    def __init__(self, name=None):
        '''
        Creates a new event dispatcher.
        The optional name argument is for convenience - to let one tell handlers
        of the same class apart.
        '''
        self.name = name or self.__class__.__name__
        self.handlers = []

    def add(self, handler):
        '''
        Appends the given handler to the list of handlers.
        On dispatch, the handler will be called with the event object and the
        result will replace it in the list. If it returns None, it is removed
        from the list of handlers.
        '''
        self.handlers.append(handler)

    def dispatch(self, event):
        '''
        Calls each handler with the event object and replaces that handler
        in the list of handlers with the return value. If the handler
        returns None, it is removed.
        The event object must have a 'type' attribute set.
        '''
        self.handlers[:] = [new_handler
                            for new_handler in (handler(event) for handler in self.handlers)
                            if new_handler is not None]

class accelerate_on_keypress:
    def __init__(self, entity, key, acceleration, frames=1):
        '''
        Accelerates the entity along the given acceleration vector for frames, or until key is released.
        acceleration must be a sequence of 2 numbers - the x and y axis acceleration to apply.
        The given entity must have a physics component.
        '''
        self.entity = entity
        self.entity.keyboard.add(self.on_key)
        self.key, self.acceleration, self.frames = key, acceleration, frames
        self.active = False
        self.current_frame = 0

    def on_key(self, event):
        if event.key != self.key:
            return self.on_key
        if event.type == KEYDOWN and not self.active:
            self.active = True
            self.current_frame = 0
            self.entity.clock.add(self.on_tick)
        elif event.type == KEYUP and self.active:
            self.active = False
            self.current_frame = 0
        return self.on_key

    def on_tick(self, event):
        if event.type != TICK:
            return self.on_tick

        if not self.active:
            return None
        else:
            self.entity.motion.a[0] += self.acceleration[0]
            self.entity.motion.a[1] += self.acceleration[1]
            self.current_frame += 1
            if self.current_frame == self.frames:
                self.active = False
        return self.on_tick

class graphics:
    def __init__(self, color, size):
        '''
        color is a tuple of three integers in [0; 255]
        size is a tuple of two integers
        '''
        self.color, self.size = color, size

def rk4(y, dy):
    '''
    Calculates the next value for y, given the past derivatives of y, dys.
    y and dy must be sequences of the same length.
    y's elements must be numbers and dy's elements must be sequences of 4 numbers.
    Returns a list of numbers - the new values for y
    '''
    return list(x + (dx[0] + 2 * dx[1] + 2 * dx[2] + dx[3]) / 6 for x, dx in zip(y, dy))

class motion:
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = list(velocity), list(acceleration)
        self.past_a = [[0] * 4, [0] * 4]
        self.past_v = [[0] * 4, [0] * 4]

    def update_velocity(self):
        for a, b in zip(self.past_a, self.a):
            a[0:3] = a[1:4]
            a[3] = b
        self.v = rk4(self.v, self.past_a)
        for v, u in zip(self.past_v, self.v):
            v[0:3] = v[1:4]
            v[3] = u

class entity:
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None, location=None, motion=None, graphics=None):
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.location = location
        self.motion = motion
        self.graphics = graphics

def clamp(lo, hi):
    '''
    Returns a function that takes a number and returns that number clamped to [lo, hi], or:
    min(max(lo, n), hi)
    '''
    def clamper(n):
        return min(max(lo, n), hi)
    return clamper

def main():
    clock = event_dispatcher('Clock')
    keyboard = event_dispatcher('Keyboard')
    rect = entity('Red Rect', location=[100, 100], graphics=graphics((255, 0, 0), (20, 20)))
    player = entity('White Rect', clock, keyboard,
                    location=[0, 0],
                    motion=motion([0, 0], [0, 0]),
                    graphics=graphics((128, 128, 128), (10, 10)))
    accelerate_on_keypress(player, K_UP, (0, -0.25), frames=10)
    accelerate_on_keypress(player, K_DOWN, (0, 0.25), frames=10)
    accelerate_on_keypress(player, K_LEFT, (-0.25, 0), frames=10)
    accelerate_on_keypress(player, K_RIGHT, (0.25, 0), frames=10)
    things = [rect, player]
    frame_time = 0.02
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    tick_event = pygame.event.Event(TICK)
    while True:
        start = time.clock()
        for thing in things:
            if thing.motion:
                thing.motion.update_velocity()
                thing.location = map(clamp(0, 599), rk4(thing.location, thing.motion.past_v))
                thing.motion.a = [0, 0]

        clock.dispatch(tick_event)
        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)

        screen.fill((0, 0, 0))
        for thing in things:
            if thing.graphics and thing.location:
                screen.fill(thing.graphics.color, pygame.Rect(thing.location, thing.graphics.size))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < frame_time:
            time.sleep(frame_time - delta)

if __name__ == '__main__':
    main()


