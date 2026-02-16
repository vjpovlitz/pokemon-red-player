"""
Battle state - handles Pokemon battles.
"""

import pygame
import random
from typing import Optional, Dict, Any, List

from src.core.state_manager import State
from src.battle.battle_manager import BattleManager
from src.battle.damage_calc import calculate_damage
from src.ui.text_box import TextBox
from src.ui.health_bar import HealthBar
from src.ui.menu import BattleMenu
from config import (
    NATIVE_WIDTH, NATIVE_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_LIGHT,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_A, KEY_B
)


class BattleState(State):
    """Handles Pokemon battle logic and rendering."""

    # Battle phases
    PHASE_INTRO = "intro"
    PHASE_ACTION_SELECT = "action_select"
    PHASE_MOVE_SELECT = "move_select"
    PHASE_POKEMON_SELECT = "pokemon_select"
    PHASE_ITEM_SELECT = "item_select"
    PHASE_EXECUTING = "executing"
    PHASE_MESSAGE = "message"
    PHASE_VICTORY = "victory"
    PHASE_DEFEAT = "defeat"

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.battle_manager: Optional[BattleManager] = None
        self.phase = self.PHASE_INTRO
        self.is_wild = True
        self.can_run = True

        # UI elements
        self.text_box: Optional[TextBox] = None
        self.battle_menu: Optional[BattleMenu] = None
        self.player_hp_bar: Optional[HealthBar] = None
        self.enemy_hp_bar: Optional[HealthBar] = None

        # Message queue
        self.message_queue: List[str] = []
        self.current_message = ""
        self.message_complete = False

        # Animation state
        self.intro_timer = 0
        self.intro_complete = False

        # Fonts
        self.font = pygame.font.Font(None, 16)

    def enter(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize battle with given parameters."""
        params = params or {}

        self.is_wild = params.get("type", "wild") == "wild"
        self.can_run = self.is_wild

        # Create battle manager
        self.battle_manager = BattleManager(
            player_party=self.game.player_data.get("party", []),
            enemy_pokemon=params.get("pokemon"),
            is_wild=self.is_wild
        )

        # Create UI elements
        self.text_box = TextBox()
        self.battle_menu = BattleMenu()

        # Create HP bars
        if self.battle_manager.player_pokemon:
            self.player_hp_bar = HealthBar(
                self.battle_manager.player_pokemon.current_hp,
                self.battle_manager.player_pokemon.max_hp
            )
        if self.battle_manager.enemy_pokemon:
            self.enemy_hp_bar = HealthBar(
                self.battle_manager.enemy_pokemon.current_hp,
                self.battle_manager.enemy_pokemon.max_hp
            )

        # Queue intro messages
        enemy_name = self.battle_manager.enemy_pokemon.name if self.battle_manager.enemy_pokemon else "POKEMON"
        if self.is_wild:
            self.message_queue.append(f"Wild {enemy_name} appeared!")
        else:
            trainer_name = params.get("trainer_name", "TRAINER")
            self.message_queue.append(f"{trainer_name} wants to battle!")
            self.message_queue.append(f"{trainer_name} sent out {enemy_name}!")

        player_name = self.battle_manager.player_pokemon.name if self.battle_manager.player_pokemon else "POKEMON"
        self.message_queue.append(f"Go! {player_name}!")

        self.phase = self.PHASE_INTRO
        self._next_message()

    def _next_message(self) -> None:
        """Show the next message in queue."""
        if self.message_queue:
            self.current_message = self.message_queue.pop(0)
            self.text_box.set_text(self.current_message)
            self.message_complete = False
            self.phase = self.PHASE_MESSAGE
        else:
            # No more messages, proceed to next phase
            self._advance_phase()

    def _advance_phase(self) -> None:
        """Move to the next appropriate phase."""
        if self.phase == self.PHASE_INTRO or self.phase == self.PHASE_MESSAGE:
            # Check for battle end conditions
            if self.battle_manager.is_player_defeated():
                self.phase = self.PHASE_DEFEAT
                self.message_queue.append("You have no more Pokemon!")
                self._next_message()
            elif self.battle_manager.is_enemy_defeated():
                self.phase = self.PHASE_VICTORY
                self._handle_victory()
            else:
                self.phase = self.PHASE_ACTION_SELECT
                self.battle_menu.show_main_menu()

    def _handle_victory(self) -> None:
        """Handle battle victory."""
        enemy = self.battle_manager.enemy_pokemon
        if enemy:
            # Calculate and award EXP
            exp = self.battle_manager.calculate_exp_gain()
            self.message_queue.append(f"Defeated {enemy.name}!")
            if exp > 0:
                self.message_queue.append(f"Gained {exp} EXP!")

                # Check for level up
                player = self.battle_manager.player_pokemon
                if player:
                    leveled = player.gain_exp(exp)
                    if leveled:
                        self.message_queue.append(f"{player.name} grew to level {player.level}!")

        self._next_message()

    def handle_event(self, event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False

        action = self.game.input.bindings.get(event.key)

        if self.phase == self.PHASE_MESSAGE:
            if action == KEY_A:
                if self.text_box.is_complete():
                    self._next_message()
                else:
                    self.text_box.skip()
                return True

        elif self.phase == self.PHASE_ACTION_SELECT:
            return self._handle_action_select(action)

        elif self.phase == self.PHASE_MOVE_SELECT:
            return self._handle_move_select(action)

        elif self.phase == self.PHASE_POKEMON_SELECT:
            return self._handle_pokemon_select(action)

        elif self.phase == self.PHASE_VICTORY or self.phase == self.PHASE_DEFEAT:
            if action == KEY_A:
                self.state_manager.pop()
                return True

        return False

    def _handle_action_select(self, action: str) -> bool:
        """Handle input during action selection."""
        if action in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]:
            self.battle_menu.move_cursor(action)
            return True

        elif action == KEY_A:
            selected = self.battle_menu.get_selected()
            if selected == "FIGHT":
                self.phase = self.PHASE_MOVE_SELECT
                moves = []
                if self.battle_manager.player_pokemon:
                    moves = self.battle_manager.player_pokemon.moves
                self.battle_menu.show_move_menu(moves)
            elif selected == "BAG":
                self.phase = self.PHASE_ITEM_SELECT
                # TODO: Show bag
            elif selected == "POKEMON":
                self.phase = self.PHASE_POKEMON_SELECT
                # TODO: Show party
            elif selected == "RUN":
                if self._try_run():
                    self.message_queue.append("Got away safely!")
                    self._next_message()
                    self.phase = self.PHASE_VICTORY  # Will pop state after message
                else:
                    self.message_queue.append("Can't escape!")
                    self._execute_enemy_turn()
            return True

        return False

    def _handle_move_select(self, action: str) -> bool:
        """Handle input during move selection."""
        if action in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]:
            self.battle_menu.move_cursor(action)
            return True

        elif action == KEY_A:
            move_index = self.battle_menu.cursor
            if self.battle_manager.player_pokemon:
                moves = self.battle_manager.player_pokemon.moves
                if move_index < len(moves):
                    self._execute_turn(move_index)
            return True

        elif action == KEY_B:
            self.phase = self.PHASE_ACTION_SELECT
            self.battle_menu.show_main_menu()
            return True

        return False

    def _handle_pokemon_select(self, action: str) -> bool:
        """Handle input during Pokemon selection."""
        if action == KEY_B:
            self.phase = self.PHASE_ACTION_SELECT
            self.battle_menu.show_main_menu()
            return True

        # TODO: Implement party selection

        return False

    def _try_run(self) -> bool:
        """Attempt to run from battle."""
        if not self.can_run:
            return False

        # Gen 1 escape formula
        player = self.battle_manager.player_pokemon
        enemy = self.battle_manager.enemy_pokemon

        if not player or not enemy:
            return True

        player_speed = player.stats.get("speed", 50)
        enemy_speed = enemy.stats.get("speed", 50)

        # Simplified escape chance
        escape_chance = (player_speed * 32) / (enemy_speed // 4) + 30
        return random.randint(0, 255) < escape_chance

    def _execute_turn(self, player_move_index: int) -> None:
        """Execute a full turn of battle."""
        if not self.battle_manager.player_pokemon or not self.battle_manager.enemy_pokemon:
            return

        player = self.battle_manager.player_pokemon
        enemy = self.battle_manager.enemy_pokemon

        player_move = player.moves[player_move_index] if player_move_index < len(player.moves) else None
        enemy_move = self.battle_manager.get_enemy_move()

        if not player_move:
            return

        # Determine turn order
        player_first = player.stats.get("speed", 50) >= enemy.stats.get("speed", 50)

        if player_first:
            self._execute_move(player, enemy, player_move, is_player=True)
            if enemy.current_hp > 0:
                self._execute_move(enemy, player, enemy_move, is_player=False)
        else:
            self._execute_move(enemy, player, enemy_move, is_player=False)
            if player.current_hp > 0:
                self._execute_move(player, enemy, player_move, is_player=True)

        self._next_message()

    def _execute_move(self, attacker, defender, move: dict, is_player: bool) -> None:
        """Execute a single move."""
        if not move:
            return

        move_name = move.get("name", "TACKLE")
        self.message_queue.append(f"{attacker.name} used {move_name}!")

        # Calculate damage
        damage, effectiveness = calculate_damage(attacker, defender, move)

        if damage > 0:
            defender.current_hp = max(0, defender.current_hp - damage)

            # Update HP bars
            if is_player:
                self.enemy_hp_bar.set_hp(defender.current_hp)
            else:
                self.player_hp_bar.set_hp(defender.current_hp)

            # Effectiveness messages
            if effectiveness > 1:
                self.message_queue.append("It's super effective!")
            elif effectiveness < 1 and effectiveness > 0:
                self.message_queue.append("It's not very effective...")
            elif effectiveness == 0:
                self.message_queue.append("It doesn't affect the foe...")

            # Check for KO
            if defender.current_hp <= 0:
                self.message_queue.append(f"{defender.name} fainted!")

    def _execute_enemy_turn(self) -> None:
        """Execute only the enemy's turn (after failed run)."""
        if not self.battle_manager.enemy_pokemon or not self.battle_manager.player_pokemon:
            return

        enemy_move = self.battle_manager.get_enemy_move()
        self._execute_move(
            self.battle_manager.enemy_pokemon,
            self.battle_manager.player_pokemon,
            enemy_move,
            is_player=False
        )
        self._next_message()

    def update(self, dt: float) -> None:
        # Update text box
        if self.text_box:
            self.text_box.update(dt)

        # Update HP bars
        if self.player_hp_bar:
            self.player_hp_bar.update(dt)
        if self.enemy_hp_bar:
            self.enemy_hp_bar.update(dt)

    def render(self, surface) -> None:
        # Draw background
        surface.fill((248, 248, 248))

        # Draw battle scene (placeholder)
        self._render_battle_scene(surface)

        # Draw HP bars and info
        self._render_pokemon_info(surface)

        # Draw menu or text box
        if self.phase in [self.PHASE_ACTION_SELECT, self.PHASE_MOVE_SELECT]:
            self.battle_menu.render(surface)
        elif self.text_box:
            self.text_box.render(surface)

    def _render_battle_scene(self, surface) -> None:
        """Render the battle scene with Pokemon sprites."""
        # Enemy Pokemon position (top right area)
        enemy_rect = pygame.Rect(100, 8, 48, 48)
        pygame.draw.rect(surface, (200, 200, 200), enemy_rect)

        if self.battle_manager.enemy_pokemon:
            name = self.font.render(
                self.battle_manager.enemy_pokemon.name[:10],
                True, COLOR_BLACK
            )
            surface.blit(name, (enemy_rect.x, enemy_rect.y + 50))

        # Player Pokemon position (bottom left area)
        player_rect = pygame.Rect(16, 56, 56, 56)
        pygame.draw.rect(surface, (180, 180, 180), player_rect)

        if self.battle_manager.player_pokemon:
            name = self.font.render(
                self.battle_manager.player_pokemon.name[:10],
                True, COLOR_BLACK
            )
            surface.blit(name, (player_rect.x, player_rect.y + 58))

    def _render_pokemon_info(self, surface) -> None:
        """Render Pokemon names, levels, and HP bars."""
        # Enemy info (top left)
        if self.battle_manager.enemy_pokemon and self.enemy_hp_bar:
            enemy = self.battle_manager.enemy_pokemon
            info_rect = pygame.Rect(4, 8, 72, 28)
            pygame.draw.rect(surface, COLOR_WHITE, info_rect)
            pygame.draw.rect(surface, COLOR_BLACK, info_rect, 1)

            # Name and level
            text = self.font.render(f"{enemy.name[:8]}", True, COLOR_BLACK)
            surface.blit(text, (8, 10))
            level_text = self.font.render(f"Lv{enemy.level}", True, COLOR_BLACK)
            surface.blit(level_text, (8, 22))

            # HP bar
            self.enemy_hp_bar.render(surface, 40, 24, 32)

        # Player info (bottom right)
        if self.battle_manager.player_pokemon and self.player_hp_bar:
            player = self.battle_manager.player_pokemon
            info_rect = pygame.Rect(84, 80, 72, 36)
            pygame.draw.rect(surface, COLOR_WHITE, info_rect)
            pygame.draw.rect(surface, COLOR_BLACK, info_rect, 1)

            # Name and level
            text = self.font.render(f"{player.name[:8]}", True, COLOR_BLACK)
            surface.blit(text, (88, 82))
            level_text = self.font.render(f"Lv{player.level}", True, COLOR_BLACK)
            surface.blit(level_text, (88, 94))

            # HP bar with numbers
            self.player_hp_bar.render(surface, 120, 96, 32)
            hp_text = self.font.render(
                f"{player.current_hp}/{player.max_hp}",
                True, COLOR_BLACK
            )
            surface.blit(hp_text, (88, 106))
