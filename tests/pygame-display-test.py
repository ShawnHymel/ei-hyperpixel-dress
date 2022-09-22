"""
PyGame Display Test

Run to see if you can draw things in Pygame. Press 'esc` to exit. Run with
root privileges to draw on external monitor (e.g. from SSH).
"""

import pygame
import os

# assigning values to X and Y variable
WIDTH = 480
HEIGHT = 480

# Write directly to framebuffer
RAW_FB = True

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 128)

# Define framebuffer
os.environ['SDL_FBDEV'] = "/dev/fb0"

# Initialize display
os.putenv('SDL_VIDEODRIVER', 'dummy')
pygame.display.init()
pygame.font.init()
surface = pygame.Surface((WIDTH, HEIGHT))

# Set the pygame window name
pygame.display.set_caption('Show Text')

# Create a rectangle with some text
font = pygame.font.Font('freesansbold.ttf', 32)
text = font.render('PyGame Draw Test', True, RED, BLUE)
textRect = text.get_rect()
textRect.center = (WIDTH // 2, HEIGHT // 2)

# Disable mouse
pygame.event.set_blocked(pygame.MOUSEMOTION)
pygame.mouse.set_visible(False)

# Function to update framebuffer directly
def updatefb():
    fbdev = os.getenv('SDL_FBDEV', '/dev/fb0')
    with open(fbdev, 'wb') as fb:
        fb.write(surface.convert(16, 0).get_buffer())

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

    # Fill surface with solid color
    surface.fill(WHITE)

    # Draw text on text rectangle
    surface.blit(text, textRect)

    # Draws the surface object to the screen
    if RAW_FB:
        updatefb()
    else:
        pygame.display.update()

# Exit
pygame.quit()