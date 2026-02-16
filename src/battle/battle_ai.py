"""
Battle AI for enemy Pokemon/trainers.
"""

import random
from typing import Dict, Any, Optional, List

from src.battle.type_chart import get_all_effectiveness


class BattleAI:
    """Simple battle AI for enemy Pokemon."""

    def __init__(self, difficulty: str = "normal"):
        """
        Initialize AI.

        Args:
            difficulty: "easy", "normal", or "hard"
        """
        self.difficulty = difficulty

    def choose_move(self, attacker, defender) -> Optional[Dict[str, Any]]:
        """
        Choose a move for the AI Pokemon to use.

        Args:
            attacker: The AI's Pokemon
            defender: The player's Pokemon

        Returns:
            Move data dict, or None if no moves available
        """
        available_moves = [m for m in attacker.moves if m.get("current_pp", 0) > 0]

        if not available_moves:
            # Struggle (placeholder)
            return {"name": "STRUGGLE", "power": 50, "type": "normal", "pp": 1}

        if self.difficulty == "easy":
            return self._choose_random(available_moves)
        elif self.difficulty == "hard":
            return self._choose_smart(available_moves, attacker, defender)
        else:
            # Normal: 50% smart, 50% random
            if random.random() < 0.5:
                return self._choose_smart(available_moves, attacker, defender)
            return self._choose_random(available_moves)

    def _choose_random(self, moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Randomly select a move."""
        return random.choice(moves)

    def _choose_smart(self, moves: List[Dict[str, Any]], attacker, defender) -> Dict[str, Any]:
        """Choose the best move based on type effectiveness and power."""
        best_move = moves[0]
        best_score = 0

        for move in moves:
            score = self._score_move(move, attacker, defender)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _score_move(self, move: Dict[str, Any], attacker, defender) -> float:
        """
        Score a move based on expected damage.

        Args:
            move: Move data dict
            attacker: Attacking Pokemon
            defender: Defending Pokemon

        Returns:
            Score value (higher = better)
        """
        power = move.get("power", 0)

        # Non-damaging moves get low score (AI doesn't use them well)
        if power == 0:
            return 10  # Small chance to use status moves

        # Base score from power
        score = power

        # Type effectiveness bonus
        move_type = move.get("type", "normal")
        effectiveness = get_all_effectiveness(move_type, defender.types)
        score *= effectiveness

        # STAB bonus
        if move_type in attacker.types:
            score *= 1.5

        # Accuracy penalty
        accuracy = move.get("accuracy", 100)
        score *= (accuracy / 100)

        return score

    def should_switch(self, current: 'Pokemon', team: List['Pokemon'],
                      opponent: 'Pokemon') -> Optional[int]:
        """
        Decide if AI should switch Pokemon.

        Returns index to switch to, or None to stay.
        """
        if self.difficulty == "easy":
            return None  # Easy AI never switches

        # Check if current Pokemon is at disadvantage
        best_matchup_score = self._matchup_score(current, opponent)

        best_switch = None
        best_switch_score = best_matchup_score

        for i, pokemon in enumerate(team):
            if pokemon == current or pokemon.current_hp <= 0:
                continue

            score = self._matchup_score(pokemon, opponent)
            if score > best_switch_score + 50:  # Significant improvement needed
                best_switch_score = score
                best_switch = i

        return best_switch

    def _matchup_score(self, pokemon, opponent) -> float:
        """Score how well a Pokemon matches up against opponent."""
        score = 0

        # Check our moves against opponent
        for move in pokemon.moves:
            if move.get("power", 0) > 0:
                move_type = move.get("type", "normal")
                effectiveness = get_all_effectiveness(move_type, opponent.types)
                if effectiveness > 1:
                    score += 50 * effectiveness

        # Check opponent's types against us
        for opp_type in opponent.types:
            effectiveness = get_all_effectiveness(opp_type, pokemon.types)
            if effectiveness > 1:
                score -= 30 * effectiveness

        # HP consideration
        hp_percent = pokemon.current_hp / max(1, pokemon.max_hp)
        score *= hp_percent

        return score
