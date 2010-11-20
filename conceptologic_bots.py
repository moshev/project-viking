import pygame
import pygame.locals
import os, sys
import stackless
import math
import time
import random
from collections import defaultdict
from multiprocessing import Process, Pipe, Queue
import avi
RK = True

class actor:
    def __init__(self):
        self.channel = stackless.channel()
        self.processMessageMethod = self.defaultMessageAction
        stackless.tasklet(self.processMessage)()

    def processMessage(self):
        while 1:
            self.processMessageMethod(self.channel.receive())
        
    def defaultMessageAction(self,args):
        print args

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
    def __init__(self,updateRate,time):
        self.updateRate = updateRate
        self.time = time
        self.actors = []

class world(actor):
    def __init__(self):
        actor.__init__(self)
        self.registeredActors = {}
        self.updateRate = 60
        self.maxupdateRate = 60
        stackless.tasklet(self.runFrame)()

    def testForCollision(self,x,y,item,otherItems=[]):
        if x < 0 or x + item.width > 496:
            return self.channel
        elif y < 0 or y+ item.height > 496:
            return self.channel
        else:
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
                x, y = (a + (da[0] + 2 * da[1] + 2 * da[2] + da[3]) / 6 for a, da in zip(actorInfo.location, actorInfo.vectors))
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
        WorldState = worldState(self.updateRate,starttime)
        for actor in self.registeredActors.keys():
            if self.registeredActors[actor].public:
                WorldState.actors.append( (actor, self.registeredActors[actor]) )
        for actor in self.registeredActors.keys():
            actor.send( (self.channel,"WORLD_STATE",WorldState) )

    def runFrame(self):
        initialStartTime = time.clock()
        startTime = time.clock()
        while 1:
            self.killDeadActors()
            self.updateActorPositions()
            self.sendStateToActors(startTime)
            #wait
            calculatedEndTime = startTime + 1.0/self.updateRate

#            doneProcessingTime = time.clock()
#            percentUtilized =  (doneProcessingTime - startTime) / (1.0/self.updateRate)
#            if percentUtilized >= 1:
#                self.updateRate -= 1
#                print "TOO SLOW, ACTORS:", len(self.registeredActors), "LOWERING FRAME RATE:", self.updateRate
#            elif percentUtilized <= 0.6 and self.updateRate < self.maxupdateRate:
#                self.updateRate += 1
#                print "TOO FAST, ACTORS:", len(self.registeredActors), "RAISING FRAME RATE: " , self.updateRate

            while time.clock() < calculatedEndTime:
                stackless.schedule()
            startTime = calculatedEndTime
            
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
            print "FFUUU"
        elif msg == "KILLME":
            self.registeredActors[sentFrom].hitpoints = 0
        elif msg == "QUIT":
            sys.exit(msgArgs[0])
        else:
            print '!!!! WORLD GOT UNKNOWN MESSAGE', sentFrom, msg, msgArgs
            raise NotImplemented()
            
class display(actor):
    def __init__(self, world):
        actor.__init__(self)

        self.world = World
        self.icons = {}
        pygame.init()

        window = pygame.display.set_mode((496,496))
        pygame.display.set_caption("Actor Demo")
        
        self.world.send((self.channel,"JOIN",
                            properties(self.__class__.__name__,
                                       public=False)))

    def defaultMessageAction(self,args):
        sentFrom, msg, msgArgs = args[0],args[1],args[2:]
        if msg == "WORLD_STATE":
            self.updateDisplay(msgArgs)
        else:
            print "DISPLAY UNKNOWN MESSAGE", args

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
            
        screen = pygame.display.get_surface()
        screen.fill((200, 200, 200))

        WorldState = msgArgs[0]

        for channel,item in WorldState.actors:
            itemImage = self.getIcon(item.name, 270.0 - item.angle)
            screen.blit(itemImage, item.location)
        pygame.display.flip()

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
                if actor[0] is self: break
            self.location = actor[1].location
            self.angle += 1
            if self.angle >= 360:
                self.angle -= 360
                
            updateMsg = (self.channel, "UPDATE_VECTOR", self.angle, self.velocity)
            self.world.send(updateMsg)
        elif msg == "COLLISION":
            self.angle += 73
            if self.angle >= 360:
                self.angle -= 360
            self.hitpoints -= 1
            if self.hitpoints <= 0:
                explosion(self.world, self.location, self.angle)
                self.world.send((self.channel, "KILLME"))
        elif msg == "DAMAGE":
            self.hitpoints -= msgArgs[0]
            if self.hitpoints <= 0:
                explosion(self.world, self.location, self.angle)
                self.world.send((self.channel,"KILLME"))
                
        else:
            print "BASIC ROBOT UNKNOWN MESSAGE", args

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
            elif WorldState.time >= self.time + 3.0:
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
            print "UNKNOWN MESSAGE", args

class minedropperRobot(actor):
    def __init__(self,world,location=(0,0),angle=135,velocity=1,
                 hitpoints=20):
        actor.__init__(self)
        self.location = location
        self.angle = angle
        self.delta = 0.0
        self.height=32.0
        self.width=32.0
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
                self.delta += 60.0 * (1.0 / msgArgs[0].updateRate)
                if self.delta > 15.0:
                    self.delta = 15.0
                    self.deltaDirection = "down"
            else:
                self.delta -= 60.0 * (1.0 / msgArgs[0].updateRate)
                if self.delta < -15.0:
                    self.delta = -15.0
                    self.deltaDirection = "up"
            if self.nextMine <= msgArgs[0].time:
                self.nextMine = msgArgs[0].time + 1.0
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
            print "UNKNOWN MESSAGE", args

class spawner(actor):
    def __init__(self,world,location=(0,0)):
        actor.__init__(self)
        self.location = location
        self.time = 0.0
        self.world = world
        
        self.robots = []
        for name,klass in globals().iteritems():
            if name.endswith("Robot"):
                self.robots.append(klass)

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
                self.time = WorldState.time + 0.5 # wait 1/2 second on start
            elif WorldState.time >= self.time:
                self.time = WorldState.time + 1.0
                angle = random.random() * 360.0
                velocity = random.random() * 1.0 + 2.0
                hitpoints = math.trunc(random.random() * 30 + 20)
                newRobot = random.choice(self.robots)
                newRobot(self.world,self.location,angle,velocity, hitpoints)

class world_pipe_bridge(actor):
    def __init__(self, world, process, pipe):
        actor.__init__(self)
        self.world = world
        self.process = process
        self.pipe = pipe
        stackless.tasklet(self.poll_pipe)()
        self.world.send((self.channel, "JOIN", properties(self.__class__.__name__, physical = False, public = False)))

    def poll_pipe(self):
        while self.process.is_alive():
            try:
                if self.pipe.poll(0.01):
                    obj = self.pipe.recv()
                    self.world.send(tuple([self.channel] + list(obj)))
            except IOError:
                print 'omgwtf'
            stackless.schedule()
        self.process.join()
        stackless.schedule_remove()

    def defaultMessageAction(self, args):
        if self.process.is_alive():
            self.pipe.send(args[1:])

def display_process(pipe):
    def getIcon(icons, iconName, angle):
        angle = math.trunc(angle / 10.0) * 10
        if icons.has_key((iconName, angle)):
            return icons[(iconName, angle)]
        elif icons.has_key((iconName, 0)):
            icon = pygame.transform.rotate(icons[(iconName, 0)], angle).convert()
            icons[(iconName, angle)] = icon
            return icon
        else:
            iconFile = os.path.join("data","%s.bmp" % iconName)
            surface = pygame.image.load(iconFile)
            surface.set_colorkey((0xf3,0x0a,0x0a))
            icons[(iconName, 0)] = surface.convert()
            return getIcon(icons, iconName, angle)

    icons = {}
    pygame.init()

    window = pygame.display.set_mode((496,496))
    pygame.display.set_caption("Actor Demo")
    
    while True:
        try:
            msg = pipe.recv()
        except EOFError:
            return 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pipe.send(("QUIT", 0))
                return 0
            
        if msg[0] == 'WORLD_STATE':
            world_state = msg[1]
            screen = pygame.display.get_surface()
            screen.fill((200, 200, 200))

            for channel, item in world_state.actors:
                itemImage = getIcon(icons, item.name, 270.0 - item.angle)
                screen.blit(itemImage, item.location)
            pygame.display.flip()

if __name__ == '__main__':
    World = world().channel
    display(World)
    spawner(World, (32,32))
    spawner(World, (432,32))
    spawner(World, (32,432))
    spawner(World, (432,432))
    spawner(World, (232,232))

    stackless.run()

