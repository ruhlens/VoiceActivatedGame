import pygame
'''
Player class.
This class defines the player object and how it moves.
Author: Stephen Ruhlen
'''

class Player:
    ###Class that creates the player and controls player movement

    def __init__(self,x,y,display):
        self.display = display
        self.height = 10
        self.width = 10
        self.x = x
        self.y = y
        self.dx, self.dy = 0,0
        self.rect = pygame.Rect(self.x,self.y,self.width,self.height)
        self.speed = 2

    def moveUp(self):
        self.dy -= self.speed

    def moveDown(self):
        self.dy += self.speed

    def moveRight(self):
        self.dx += self.speed

    def moveLeft(self):
        self.dx -= self.speed

    def stop(self):
        self.dx = 0 
        self.dy = 0

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.rect.update(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.display, (255,0,0), self.rect)

    def getSpeed(self):
        return self.speed 
    
    def setSpeed(self, speed):
        self.speed += speed                        
