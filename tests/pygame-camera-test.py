"""
PyGame Camera Test

Run to see if you can capture and display images from a camera. Press 'esc` to 
exit. Run with root privileges to draw on external monitor (e.g. from SSH).

"Borrowed" from https://gist.github.com/snim2/255151
"""

import pygame
import pygame.camera
from pygame.locals import *

DEVICE = '/dev/video0'
SIZE = (480, 480)
FILENAME = 'capture.png'

def camstream():
    pygame.init()
    pygame.camera.init()
    display = pygame.display.set_mode(SIZE)
    camera = pygame.camera.Camera(DEVICE, SIZE)
    camera.start()
    screen = pygame.surface.Surface(SIZE, 0, display)
    capture = True
    while capture:
        screen = camera.get_image(screen)
        display.blit(screen, (0,0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == QUIT:
                capture = False
            elif event.type == KEYDOWN and event.key == K_s:
                pygame.image.save(screen, FILENAME)
    camera.stop()
    pygame.quit()
    return

if __name__ == '__main__':
    camstream()