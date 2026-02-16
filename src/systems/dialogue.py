"""
Dialogue system for NPC conversations.
"""

from typing import Dict, List, Optional, Any, Callable


class DialogueNode:
    """A single dialogue node with text and possible branches."""

    def __init__(self, text: str, node_id: str = ""):
        self.id = node_id
        self.text = text
        self.choices: List[DialogueChoice] = []
        self.next_node: Optional[str] = None  # Auto-advance to this node
        self.on_enter: Optional[Callable] = None  # Called when node is shown
        self.condition: Optional[Callable] = None  # Must return True to show

    def add_choice(self, text: str, next_node: str,
                   condition: Optional[Callable] = None) -> 'DialogueNode':
        """Add a dialogue choice."""
        self.choices.append(DialogueChoice(text, next_node, condition))
        return self

    def set_next(self, next_node: str) -> 'DialogueNode':
        """Set automatic next node (no choices)."""
        self.next_node = next_node
        return self


class DialogueChoice:
    """A choice in a dialogue node."""

    def __init__(self, text: str, next_node: str,
                 condition: Optional[Callable] = None):
        self.text = text
        self.next_node = next_node
        self.condition = condition

    def is_available(self, context: Dict[str, Any]) -> bool:
        """Check if choice is available."""
        if self.condition is None:
            return True
        return self.condition(context)


class DialogueTree:
    """A complete dialogue tree with multiple nodes."""

    def __init__(self, tree_id: str = ""):
        self.id = tree_id
        self.nodes: Dict[str, DialogueNode] = {}
        self.start_node: str = "start"
        self.current_node: Optional[str] = None

    def add_node(self, node_id: str, text: str) -> DialogueNode:
        """Add a dialogue node."""
        node = DialogueNode(text, node_id)
        self.nodes[node_id] = node
        return node

    def start(self) -> Optional[DialogueNode]:
        """Start dialogue from beginning."""
        self.current_node = self.start_node
        return self.get_current()

    def get_current(self) -> Optional[DialogueNode]:
        """Get current node."""
        if self.current_node:
            return self.nodes.get(self.current_node)
        return None

    def advance(self, choice_index: int = -1) -> Optional[DialogueNode]:
        """
        Advance dialogue.

        Args:
            choice_index: Index of choice selected (-1 for auto-advance)

        Returns:
            Next dialogue node, or None if dialogue ended
        """
        current = self.get_current()
        if not current:
            return None

        if choice_index >= 0 and current.choices:
            # Player made a choice
            if choice_index < len(current.choices):
                choice = current.choices[choice_index]
                self.current_node = choice.next_node
        elif current.next_node:
            # Auto-advance
            self.current_node = current.next_node
        else:
            # End of dialogue
            self.current_node = None

        return self.get_current()

    def is_complete(self) -> bool:
        """Check if dialogue has ended."""
        return self.current_node is None


class DialogueManager:
    """Manages dialogue trees and conversations."""

    def __init__(self):
        self.trees: Dict[str, DialogueTree] = {}
        self.active_tree: Optional[DialogueTree] = None
        self.context: Dict[str, Any] = {}

    def register_tree(self, tree: DialogueTree) -> None:
        """Register a dialogue tree."""
        self.trees[tree.id] = tree

    def start_dialogue(self, tree_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[DialogueNode]:
        """Start a dialogue tree."""
        if tree_id not in self.trees:
            return None

        self.active_tree = self.trees[tree_id]
        self.context = context or {}

        return self.active_tree.start()

    def get_current_text(self) -> str:
        """Get current dialogue text."""
        if self.active_tree:
            node = self.active_tree.get_current()
            if node:
                return node.text
        return ""

    def get_choices(self) -> List[str]:
        """Get available choices for current node."""
        if not self.active_tree:
            return []

        node = self.active_tree.get_current()
        if not node:
            return []

        return [c.text for c in node.choices if c.is_available(self.context)]

    def select_choice(self, index: int) -> Optional[DialogueNode]:
        """Select a dialogue choice."""
        if self.active_tree:
            return self.active_tree.advance(index)
        return None

    def advance(self) -> Optional[DialogueNode]:
        """Advance dialogue without choice."""
        if self.active_tree:
            return self.active_tree.advance()
        return None

    def is_active(self) -> bool:
        """Check if dialogue is active."""
        return self.active_tree is not None and not self.active_tree.is_complete()

    def end_dialogue(self) -> None:
        """End current dialogue."""
        self.active_tree = None
        self.context = {}


# Pre-built dialogues for demo
def create_oak_dialogue(game_flags: Dict[str, bool]) -> DialogueTree:
    """Create Professor Oak's dialogue tree."""
    tree = DialogueTree("oak")

    if not game_flags.get("got_starter"):
        tree.add_node("start", "Hello there! Welcome to the world of POKEMON!") \
            .set_next("intro2")
        tree.add_node("intro2", "My name is OAK! People call me the POKEMON PROF!") \
            .set_next("intro3")
        tree.add_node("intro3", "This world is inhabited by creatures called POKEMON!") \
            .set_next("choose")
        tree.add_node("choose", "Now, choose your partner!") \
            .add_choice("BULBASAUR", "chose_bulba") \
            .add_choice("CHARMANDER", "chose_charm") \
            .add_choice("SQUIRTLE", "chose_squirt")
        tree.add_node("chose_bulba", "Ah! BULBASAUR is your choice!")
        tree.add_node("chose_charm", "Ah! CHARMANDER is your choice!")
        tree.add_node("chose_squirt", "Ah! SQUIRTLE is your choice!")

    else:
        tree.add_node("start", "How is your POKEDEX coming along?")

    return tree


def create_mom_dialogue() -> DialogueTree:
    """Create Mom's dialogue tree."""
    tree = DialogueTree("mom")

    tree.add_node("start", "...Right. All boys leave home someday.") \
        .set_next("mom2")
    tree.add_node("mom2", "It said so on TV.") \
        .set_next("mom3")
    tree.add_node("mom3", "Take care, honey!")

    return tree
