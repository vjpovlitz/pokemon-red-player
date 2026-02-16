"""
Stack-based state manager for game states.
Allows states to be pushed/popped (e.g., menu overlay on overworld).
"""

from typing import Optional, Dict, Any


class State:
    """Base class for all game states."""

    def __init__(self, state_manager: 'StateManager'):
        self.state_manager = state_manager
        self.game = state_manager.game

    def enter(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Called when state becomes active."""
        pass

    def exit(self) -> None:
        """Called when state is removed or covered."""
        pass

    def resume(self) -> None:
        """Called when state becomes active again after being covered."""
        pass

    def pause(self) -> None:
        """Called when another state is pushed on top."""
        pass

    def handle_event(self, event) -> bool:
        """
        Handle a pygame event.
        Return True if event was consumed, False to pass to states below.
        """
        return False

    def update(self, dt: float) -> None:
        """Update state logic."""
        pass

    def render(self, surface) -> None:
        """Render state to surface."""
        pass


class StateManager:
    """
    Manages a stack of game states.
    Only the top state receives updates, but all states can render (for overlays).
    """

    def __init__(self, game):
        self.game = game
        self.states: list[State] = []
        self.state_classes: Dict[str, type] = {}

    def register(self, name: str, state_class: type) -> None:
        """Register a state class with a name."""
        self.state_classes[name] = state_class

    def push(self, name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Push a new state onto the stack."""
        if name not in self.state_classes:
            raise ValueError(f"Unknown state: {name}")

        # Pause current state if exists
        if self.states:
            self.states[-1].pause()

        # Create and enter new state
        state = self.state_classes[name](self)
        self.states.append(state)
        state.enter(params)

    def pop(self) -> Optional[State]:
        """Pop the top state from the stack."""
        if not self.states:
            return None

        state = self.states.pop()
        state.exit()

        # Resume the state below if exists
        if self.states:
            self.states[-1].resume()

        return state

    def replace(self, name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Replace the top state with a new one."""
        if self.states:
            self.states[-1].exit()
            self.states.pop()

        state = self.state_classes[name](self)
        self.states.append(state)
        state.enter(params)

    def clear(self) -> None:
        """Remove all states."""
        while self.states:
            self.states.pop().exit()

    @property
    def current(self) -> Optional[State]:
        """Get the current (top) state."""
        return self.states[-1] if self.states else None

    def handle_event(self, event) -> None:
        """Pass event to states from top to bottom until consumed."""
        for state in reversed(self.states):
            if state.handle_event(event):
                break

    def update(self, dt: float) -> None:
        """Update only the top state."""
        if self.states:
            self.states[-1].update(dt)

    def render(self, surface) -> None:
        """Render all states from bottom to top (for overlays)."""
        for state in self.states:
            state.render(surface)
