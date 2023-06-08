import pygame
import player
from ThreadedDialogflowService import ThreadedDialogflowService
import os

'''
Main file for the voiceactivated game.
*Run this file to play the game
*This currently functions as a showcase for Natural Language Processing capabilities in videogames and has no concrete objectives to complete
*Voice commands: 
--> You control the movement of the red dot on the screen:
-----> You can tell it to go left, right, up, down, stop, speed up, and slow down.
***There may be a little delay between when you give the command and when the dot responds
***This is due to server latency 
******PLAY THIS GAME WITH A FUNCTIONING MICROPHONE******
AUTHER: Stephen Ruhlen 
'''

def main2():
    pygame.init()
    font = pygame.font.SysFont('Arial',20)
    clock = pygame.time.Clock()
    fps = 60
    windowx = 800
    windowy = 800
    display = pygame.display.set_mode((windowx,windowy))
    pygame.display.set_caption('VoiceActivatedGame')
    clock = pygame.time.Clock()

    ###API Variables
    #I am sacrificing my API key to the public. Have fun!
    PROJECT_ID = "voiceactivatedgame"
    LANGUAGE_CODE = 'en-US'
    SESSION_ID = 'stevebahret@gmail.com'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'keysFile.json'

    run = True
    player1 = player.Player(10,10,display)
    service = ThreadedDialogflowService(PROJECT_ID)
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                service.stop()

        display.fill((0,0,0))
        response = service.request()
        if response is not None:
            start_time, end_time, result = response
            intent = result.intent.display_name
            if intent == "Move_Up":
                player1.moveUp()
            elif intent == "Move_Down":
                player1.moveDown()
            elif intent == "Move_Left":
                player1.moveLeft()
            elif intent == "Move_Right":
                player1.moveRight()
            elif intent == "Stop":
                player1.stop()
            elif intent == "Slow_Down":
                player1.setSpeed(-5)
            elif intent == "Speed_Up":
                player1.setSpeed(5)
        player1.update()
        clock.tick(60)
        pygame.display.update()

if __name__ == "__main__":
    main2()

'''
NOTES 
--> 3.5-4 second delay after every command until the object reacts
----> This is not fixable as it is an effect of the requirements of NLP
'''