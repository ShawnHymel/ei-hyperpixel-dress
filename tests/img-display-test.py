"""
Display test on HyperPixel 2" Round

License: Apache-2.0
"""

import os, time

import pygame
import cv2

# Settings
DISPLAY_RES = (480, 480)

# Initialize display
pygame.display.init()
surface = pygame.display.set_mode(DISPLAY_RES)

# Disable mouse
pygame.event.set_blocked(pygame.MOUSEMOTION)
pygame.mouse.set_visible(False)

# Load, resize, and flip image
img = cv2.imread("image.png", cv2.IMREAD_UNCHANGED)
img = cv2.resize(img, DISPLAY_RES, interpolation=cv2.INTER_LINEAR)
img = cv2.flip(img, 1)

# Main game loop
running = True
while running:

    # Iterate over all received game events in the queue
    for event in pygame.event.get():

        # Check for GUI or keystroke exits
        if event.type == pygame.QUIT:
            running = False
            break
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
            break

    # Draw image on surface
    frame = pygame.surfarray.make_surface(img)
    surface.blit(frame, (0,0))

    # Draws the surface object to the screen
    pygame.display.update()

# Exit
pygame.quit()