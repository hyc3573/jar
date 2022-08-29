import pygame
from pygame.locals import *
import time
from math import *
import pygame.math

flt_min = 0.0000001

drawLine = False
lineFrom = pygame.Vector2(0, 0)
lineTo = pygame.Vector2(0, 0)

def AABBvsAABB(rect1: pygame.Rect, rect2: pygame.Rect):
    return (rect1.x < rect2.x + rect2.width and
            rect1.x + rect1.width > rect2.x and
            rect1.y < rect2.y + rect2.height and
            rect1.y + rect1.height > rect2.y)

def AABBvsPoint(rect: pygame.Rect, point: pygame.Vector2):
    return AABBvsAABB(rect, pygame.Rect(point.x, point.y, 0, 0))

def personRect(personPos):
    return pygame.Rect(
                personPos.x - personWidth/2,
                personPos.y - personHeight/2,
                personWidth,
                personHeight
            )

def PenetrationVector(minDiff: pygame.Rect):
    # https://blog.hamaluik.ca/posts/simple-aabb-collision-using-minkowski-difference/
    minDist = abs(minDiff.left)
    result = V2(minDiff.left, 0)
    if abs(minDiff.right) < minDist:
        minDist = abs(minDiff.right)
        result = V2(minDiff.right, 0)
    if abs(minDiff.bottom) < minDist:
        minDist = abs(minDiff.bottom)
        result = V2(0, minDiff.bottom)
    if abs(minDiff.top) < minDist:
        minDist = abs(minDiff.top)
        result = V2(0, minDiff.top)

    return result

def AABBvsRay(rect: pygame.Rect, orig: pygame.Vector2, rdir: pygame.Vector2):
    dirfrac = pygame.Vector2(1/(rdir.x+flt_min), 1/(rdir.y+flt_min))

    t1 = (rect.left - orig.x)*dirfrac.x
    t2 = (rect.right - orig.x)*dirfrac.x
    t3 = (rect.top - orig.y)*dirfrac.y
    t4 = (rect.bottom - orig.y)*dirfrac.y

    tmin = max(min(t1, t2), min(t3, t4))
    tmax = min(max(t1, t2), max(t3, t4))

    if tmax < 0:
        return (False, tmax)
    elif tmin > tmax:
        return (False, tmax)
    else:
        return (True, tmin)

def AABBvsSegment(rect: pygame.Rect, vfrom: pygame.Vector2, vto: pygame.Vector2):
    c, t = AABBvsRay(rect, vfrom, (vto - vfrom).normalize())

    if not c:
        return (False, V2(0, 0))
    
    if t**2 < (vto-vfrom).length_squared():
        return (True, (vto-vfrom).normalize()*t)
    else:
        return (False, V2(0, 0))

# Constants
FPS = 120
dt = 1/FPS

WIDTH = 800
HEIGHT = 600

V2 = pygame.Vector2

hammerPos = V2(0, 0)
hammerVel = V2(0, 0)
hammerAcc = V2(0, 0)
hammerLength = WIDTH/5
hammerRad = 5

personWidth = WIDTH/15
personHeight = WIDTH/5
personPos = V2(WIDTH/2, HEIGHT/2)
personVel = V2(0, 0)
personAcc = V2(0, 0)
personInvMass = 1/1

stopFall = False

hammerPos = personPos*1

friction = 0.2
damp = 0.01
sepdist = 0.01

gravity = V2(0, 1000)

rects = [
    pygame.Rect(0, HEIGHT-50, WIDTH, 50),
    pygame.Rect(WIDTH*2/3, HEIGHT*2/3, WIDTH/15, WIDTH/15)
]

pygame.init()
pygame.mouse.set_visible(False)
pygame.mouse.set_pos(V2(WIDTH/2, HEIGHT/2))
pygame.event.set_grab(True)

fpsClock = pygame.time.Clock()

display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Jar')

shouldExit = False
while not shouldExit:
    tick = time.time();
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            shouldExit = True;
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                shouldExit = True

    hammerPosPrev = hammerPos

    # hammerPos = V2(pygame.mouse.get_pos())
    hammerAcc: V2 = (-(V2(WIDTH/2, HEIGHT/2) - V2(pygame.mouse.get_pos()))*FPS - hammerVel)*FPS

    # hammerVel + 
    hammerVel += hammerAcc * dt

    pygame.mouse.set_pos(V2(WIDTH/2, HEIGHT/2))

    hammerPosPrev = hammerPos*1
    hammerPos += hammerVel*dt
    if (hammerPos - personPos).length_squared() > hammerLength**2:
        hammerPos = (hammerPos - personPos).normalize()*hammerLength + personPos
    hammerVel = (hammerPos - hammerPosPrev)*FPS

    personAcc += gravity
    personVel += personAcc*dt
    personVel *= 1 - damp

    personAcc = V2(0, 0)
    stopFall = False

    personPosPrev = personPos*1 # to make sure it copies
    personPos += personVel*dt

    # collision check
    for i in range(len(rects)):
        if AABBvsAABB(
                personRect(personPos),
                rects[i]
        ):
            rect = personRect(personPos)
            minDiff = pygame.Rect(rect.left-rects[i].right,
                                  rect.top-rects[i].bottom,
                                  rect.width+rects[i].width,
                                  rect.height+rects[i].height)
    
            # find closest side
            result = PenetrationVector(minDiff)
    
            # resolution
            personPos -= result
            # personVel += gravity*(result.dot(gravity))*dt
            # personVel -= gravity*dt
            if result.y:
                personVel.x *= 1-friction
                personAcc -= gravity
    
        c = False
        t = V2(0, 0)
        if hammerVel.length_squared() != 0:
            c, t = AABBvsSegment(rects[i], hammerPos - hammerVel*dt, hammerPos)

        if c:
            result = t
            
            hammerPos = hammerPosPrev + result

            if result.y:
                hammerPos.x -= hammerVel.x*dt
            elif result.x:
                hammerPos.y -= hammerVel.y*dt

            F = ((hammerPos - hammerPosPrev)*FPS - hammerVel)*FPS
            personAcc += F/50
            # personVel -= hammerVel*dt*5
            # hammerVel = hammerPos - hammerPosPrev

    display.fill((0, 0, 0))

    for rect in rects:
        pygame.draw.rect(display, (0, 0, 255), rect)
        
    pygame.draw.rect(display, (255, 0, 0), personRect(personPos))
    pygame.draw.circle(display, (0, 255, 0), tuple(hammerPos), hammerRad)

    if drawLine:
        pygame.draw.line(display, (255, 255, 0), lineFrom, lineTo)
        pygame.draw.circle(display, (255, 55, 0), lineTo, 10)
        # drawLine = False

    pygame.display.flip()
    fpsClock.tick(FPS);

pygame.quit()
quit(0)
