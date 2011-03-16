# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division
from time import time, sleep
import ctypes
import numpy
import pygame
from pygame.locals import *
import pyglet
pyglet.options['debug_gl'] = False
from pyglet.gl import *
import events
from constants import *
import components
import random
from util import arrayify

NPARTICLES = 20000

class sparse_array(object):
    def __init__(self, shape, dtype=numpy.float64, initial_capacity=16):
        if initial_capacity <= 0:
            raise ValueError('Initial capacity must be positive')
        self.shape=[initial_capacity] + list(shape)
        self.size = 0
        self.values = numpy.ones(self.shape, dtype)
        self.allocated = numpy.zeros(initial_capacity, numpy.bool)
        self.len = 0

    def add(self, vector):
        '''Adds a vector to the array and returns its index in the sparse array.
        If there is no free space, the storage space is grown twice.'''

        candidate = numpy.argmin(self.allocated)
        if self.allocated[candidate]:
            # allocate more space
            self.shape[0] *= 2
            try:
                self.values.resize(self.shape)
            except ValueError:
                print("fixme: Somebody has references to values of a sparse array.")
                self.values.resize(self.shape, False)
            try:
                self.allocated.resize(self.shape[0])
            except ValueError:
                print("fixme: Somebody has references to bitmap of a sparse array.")
                self.allocated.resize(self.shape, False)
            # now the next index is free and allocated
            candidate += 1
        self.values[candidate] = vector
        self.allocated[candidate] = True
        self.len += 1
        return candidate

    def release(self, idx):
        '''Marks a cell as free.
        idx is the number returned by the add method when adding a new vector.'''

        self.values[idx] = 1
        self.allocated[idx] = False
        self.len -= 1

    @property
    def v(self):
        '''Returns an array of all allocated vectors in this sparse array'''

        return self.values[self.allocated]

    def __len__(self):
        '''Returns the number of registered objects.'''

        return self.len

class physics(object):
    '''Holds the physics properties for all entities.
    Each entity has a location, velocity, mass and forces acting on it this frame.
    The intention is to accumulate all forces acting on each entity this frame
    and then call tick() to update the other values.'''

    def __init__(self):
        self.locations = sparse_array((2,))
        self.velocities = sparse_array((2,))
        self.forces = sparse_array((2,))
        self.masses = sparse_array((1,))

    def tick(self):
        numpy.divide(self.forces.values, self.masses.values, self.forces.values)
        numpy.add(self.velocities.values, self.forces.values, self.velocities.values)
        self.forces.values[:] = 0
        numpy.add(self.locations.values, self.velocities.values, self.locations.values)

    def add(self, location, velocity, force, mass):
        '''Adds a new entity's properties and returns an index to them.
        You should use the index to mark these properties as free after
        the entity doesn't exist anymore.'''

        idx_location = self.locations.add(location)
        idx_velocity = self.velocities.add(velocity)
        idx_force = self.forces.add(force)
        idx_mass = self.masses.add(mass)
        assert idx_location == idx_velocity == idx_force == idx_mass
        return idx_location

    def release(self, idx):
        '''Marks index as free.'''

        self.locations.release(idx)
        self.velocities.release(idx)
        self.forces.release(idx)
        self.masses.release(idx)

    def __len__(self):
        '''Returns the number of registered objects.'''

        return len(self.locations)

    @property
    def l(self):
        return self.locations.values

    @property
    def v(self):
        return self.velocities.values

    @property
    def f(self):
        return self.forces.values

    @property
    def m(self):
        return self.masses.values

def update_physics_on_tick(physics, clock):
    def on_tick(event):
        physics.tick()
        return on_tick

    clock.add(on_tick)

class physics_properties(object):
    '''Location, velocity, speed and mass'''

    def __init__(self, physics, location=(0, 0), velocity=(0, 0), force=(0, 0), mass=1):
        self.physics = physics
        self.idx = self.physics.add(location, velocity, force, mass)

    @property
    def location(self):
        return self.physics.locations.values[self.idx]

    @location.setter
    def location(self, location):
        self.physics.locations.values[self.idx][:] = location

    @property
    def velocity(self):
        return self.physics.velocities.values[self.idx]

    @velocity.setter
    def velocity(self, velocity):
        self.physics.velocities.values[self.idx][:] = velocity

    @property
    def force(self):
        return self.physics.forces.values[self.idx]

    @force.setter
    def force(self, force):
        self.physics.forces.values[self.idx][:] = force

    @property
    def mass(self):
        return self.physics.masses.values[self.idx]

    @mass.setter
    def mass(self, mass):
        self.physics.masses.values[self.idx][:] = mass

class graphics:
    def __init__(self, color, size):
        '''
        sprite is a pygame.surface or other blittable object.
        anchor is a tuple, giving the location of the object's
        upper-left corner inside the sprite.
        '''
        self.color = numpy.array(color, dtype=numpy.int8)
        self.size = arrayify(size)

class motion(object):
    def __init__(self, velocity=(0, 0), acceleration=(0, 0)):
        self.v, self.a = map(arrayify, (velocity, acceleration))

class entity(object):
    def __init__(self, name=None, clock=None, keyboard=None, mouse=None, physics=None, graphics=None):
        self.name = name or self.__class__.__name__
        self.clock = clock
        self.keyboard = keyboard
        self.mouse = mouse
        self.physics = physics
        self.graphics = graphics

class accelerate_on_keypress(object):
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
            self.entity.physics.force += self.acceleration
            self.current_frame += 1
            if self.current_frame == self.frames:
                self.active = False
        return self.on_tick

class repulsor(object):
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

class attractor(object):
    ''' Attracts all entities with the given physics, according to the law of gravity.  '''

    def __init__(self, clock, physics, location, strength):
        '''Initialise a new attractor.
        physics - the physics object containing all physics info on the entities.
        location - a sequence of 2 numbers - the coordinates of the centre of mass.
        strength - used in calculating attraction. The formula used is:
            F = strength / distance ** 2'''

        self.clock = clock
        self.physics = physics
        self.location = numpy.array(location)
        self.strength = strength
        self.clock.add(self.on_tick)

        # storage for computing the accelerations
        self.forces = numpy.zeros((len(self.physics.f), 2))

        # storage for computing dot products
        self.adot = numpy.zeros((len(self.physics.f), 2))

    def on_tick(self, event):
        if len(self.forces) != len(self.physics.f):
            self.forces = numpy.zeros((len(self.physics.f), 2))
            self.adot = numpy.zeros((len(self.physics.f), 2))

        # The formula is
        # a = d * K / r²
        # where d is the direction, K is a constant and r is the distance
        # In this case, it is
        # a = v * K / (v²)**1.5 where v is the vector from self.location to the location
        # of each entity and K is self.strength.
        # The value of (v²)**1.5 is accumulated in self.adots and the final result in self.forces
        self.forces[:] = self.location
        self.forces -= self.physics.l
        self.adot[:] = self.forces
        numpy.square(self.adot, self.adot)
        self.adot[:,0] += self.adot[:,1]
        self.adot[:,1] = self.adot[:,0]
        numpy.power(self.adot, 1.5, self.adot)
        self.forces *= self.strength
        self.forces /= self.adot
        result = self.physics.f
        result += self.forces
        return self.on_tick

class location_clamper(object):
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

class location_warper(object):
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

class court_order(object):
    '''
    Keeps the entity at least distance away from the given point.
    '''
    def __init__(self, entity, location, distance):
        self.entity = entity
        self.location = numpy.array(location, dtype=float)
        self.distance = distance
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        r = self.entity.location - self.location
        d = numpy.sqrt(numpy.dot(r, r))
        if d < self.distance:
            r /= d
            self.entity.location[:] = self.location + r * self.distance
        return self.on_tick

class velocity_updater(object):
    '''
    Updates the entity's velocity, according to acceleration.
    '''
    def __init__(self, entity):
        self.entity = entity
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        self.entity.motion.v += self.entity.motion.a
        return self.on_tick

class motion_cleaner(object):
    '''
    Sets the entity's acceleration to 0 and velocity according to last frame->this difference.
    '''
    def __init__(self, entity):
        self.entity = entity
        self.last_location = numpy.array(self.entity.location)
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        self.entity.motion.a[:] = 0.0
        self.entity.motion.v[:] = self.entity.location
        self.entity.motion.v -= self.last_location
        self.last_location[:] = self.entity.location
        return self.on_tick

class location_updater(object):
    '''
    Moves the entity, according to velocity.
    '''
    def __init__(self, entity):
        self.entity = entity
        self.entity.clock.add(self.on_tick)

    def on_tick(self, event):
        self.entity.location += self.entity.motion.v
        return self.on_tick

def rand_colour():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def rand_grey(lo, hi):
    grey = random.randint(lo, hi)
    return (grey, grey, grey)

def collision_check(c1, s1, c2, s2):
    return not (c2[0] - s2[0] > c1[0] + s1[0] or
                c2[0] + s2[0] < c1[0] - s1[0] or
                c2[1] - s2[1] > c1[1] + s1[1] or
                c2[1] + s2[1] < c1[1] - s1[1])

def main():
    clock = events.dispatcher('Clock')
    keyboard = events.dispatcher('Keyboard')
    phy = physics()
    rects = [entity('Rect', clock,
                    physics=physics_properties(phy,
                                               location=(180 + random.randint(0, 20),
                                                         60 + random.randint(0, 10)),
                                               velocity=(4 + random.random() * 2,
                                                         -random.random() - 0.5),
                                               mass = random.random() + 0.5),
                    graphics=graphics(rand_colour() , (5, 5)))
             for _ in range(NPARTICLES)]
    player = entity('White Rect', clock, keyboard,
                    physics=physics_properties(phy,
                                               location=(300, 60),
                                               velocity=(0, 0)),
                    graphics=graphics((227, 227, 227), (10, 10)))
    accelerate_on_keypress(player, K_UP, (0, -0.25), frames=0)
    accelerate_on_keypress(player, K_DOWN, (0, 0.25), frames=0)
    accelerate_on_keypress(player, K_LEFT, (-0.25, 0), frames=0)
    accelerate_on_keypress(player, K_RIGHT, (0.25, 0), frames=0)
    a1l = (240, 300)
    a2l = (360, 300)
    adist = 50
    astr = 4000
    aphy = physics()
    attractor1_centre = entity('A1',
                               physics=physics_properties(aphy, location=a1l),
                               graphics=graphics((128, 227, 80), (5, 5)))
    attractor2_centre = entity('A2',
                               physics=physics_properties(aphy, location=a2l),
                               graphics=graphics((128, 80, 227), (5, 5)))
    things = rects + [player]
    attractor(clock, phy, a1l, astr)
    attractor(clock, phy, a2l, astr)
    frame_time = 0.04
    pygame.init()
    screen = pygame.display.set_mode((600, 600), DOUBLEBUF | OPENGL)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glOrtho(0, 600, 600, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    tick_event = pygame.event.Event(TICK)
    drawables_indices = [i for thing, i in zip(things, range(len(things))) if thing.graphics is not None]
    drawables_physics_indices = [things[i].physics.idx for i in drawables_indices]
    ndrawables = len(drawables_indices)
    colors = numpy.zeros((ndrawables, 4, 3), dtype=numpy.uint8)
    vertices = numpy.zeros((ndrawables, 4, 2), dtype=numpy.float32)
    for it, i in zip(drawables_indices, range(len(drawables_indices))):
        colors[i] = things[it].graphics.color.reshape(1, 3)
    vertex_list = pyglet.graphics.vertex_list(ndrawables * 4, 'v2f/stream',
                                              ('c3B/static', colors.ravel()))
    shapes = numpy.array([((things[i].graphics.size * things[i].physics.mass * 0.5).repeat(4) *
                           [-1, -1, -1, 1, 1, 1, 1, -1]).reshape(4, 2)
                          for i in drawables_indices], dtype=numpy.float32)
    verticestmp64 = numpy.zeros((len(drawables_physics_indices), 2), dtype=numpy.float64)
    nframes = 0
    vertices_time = 0.0
    draw_time = 0.0
    phy_time = 0.0
    total_time = 0.0
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                print('Average physics time (ms):', phy_time / nframes)
                print('Average vertices copy time (ms):', vertices_time / nframes)
                print('Average draw time (ms):', draw_time / nframes)
                print('Average frame time (ms):', total_time / nframes)
                return 0
            elif event.type == KEYDOWN or event.type == KEYUP:
                keyboard.dispatch(event)

        start = time()

        clock.dispatch(tick_event)
        phy.tick()

        start_vertices = time()

        numpy.take(phy.l, drawables_physics_indices, out=verticestmp64, axis=0)
        vertices[:] = verticestmp64.reshape(-1, 1, 2)
        vertices += shapes

        ctypes.memmove(vertex_list.vertices, vertices.ctypes.data, vertices.nbytes)

        end_vertices_start_draw = time()

        glClear(GL_COLOR_BUFFER_BIT)
        vertex_list.draw(GL_QUADS)
        pygame.display.flip()

        end_draw = time()

        delta = end_draw - start
        nframes += 1
        phy_time += (start_vertices - start) * 1000
        vertices_time += (end_vertices_start_draw - start_vertices) * 1000
        draw_time += (end_draw - end_vertices_start_draw) * 1000
        total_time += delta * 1000
        if delta < frame_time:
            sleep(frame_time - delta)

if __name__ == '__main__':
    main()


