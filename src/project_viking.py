from __future__ import print_function, absolute_import
import time
import numpy
import pygame
from pygame.locals import *
import events
import components
from constants import *
from collections import defaultdict
from util import arrayify, find_datadir
FRAME = 0.02
# g = 980 cm/s**2;
G = 4000.0 * (FRAME**2)

class physics:
    '''
    A collection of ordered physics modifiers on an entity.
    On the start of each tick, the entity's acceleration is zeroed.
    A few standard constants are added for prioritising the modifiers.
    Modifiers are applied starting with the ones with lowest number,
    to the ones with highest number.
    Add all things that modify acceleration first,
    then a velocity-from-acceleration calculator,
    then all things that work with velocity,
    then a location-from-velocity calculator,
    then everything which limits movement.
    The modifiers are applied on each clock tick.
    '''
    GROUP_ACCELERATION = 10
    GROUP_VELOCITY = 20
    GROUP_LOCATION = 30
    GROUP_LAST = 40
     
    def __init__(self, entity):
        '''
        entity - the entity to act upon
        '''
        self.modifiers = defaultdict(list)
        self.entity = entity
        self.entity.clock.add(self.on_tick)
        assert(self.entity.physics is None)
        self.entity.physics = self
        self.last_position = numpy.array(self.entity.location.point)

    def add(self, modifier, priority):
        self.modifiers[priority].append(modifier)

    def remove(self, modifier, priority=None):
        '''
        If priority is not given, remove the modifier from all groups.
        If the modifier is not present in the given group, this is a no-op
        '''
        if priority is None:
            for priority in self.modifiers.iterkeys():
                self.remove(modifier, priority)
        else:
            try:
                self.modifiers[priority].remove(modifier)
            except ValueError:
                pass

    def on_tick(self, event):
        if event.type != TICK: return self.on_tick
        # Reset acceleration to 0 and velocity to the difference between the last two frames.
        self.entity.motion.a[:] = 0
        self.entity.motion.v[:] = self.entity.location.point - self.last_position
        self.last_position[:] = self.entity.location.point
        for priority in self.modifiers.iterkeys():
            for modifier in self.modifiers[priority]:
                modifier(self.entity)
        return self.on_tick

def ground_limiter(ground_level):
    '''
    Returns a function, that moves an entity's location, making its lower edge stay above the given horizontal line.
    '''
    def limiter(entity):
        if entity.location.point[1] + entity.location.size[1] >= ground_level:
            entity.tags.add('grounded')
            entity.location.point[1] = ground_level - entity.location.size[1]
        elif entity.location.point[1] + entity.location.size[1] < ground_level:
            if 'grounded' in entity.tags:
                entity.tags.remove('grounded')

    return limiter

def regular_physics(entity):
    '''
    Returns a physics object with added velocity and location calculators and affected by gravity.
    '''
    p = physics(entity)
    p.add(components.velocity_calculator, physics.GROUP_ACCELERATION + 1)
    p.add(components.location_calculator, physics.GROUP_VELOCITY + 1)
    p.add(gravity, physics.GROUP_ACCELERATION)
    return p

def gravity(entity):
    entity.motion.a[1] += G

class move_while_key_pressed:
    '''
    Accelerates the entity along the given acceleration vector for some frames,
    then decelerates it when the key is released.
    '''
    def __init__(self, entity, key, vector, frames=0):
        '''
        Adds self to the entity's keyboard event dispatcher.
        Adds self to the entity's physics, in the ACCELERATION_GROUP
        If frames is 0, the acceleration is applied until the key is released.
        '''
        self.entity, self.key = entity, key
        self.entity.physics.add(self.on_physics, physics.GROUP_VELOCITY)
        self.entity.keyboard.add(self.on_key)
        self.frames = frames
        self.tick = 0
        self.state = self.state_none
        assert frames != 0, 'omgwtf'
        self.vectors = numpy.zeros((frames + 1, 2))
        self.vectors += arrayify(vector)
        self.vectors *= [[x, x] for x in range(0, frames + 1)]

    def state_none(self):
        return self.state_none

    def state_accelerate(self):
        self.entity.motion.v[:] -= self.vectors[self.tick]
        self.tick += 1
        if self.tick >= self.frames and self.frames != 0:
            self.tick = self.frames - 1
        self.entity.motion.v[:] += self.vectors[self.tick]
        return self.state_accelerate

    def state_decelerate(self):
        self.entity.motion.v[:] -= self.vectors[self.tick]
        self.tick -= 1
        if self.tick <= 0:
            self.tick = 0
        self.entity.motion.v[:] += self.vectors[self.tick]
        return self.state_decelerate

    def on_physics(self, entity):
        self.state = self.state()

    def on_key(self, event):
        if event.key != self.key:
            return self.on_key
        if event.type == KEYDOWN:
            self.state = self.state_accelerate
        elif event.type == KEYUP:
            self.state = self.state_decelerate
        return self.on_key
        
class jump_when_key_pressed:
    '''
    Accelerates the entity along the given acceleration vector for some frames.
    '''
    def __init__(self, entity, key, vector, frames=0):
        '''
        Adds self to the entity's keyboard event dispatcher.
        Adds self to the entity's physics, in the ACCELERATION_GROUP
        If frames is 0, the acceleration is applied until the key is released.
        '''
        self.entity, self.key, self.a = entity, key, arrayify(vector)
        self.entity.physics.add(self.on_physics, physics.GROUP_ACCELERATION)
        self.entity.keyboard.add(self.on_key)
        self.frames = frames
        self.tick = 0
        self.state = self.state_none

    def state_none(self):
        if self.tick > 0:
            self.tick -= 1
        return self.state_none

    def state_accelerate(self):
        self.entity.motion.a += self.a
        self.tick += 1
        if self.tick >= self.frames and self.frames != 0:
            return self.state_none
        else:
            return self.state_accelerate

    def on_physics(self, entity):
        self.state = self.state()

    def on_key(self, event):
        if event.key != self.key:
            return self.on_key
        if event.type == KEYDOWN and 'grounded' in self.entity.tags:
            self.state = self.state_accelerate
        elif event.type == KEYUP:
            self.state = self.state_none
        return self.on_key

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    pygame.init()
    screen = pygame.display.set_mode((1000, 600))
    tick_event = pygame.event.Event(TICK)

    player = components.entity('Player', clock, keyboard,
                               location=components.location((0, 0), (50, 100)),
                               motion=components.motion(),
                               graphics=components.graphics(None))
    regular_physics(player)
    player.physics.add(ground_limiter(400), physics.GROUP_LOCATION)
    # movement left/right
    move_while_key_pressed(player, K_RIGHT, (0.5, 0), 50)
    move_while_key_pressed(player, K_LEFT, (-0.5, 0), 50)
    # jumping
    jump_when_key_pressed(player, K_UP, (0, -3.0), 10)

    while True:
        start = time.clock()

        clock.dispatch(tick_event)

        for event in pygame.event.get():
            if event.type == QUIT:
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)

        screen.fill((0, 0, 0))
        screen.fill((200, 200, 150), pygame.Rect(player.location.point, player.location.size))
        pygame.display.flip()

        delta = time.clock() - start
        if delta < FRAME:
            time.sleep(FRAME - delta)

if __name__ == '__main__':
    main()


