from __future__ import print_function
import pygame
import pygame.locals
import pyglet
from pyglet.gl import *
import os, sys
import stackless
import math
import time
import random
from collections import defaultdict
import multiprocessing
import Queue
import avi
import config

class actor:
    def __init__(self):
        self.channel = stackless.channel()
        self.processMessageMethod = self.defaultMessageAction
        stackless.tasklet(self.processMessage)()

    def processMessage(self):
        while 1:
            self.processMessageMethod(self.channel.receive())
        
    def defaultMessageAction(self,args):
        print(args)

class properties:
    def __init__(self,name,location=(-1,-1),angle=0,
                 velocity=0,height=-1,width=-1,hitpoints=1,physical=True,
                 public=True):
        self.name = name
        self.location = location
        self.angle = angle
        self.velocity = velocity
        self.height = height
        self.width = width
        self.public = public
        self.hitpoints = hitpoints
        self.physical = physical

class worldState:
    def __init__(self, frame_time, time):
        self.frame_time = frame_time
        self.time = time
        self.actors = []

class world(actor):
    def __init__(self):
        actor.__init__(self)
        self.registeredActors = {}
        self.frame_time_ms = 10
        self.min_frame_time_ms = 10
        stackless.tasklet(self.runFrame)()

    def testForCollision(self,x,y,item,otherItems=[]):
        if x < 0 or x + item.width > 496:
            return self.channel
        elif y < 0 or y+ item.height > 496:
            return self.channel
        else:
            if not config.ATOACOLLISION:
                return None
            ax1, ax2, ay1, ay2 = x, x + item.width, y, y + item.height
            angle = item.angle
            velocity = item.velocity
            for item, bx1, bx2, by1, by2 in otherItems:
                if self.registeredActors[item].physical == False:
                    continue
                # test if the two actors are heading towards each other or away
                if velocity != 0 and self.registeredActors[item].velocity != 0:
                    alpha = angle - self.registeredActors[item].angle
                    v1 = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
                    v2 = (bx1 - ax1, by1 - ay1)
                    if (v1[0] * v2[0] + v1[1] * v2[1]) < 0:
                        continue
                for x, y in [(ax1, ay1), (ax1, ay2), (ax2, ay1), (ax2, ay2)]:
                    if x >= bx1 and x <= bx2 and y >= by1 and y <= by2:
                        return item
                for x, y in [(bx1, by1), (bx1, by2), (bx2, by1), (bx2, by2)]:
                    if x >= ax1 and x <= ax2 and y >= ay1 and y <= ay2:
                        return item
            return None

    def killDeadActors(self):
        for actor in self.registeredActors.keys():
            if self.registeredActors[actor].hitpoints <= 0:
                actor.send_exception(TaskletExit)
                del self.registeredActors[actor]

    def updateActorPositions(self):
        actorPositions = []
        for actor in self.registeredActors.keys():
            actorInfo = self.registeredActors[actor]
            if actorInfo.public and actorInfo.physical:
                angle = actorInfo.angle
                velocity = actorInfo.velocity
                for vs, f in zip(actorInfo.vectors, (math.cos, math.sin)):
                    if len(vs) is 0:
                        vs.extend([f(math.radians(angle)) * velocity] * 4)
                    else:
                        vs[0:3] = vs[1:4]
                        vs[3] = f(math.radians(angle)) * velocity
                # RK4 integration.
                # the new positions are the old positions, plus
                # 1/6th of the last 4 vector values, multiplied by
                # 1, 2, 2 and 1 respectively, or:
                # a' = a + 1/6 (da1 + 2*da2 + 2*da3 + da4)
                if config.RK:
                    x, y = (a + (da[0] + 2 * da[1] + 2 * da[2] + da[3]) / 6 for a, da in zip(actorInfo.location, actorInfo.vectors))
                else:
                    x = actorInfo.location[0] + actorInfo.vectors[0][3]
                    y = actorInfo.location[1] + actorInfo.vectors[1][3]
                collision = self.testForCollision(x, y, actorInfo, actorPositions)
                if collision:
                    assert(collision is not actor)
                    assert(actor is not self.channel)
                    actor.send((self.channel, "COLLISION", actor, collision))
                    if collision and collision is not self.channel:
                        collision.send((self.channel,"COLLISION",actor,collision))
                else:                        
                    actorInfo.location = (x, y)
                actorPositions.append((actor,
                                       actorInfo.location[0],
                                       actorInfo.location[0] + actorInfo.height,
                                       actorInfo.location[1],
                                       actorInfo.location[1] + actorInfo.width))

    def sendStateToActors(self,starttime):
        WorldState = worldState(self.min_frame_time_ms / 1000.0, starttime)
        for actor in self.registeredActors.keys():
            if self.registeredActors[actor].public:
                WorldState.actors.append((actor, self.registeredActors[actor]))
        for actor in self.registeredActors.keys():
            actor.send((self.channel, "WORLD_STATE", WorldState))

    def runFrame(self):
        initialStartTime = time.clock()
        while True:
            start_time = pygame.time.get_ticks()
            self.killDeadActors()
            self.sendStateToActors(start_time)
            self.updateActorPositions()

            calculated_end_time = start_time + self.frame_time_ms

            actual_end_time = pygame.time.get_ticks()
            overused = math.trunc(actual_end_time - calculated_end_time)
            if overused > (2 * self.frame_time_ms) / 3:
                print("Overused:", overused, "ms")
                print("Actors:", len(self.registeredActors))
                self.frame_time_ms += 1
                print("New frame time:", self.frame_time_ms, "ms")
            elif overused < -self.frame_time_ms / 2 and self.frame_time_ms > self.min_frame_time_ms:
                print("Underused:", -overused, "ms")
                print("Actors:", len(self.registeredActors))
                if self.frame_time_ms > self.min_frame_time_ms:
                    self.frame_time_ms -= 1
                print("New frame time:", self.frame_time_ms, "ms")

            while pygame.time.get_ticks() < calculated_end_time:
                stackless.schedule()
            
            stackless.schedule()

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "JOIN":
            self.registeredActors[sentFrom] = msgArgs[0]
            self.registeredActors[sentFrom].vectors = [[0] * 4, [0] * 4]
        elif msg == "UPDATE_VECTOR":
            self.registeredActors[sentFrom].angle = msgArgs[0]
            self.registeredActors[sentFrom].velocity = msgArgs[1]
        elif msg == "COLLISION":
            print("FFUUU")
        elif msg == "KILLME":
            self.registeredActors[sentFrom].hitpoints = 0
        elif msg == "QUIT":
            sys.exit(msgArgs[0])
        else:
            print('!!!! WORLD GOT UNKNOWN MESSAGE', sentFrom, msg, msgArgs)
            raise NotImplemented()

class display_sw(actor):
    def __init__(self, world):
        actor.__init__(self)

        self.world = world
        self.icons = {}
        pygame.init()

        window = pygame.display.set_mode(config.resolution)
        pygame.display.set_caption("Actor Demo")
        
        self.world.send((self.channel,"JOIN", properties(self.__class__.__name__, public=False)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            self.updateDisplay(msgArgs)
        else:
            print("DISPLAY UNKNOWN MESSAGE", args)

    def getIcon(self, iconName, angle):
        angle = math.trunc(angle)
        angle_key = math.trunc(angle / 17.5)
        if self.icons.has_key((iconName, angle_key)):
            return self.icons[(iconName, angle_key)]
        elif self.icons.has_key((iconName, 0)):
            icon = pygame.transform.rotate(self.icons[(iconName, 0)], angle).convert()
            self.icons[(iconName, angle_key)] = icon
            return icon
        else:
            iconFile = os.path.join("data","%s.bmp" % iconName)
            surface = pygame.image.load(iconFile)
            surface.set_colorkey((0xf3,0x0a,0x0a))
            self.icons[(iconName, 0)] = surface.convert()
            return self.getIcon(iconName, angle)

    def updateDisplay(self,msgArgs):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.world.send((self.channel, "QUIT", 0))

        WorldState = msgArgs[0]

        if config.DRAW:
            screen = pygame.display.get_surface()
            screen.fill((200, 200, 200))

            for channel,item in WorldState.actors:
                itemImage = self.getIcon(item.name, 270.0 - item.angle)
                screen.blit(itemImage, item.location)
            pygame.display.flip()

class display_gl(actor):
    def __init__(self, world):
        actor.__init__(self)

        self.world = world
        self.icons = {}
        pygame.init()
        pyglet.options['debug_gl'] = False

        window = pygame.display.set_mode(config.resolution, pygame.DOUBLEBUF | pygame.OPENGL)
        pygame.display.set_caption("Actor Demo")
        glClearColor(0.8, 0.8, 0.8, 1.0)
        glMatrixMode(GL_PROJECTION)
        gluOrtho2D(0, config.resolution[0], config.resolution[1], 0)
        glMatrixMode(GL_MODELVIEW)
        self.loader = pyglet.resource.Loader(['data'])
        self.groups = {}
        self.batch = pyglet.graphics.Batch()
        
        self.world.send((self.channel,"JOIN", properties(self.__class__.__name__, public=False)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            self.updateDisplay(msgArgs)
        else:
            print("DISPLAY UNKNOWN MESSAGE", args)

    def texture_group_for(self, name):
        if name in self.groups:
            return self.groups[name]
        else:
            image = self.loader.image('%s.bmp' % name)
            group = pyglet.graphics.TextureGroup(image)
            self.groups[name] = group
            self.groups[name].texture = image
            return group

    def updateDisplay(self,msgArgs):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.world.send((self.channel, "QUIT", 0))

        WorldState = msgArgs[0]

        if config.DRAW:
            pygame.display.flip()
            start_draw = pygame.time.get_ticks()
            glClear(GL_COLOR_BUFFER_BIT)
            lists = []
            for channel,item in WorldState.actors:
#                quad = tuple([0.0] * 8)
                ux = math.cos(math.radians(item.angle - 90))
                uy = math.sin(math.radians(item.angle - 90))
                vx = math.cos(math.radians(item.angle - 180))
                vy = math.sin(math.radians(item.angle - 180))
                w = item.width / 2
                h = item.height / 2
                cx = item.location[0] + w
                cy = item.location[1] + h
                wx, wy, hx, hy = ux * w, uy * w, vx * h, vy * h
                quad = (cx - wx - hx, cy - wy - hy,
                        cx + wx - hx, cy + wy - hy,
                        cx + wx + hx, cy + wy + hy,
                        cx - wx + hx, cy - wy + hy)
                group = self.texture_group_for(item.name)
                tex = tuple(group.texture.tex_coords[i] for i in
                            (9, 10, 6, 7, 3, 4, 0, 1))
                lists.append(self.batch.add(4, GL_QUADS, group, ('v2f', quad), ('t2f', tex)))
            self.batch.draw()
            for vlist in lists:
                vlist.delete()
            print("Draw took", pygame.time.get_ticks() - start_draw, 'ms')

class basicRobot(actor):
    def __init__(self, world, location=(0,0),angle=135,velocity=1,
                 hitpoints=20):
        actor.__init__(self)
        self.location = location
        self.angle = angle
        self.velocity = velocity
        self.hitpoints = hitpoints
        self.world = world
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       location=self.location,
                                       angle=self.angle,
                                       velocity=self.velocity,
                                       height=32, width=32, hitpoints=self.hitpoints)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            for actor in msgArgs[0].actors:
                if actor[0] is self:
                    self.location = actor[1].location
                    break
            self.angle += math.trunc(random.random() * 1.5)
            if self.angle >= 360:
                self.angle -= 360
                
            updateMsg = (self.channel, "UPDATE_VECTOR", self.angle, self.velocity)
            self.world.send(updateMsg)
        elif msg == "COLLISION":
            self.hitpoints -= 1
            if self.hitpoints <= 0:
                explosion(self.world, self.location, self.angle)
                self.world.send((self.channel, "KILLME"))
            self.angle += 73
            if self.angle >= 360:
                self.angle -= 360
        elif msg == "DAMAGE":
            self.hitpoints -= msgArgs[0]
            if self.hitpoints <= 0:
                explosion(self.world, self.location, self.angle)
                self.world.send((self.channel,"KILLME"))
                
        else:
            print("BASIC ROBOT UNKNOWN MESSAGE", args)

class explosion(actor):
    def __init__(self,world,location=(0,0),angle=0):
        actor.__init__(self)
        self.time = 0.0
        self.world = world
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       location = location,
                                       angle = angle,
                                       velocity=0,
                                       height=32.0,width=32.0,hitpoints=1,
                                       physical=False)))
                           
    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            WorldState = msgArgs[0]
            if self.time == 0.0:
                self.time = WorldState.time
            elif WorldState.time >= self.time + 3000:
                self.world.send( (self.channel, "KILLME") )

class mine(actor):
    def __init__(self, world, location=(0,0), parent = None):
        actor.__init__(self)
        self.parent = parent
        self.world = world
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       location=location,
                                       angle=0,
                                       velocity=0,
                                       height=2.0,width=2.0,hitpoints=1)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            pass                
        elif msg == "COLLISION":
            if msgArgs[0] is self.channel:
                other = msgArgs[1]
            else:
                other = msgArgs[0]
            # Do not damage the world.
            # Colliding with the world means the mine is outside the field.
            # Just die in that case
            if other is not self.world:
                other.send((self.channel,"DAMAGE",25) )
            self.world.send((self.channel,"KILLME"))
        else:
            print("UNKNOWN MESSAGE", args)

class minedropperRobot(actor):
    def __init__(self,world,location=(0,0),angle=135,velocity=1,
                 hitpoints=20):
        actor.__init__(self)
        self.location = location
        self.angle = angle
        self.delta = 0.0
        self.height = 32.0
        self.width = 32.0
        self.deltaDirection = "up"
        self.nextMine = 0.0
        self.velocity = velocity
        self.velocities = [0, 0, 0, velocity]
        self.hitpoints = hitpoints
        self.world = world
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       location=self.location,
                                       angle=self.angle,
                                       velocity=self.velocity,
                                       height=self.height,width=self.width,
                                       hitpoints=self.hitpoints)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            for actor in msgArgs[0].actors:
                if actor[0] is self.channel:
                    break
            self.location = actor[1].location
            if self.deltaDirection == "up":
                self.delta += msgArgs[0].frame_time
                if self.delta > 15.0:
                    self.delta = 15.0
                    self.deltaDirection = "down"
            else:
                self.delta -= msgArgs[0].frame_time
                if self.delta < -15.0:
                    self.delta = -15.0
                    self.deltaDirection = "up"
            if self.nextMine <= msgArgs[0].time:
                self.nextMine = msgArgs[0].time + 1000
                mineX,mineY = (self.location[0] + (self.width / 2.0) ,
                               self.location[1] + (self.width / 2.0))

                #mineDistance = (self.width / 2.0 ) ** 2
                #mineDistance += (self.height / 2.0) ** 2
                #mineDistance = math.sqrt(mineDistance)
                mineDistance = (self.width + self.height) / 3.0

                VectorX,VectorY = (math.sin(math.radians(self.angle + self.delta)),
                                   math.cos(math.radians(self.angle + self.delta)))
                VectorX,VectorY = VectorX * mineDistance,VectorY * mineDistance
                x,y = self.location
                x += self.width / 2.0
                y += self.height / 2.0
                x -= VectorX
                y += VectorY
                mine(self.world, (x,y), self)

            updateMsg = (self.channel, "UPDATE_VECTOR",
                         self.angle + self.delta ,self.velocity)
            self.world.send(updateMsg)
        elif msg == "COLLISION":
            self.angle += 73.0
            if self.angle >= 360:
                self.angle -= 360
            self.hitpoints -= 1
            if self.hitpoints <= 0:
                explosion(self.world, self.location,self.angle)
                self.world.send((self.channel,"KILLME"))
        elif msg == "DAMAGE":
            self.hitpoints -= msgArgs[0]
            if self.hitpoints <= 0:
                explosion(self.world, self.location,self.angle)
                self.world.send((self.channel, "KILLME"))
        else:
            print("UNKNOWN MESSAGE", args)

class spawner(actor):
    def __init__(self,world,location=(0,0)):
        actor.__init__(self)
        self.location = location
        self.time = 0.0
        self.world = world
        
        self.robots = [basicRobot, minedropperRobot]
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       location = location,
                                       angle=0,
                                       velocity=0,
                                       height=32.0,width=32.0,hitpoints=1,
                                       physical=False)))

    def defaultMessageAction(self,args):    
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            WorldState = msgArgs[0]
            if self.time == 0.0:
                self.time = WorldState.time + 500 # wait 1/2 second on start
            elif WorldState.time >= self.time:
                self.time = WorldState.time + 1000
                angle = random.random() * 360.0
                velocity = random.random() * 1.0 + 2.0
                hitpoints = math.trunc(random.random() * 15 + 15)
                newRobot = random.choice(self.robots)
                newRobot(self.world,self.location,angle,velocity, hitpoints)

class world_state_to_queue_bridge(actor):
    '''
    Puts WORLD_STATE messages received from world on the given queue.
    block and timeout are given to the queue's put() method, see multiprocessing.Queue
    '''
    def __init__(self, world, queue, block=True, timeout=None):
        actor.__init__(self)
        self.world, self.queue, self.block, self.timeout = world, queue, block, timeout
        self.world.send((self.channel, "JOIN", properties(self.__class__.__name__, physical = False, public=False)))

    def defaultMessageAction(self, message):
        sender, body = message[0], message[1:]
        assert(sender is self.world)
        if body[0] == 'WORLD_STATE':
            state = {'time': body[1].time,
                     'frame_time': body[1].frame_time,
                     'actors': [a[1] for a in body[1].actors]}
            try:
                self.queue.put(('WORLD_STATE', state), self.block, self.timeout)
            except Queue.Full:
                stackless.schedule()

class queue_to_world_bridge:
    '''
    Sends messages gotten from the given queue on the world channel.
    block and timeout are given to the queue's get() method, see multiprocessing.Queue
    '''
    def __init__(self, world, queue, block=True, timeout=None):
        self.world, self.queue, self.block, self.timeout = world, queue, block, timeout
        self.channel = stackless.channel()
        stackless.tasklet(self.wait_for_message)()

    def wait_for_message(self):
        while True:
            try:
                msg = self.queue.get(self.block, self.timeout)
                self.world.send(tuple([self.channel] + list(msg)))
            except (Queue.Empty, IOError):
                stackless.schedule()

def main():
    random.seed(config.SEED)
    World = world().channel
    spawner(World, (32,32))
    spawner(World, (432,32))
    spawner(World, (32,432))
    spawner(World, (432,432))
    spawner(World, (232,232))

    if config.GRAPHICS:
        if config.MULTIPROCESS:
            queue_to_avi = multiprocessing.Queue(100)
            queue_from_avi = multiprocessing.Queue(100)
            avi_process = multiprocessing.Process(target=avi.run, args=(queue_to_avi, queue_from_avi))
            world_state_to_queue_bridge(World, queue_to_avi, block=True)
            queue_to_world_bridge(World, queue_from_avi, block=False)
            avi_process.start()
        else:
            if config.OPENGL:
                display_actor = display_gl(World)
            else:
                display_actor = display_sw(World)

    stackless.run()
    if MULTIPROCESS:
        avi_process.join()

if __name__ == '__main__':
    main()

