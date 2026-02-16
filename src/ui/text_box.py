"""
Text box with typewriter effect for dialogue.
"""

import pygame
from typing import Optional, List

from config import NATIVE_WIDTH, NATIVE_HEIGHT, COLOR_WHITE, COLOR_BLACK


class TextBox:
    """Dialogue text box with typewriter effect."""

    def __init__(self, x: int = 0, y: int = 96, width: int = NATIVE_WIDTH, height: int = 48):
        """
        Initialize text box.

        Args:
            x: X position
            y: Y position
            width: Box width
            height: Box height
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Text settings
        self.font = pygame.font.Font(None, 16)
        self.text = ""
        self.displayed_text = ""
        self.char_index = 0

        # Typewriter settings
        self.chars_per_second = 30
        self.char_timer = 0

        # Pagination
        self.lines: List[str] = []
        self.current_line = 0
        self.max_lines = 2  # Lines visible at once
        self.line_height = 16

        # Continuation arrow
        self.arrow_visible = True
        self.arrow_timer = 0

    def set_text(self, text: str) -> None:
        """Set new text to display."""
        self.text = text
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0

        # Word wrap
        self._wrap_text()
        self.current_line = 0

    def _wrap_text(self) -> None:
        """Wrap text to fit in box."""
        self.lines = []
        words = self.text.split(' ')
        current_line = ""
        max_width = self.width - 16  # Padding

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_surface = self.font.render(test_line, True, COLOR_BLACK)

            if text_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    self.lines.append(current_line)
                current_line = word

        if current_line:
            self.lines.append(current_line)

    def update(self, dt: float) -> None:
        """Update typewriter effect."""
        # Typewriter effect
        if self.char_index < len(self.text):
            self.char_timer += dt
            chars_to_add = int(self.char_timer * self.chars_per_second)

            if chars_to_add > 0:
                self.char_timer = 0
                self.char_index = min(len(self.text), self.char_index + chars_to_add)
                self.displayed_text = self.text[:self.char_index]

        # Arrow blink
        self.arrow_timer += dt
        if self.arrow_timer >= 0.5:
            self.arrow_timer = 0
            self.arrow_visible = not self.arrow_visible

    def skip(self) -> None:
        """Skip to end of current text."""
        self.char_index = len(self.text)
        self.displayed_text = self.text

    def is_complete(self) -> bool:
        """Check if all text has been displayed."""
        return self.char_index >= len(self.text)

    def advance(self) -> bool:
        """
        Advance to next page of text.

        Returns True if more text, False if done.
        """
        if not self.is_complete():
            self.skip()
            return True

        # Check for more lines
        if self.current_line + self.max_lines < len(self.lines):
            self.current_line += self.max_lines
            return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        """Render the text box."""
        # Draw box background
        box_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, COLOR_WHITE, box_rect)
        pygame.draw.rect(surface, COLOR_BLACK, box_rect, 2)

        # Draw text
        visible_text = self.displayed_text
        wrapped_lines = []
        words = visible_text.split(' ')
        current_line = ""
        max_width = self.width - 16

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_surface = self.font.render(test_line, True, COLOR_BLACK)

            if text_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        # Render visible lines
        for i, line in enumerate(wrapped_lines[:self.max_lines]):
            text_surface = self.font.render(line, True, COLOR_BLACK)
            surface.blit(text_surface, (self.x + 8, self.y + 8 + i * self.line_height))

        # Draw continuation arrow if complete
        if self.is_complete() and self.arrow_visible:
            arrow_x = self.x + self.width - 16
            arrow_y = self.y + self.height - 12
            # Simple triangle
            pygame.draw.polygon(surface, COLOR_BLACK, [
                (arrow_x, arrow_y),
                (arrow_x + 8, arrow_y),
                (arrow_x + 4, arrow_y + 6)
            ])


class DialogueBox(TextBox):
    """Extended text box for NPC dialogue with name display."""

    def __init__(self, speaker_name: str = ""):
        super().__init__()
        self.speaker_name = speaker_name

    def set_speaker(self, name: str) -> None:
        """Set the speaker's name."""
        self.speaker_name = name

    def render(self, surface: pygame.Surface) -> None:
        """Render dialogue box with speaker name."""
        # Draw name box if speaker set
        if self.speaker_name:
            name_surface = self.font.render(self.speaker_name, True, COLOR_BLACK)
            name_width = name_surface.get_width() + 12
            name_rect = pygame.Rect(self.x + 4, self.y - 14, name_width, 16)
            pygame.draw.rect(surface, COLOR_WHITE, name_rect)
            pygame.draw.rect(surface, COLOR_BLACK, name_rect, 1)
            surface.blit(name_surface, (self.x + 10, self.y - 12))

        # Draw main text box
        super().render(surface)
