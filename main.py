import pygame
from pygame.locals import *
import time
from math import *
import numpy as np
import pygame.math

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

# Constants
FPS = 120
dt = 1/FPS

WIDTH = 800
HEIGHT = 600

V2 = pygame.Vector2

hammerPos = V2(0, 0)
hammerVel = V2(0, 0)
hammerAcc = V2(0, 0)
hammerLength = WIDTH/7
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

    hammerPosPrev = hammerPos

    # hammerPos = V2(pygame.mouse.get_pos())
    hammerAcc: V2 = (-(V2(WIDTH/2, HEIGHT/2) - V2(pygame.mouse.get_pos()))*FPS - hammerVel)*FPS

    # hammerVel + 
    hammerVel += hammerAcc * dt

    pygame.mouse.set_pos(V2(WIDTH/2, HEIGHT/2))

    hammerPos += hammerVel*dt
    if (hammerPos - personPos).length_squared() > hammerLength**2:
        hammerPos = (hammerPos - personPos).normalize()*hammerLength + personPos

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
    
        if AABBvsPoint(rects[i], hammerPos):
            minDiff = pygame.Rect(rects[i].left-hammerPos.x, rects[i].top-hammerPos.y,
                                  rects[i].width, rects[i].height)
            result = PenetrationVector(minDiff)
            
            hammerPos += result
            hammerPos.x -= hammerVel.x*dt

            F = ((hammerPos - hammerPosPrev)*FPS - hammerVel)*FPS
            personAcc += F/50
            # personVel -= hammerVel*dt*5
            # hammerVel = hammerPos - hammerPosPrev

    display.fill((0, 0, 0))

    for rect in rects:
        pygame.draw.rect(display, (0, 0, 255), rect)
        
    pygame.draw.rect(display, (255, 0, 0), personRect(personPos))
    pygame.draw.circle(display, (0, 255, 0), tuple(hammerPos), hammerRad)

    pygame.display.flip()
    fpsClock.tick(FPS);

pygame.quit()
quit(0)
