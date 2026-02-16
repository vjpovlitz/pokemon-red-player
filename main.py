#!/usr/bin/env python3
"""
Pokemon Red Clone - Demo Version
Entry point for the game
"""

import pygame
import sys
from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from src.game import Game


def main():
    """Initialize and run the game."""
    pygame.init()
    pygame.display.set_caption("Pokemon Red Clone")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)
        game.render()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
