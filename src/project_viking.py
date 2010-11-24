from __future__ import print_function, absolute_import
import time
import numpy
import pygame
from pygame.locals import *
import events
import components
from constants import *

class accelerate_on_keypress:
    def __init__(self, entity, key, acceleration, frames=1):
        '''
        Accelerates the entity along the given acceleration vector for frames, or until key is released.
        If frames is 0, do not stop accelerating, before key release.
        acceleration must be a sequence of 2 numbers - the x and y axis acceleration to apply.
        The given entity must have a physics component.
        '''
        self.entity = entity
        self.entity.keyboard.add(self.on_key)
        self.key, self.acceleration, self.frames = key, numpy.array(acceleration), frames
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
            self.entity.motion.a += self.acceleration
            self.current_frame += 1
            if self.current_frame == self.frames:
                self.active = False
        return self.on_tick

class repulsor:
    '''
    Repulses the actor from the given wall (line).
    The formula used is normal * strength/distance, where distance
    is the distance of the actor from the wall. If distance <= 0, nothing is applied.
    '''
    def __init__(self, entity, coords, normal, strength):
        self.entity = entity
        self.coords, self.normal, self.strength = numpy.array(coords), numpy.array(normal), strength
        self.normal /= numpy.sqrt(numpy.dot(self.normal, self.normal))
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        if event.type != TICK:
            return self.on_tick
        print('omgwtf')

        d = numpy.dot(self.normal, self.entity.location - self.coords)
        if d > 0:
            self.entity.motion.a += self.normal * self.strength / d
        return self.on_tick

class attractor:
    '''
    Attracts the entity, according to the law of gravity.
    '''
    def __init__(self, entity, location, strength):
        '''
        location - a sequence of 2 numbers - the coordinates of the centre of mass.
        strength - used in calculating attraction. The formula used is:
            F = strength / distance ** 2
        '''
        self.entity = entity
        self.location = numpy.array(location)
        self.strength = strength
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        v = self.location - self.entity.location
        self.entity.motion.a += (v * self.strength) / (numpy.dot(v, v) ** 1.5)
        return self.on_tick

class location_clamper:
    '''
    Keeps the entity's location within the given boundaries.
    '''
    def __init__(self, entity, min, max):
        self.entity = entity
        self.min, self.max = numpy.array(min), numpy.array(max)
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        numpy.clip(self.entity.location, self.min, self.max, self.entity.location)
        return self.on_tick

class location_warper:
    def __init__(self, entity, min, max):
        self.entity = entity
        self.min, self.max = numpy.array(min), numpy.array(max)
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        for i, v, min, max in zip((0, 1), self.entity.location, self.min, self.max):
            if v < min:
                self.entity.location[i] = max - min + v
            elif v >= max:
                self.entity.location[i] = min + v - max
        return self.on_tick

class court_order:
    '''
    Keeps the entity at least distance away from the given point.
    '''
    def __init__(self, entity, location, distance):
        self.entity = entity
        self.location = numpy.array(location)
        self.distance = distance
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        v = self.entity.location - self.location
        d = numpy.sqrt(numpy.dot(v, v))
        if d < self.distance:
            v /= d
            self.entity.location += v * (self.distance - d)
            self.entity.motion.v -= v * numpy.dot(self.entity.motion.v, v)
        return self.on_tick

class velocity_updater:
    '''
    Updates the entity's velocity, according to acceleration.
    '''
    def __init__(self, entity):
        self.entity = entity
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        self.entity.motion.update_velocity()
        self.entity.motion.a = [0, 0]
        return self.on_tick

class location_updater:
    '''
    Moves the entity, according to velocity.
    '''
    def __init__(self, entity):
        self.entity = entity
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        self.entity.location = self.entity.location + self.entity.motion.v
        return self.on_tick

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    rect = components.entity('Red Rect', clock,
                             location=(300, 100),
                             motion=components.motion(velocity=(3,-0.5)),
                             graphics=components.graphics((255, 0, 0), (20, 20)))
    player = components.entity('White Rect', clock, keyboard,
                               location=(0, 0),
                               motion=components.motion([0, 0], [0, 0]),
                               graphics=components.graphics((128, 128, 128), (10, 10)))
    accelerate_on_keypress(player, K_UP, (0, -0.25), frames=0)
    accelerate_on_keypress(player, K_DOWN, (0, 0.25), frames=0)
    accelerate_on_keypress(player, K_LEFT, (-0.25, 0), frames=0)
    accelerate_on_keypress(player, K_RIGHT, (0.25, 0), frames=0)
    attractor(rect, (300, 300), 5000)
    attractor(player, (300, 300), 5000)
    velocity_updater(rect)
    velocity_updater(player)
    court_order(rect, (300, 300), 50)
    court_order(player, (300, 300), 50)
    location_updater(rect)
    location_updater(player)
    location_clamper(rect, (0, 0), (600, 600))
    location_clamper(player, (0, 0), (600, 600))
    things = [rect, player]
    frame_time = 0.02
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
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
        for thing in things:
            if thing.graphics is not None and thing.location is not None:
                screen.fill(thing.graphics.color, pygame.Rect(thing.location[0] - thing.graphics.size[0] / 2,
                                                              thing.location[1] - thing.graphics.size[1] / 2,
                                                              thing.graphics.size[0],
                                                              thing.graphics.size[1]))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < frame_time:
            time.sleep(frame_time - delta)

if __name__ == '__main__':
    main()


