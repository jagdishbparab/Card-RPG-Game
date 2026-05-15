import random
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class GamePhase(Enum):
    DRAFT = 1
    CAST = 2
    COMBAT = 3
    RESULT = 4
    GAME_OVER = 5

class ReactionType(Enum):
    NONE = 0
    MELT = 1
    VAPORIZE = 2
    FREEZE = 3
    OVERLOAD = 4
    SUPERCONDUCT = 5
    SAME_ELEMENT = 6

class StatusEffect(Enum):
    NONE = 0
    STUNNED = 1
    DEFENSE_DOWN = 2

@dataclass
class Card:
    element: str
    card_id: int
    def __repr__(self) -> str: return f"{self.element}"

@dataclass
class CharacterStatus:
    hp: float
    max_hp: float = 200.0
    status_effect: StatusEffect = StatusEffect.NONE
    defense_modifier: float = 1.0 
    is_stunned_next_turn: bool = False

    def take_damage(self, damage: float) -> float:
        actual_damage = damage / self.defense_modifier
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def clear_negative_effects(self) -> None:
        if self.status_effect == StatusEffect.STUNNED:
            self.status_effect = StatusEffect.NONE
        self.is_stunned_next_turn = False

    def reset_turn_status(self) -> None:
        if self.is_stunned_next_turn:
            self.status_effect = StatusEffect.STUNNED
            self.is_stunned_next_turn = False
        else:
            self.status_effect = StatusEffect.NONE

# ============================================================================
# THE REACTION MATRIX
# ============================================================================

class ReactionMatrix:
    REACTION_MAP: Dict[Tuple[str, str], Tuple[ReactionType, float, StatusEffect]] = {}

    @classmethod
    def initialize(cls) -> None:
        cls.REACTION_MAP = {
            ('Pyro', 'Cryo'): (ReactionType.MELT, 2.0, StatusEffect.NONE),
            ('Cryo', 'Pyro'): (ReactionType.MELT, 2.0, StatusEffect.NONE),
            ('Pyro', 'Hydro'): (ReactionType.VAPORIZE, 1.5, StatusEffect.NONE),
            ('Hydro', 'Pyro'): (ReactionType.VAPORIZE, 1.5, StatusEffect.NONE),
            ('Pyro', 'Electro'): (ReactionType.OVERLOAD, 2.5, StatusEffect.NONE),
            ('Electro', 'Pyro'): (ReactionType.OVERLOAD, 2.5, StatusEffect.NONE),
            ('Hydro', 'Cryo'): (ReactionType.FREEZE, 0.5, StatusEffect.STUNNED),
            ('Cryo', 'Hydro'): (ReactionType.FREEZE, 0.5, StatusEffect.STUNNED),
            ('Cryo', 'Electro'): (ReactionType.SUPERCONDUCT, 1.2, StatusEffect.DEFENSE_DOWN),
            ('Electro', 'Cryo'): (ReactionType.SUPERCONDUCT, 1.2, StatusEffect.DEFENSE_DOWN),
            ('Pyro', 'Pyro'): (ReactionType.SAME_ELEMENT, 1.0, StatusEffect.NONE),
            ('Hydro', 'Hydro'): (ReactionType.SAME_ELEMENT, 1.0, StatusEffect.NONE),
            ('Cryo', 'Cryo'): (ReactionType.SAME_ELEMENT, 1.0, StatusEffect.NONE),
            ('Electro', 'Electro'): (ReactionType.SAME_ELEMENT, 1.0, StatusEffect.NONE),
        }

    @classmethod
    def get_reaction(cls, element1: str, element2: str) -> Tuple[ReactionType, float, StatusEffect]:
        return cls.REACTION_MAP.get((element1, element2), (ReactionType.NONE, 0.0, StatusEffect.NONE))

# ============================================================================
# PREDICTIVE AI
# ============================================================================

class PredictiveAI:
    def __init__(self):
        self.element_frequency: Dict[str, int] = defaultdict(int)

    def record_player_action(self, cards: List[Card]) -> None:
        for card in cards:
            self.element_frequency[card.element] += 1

    def get_counter_element(self, available_elements: List[str]) -> Optional[str]:
        if not self.element_frequency or not available_elements:
            return random.choice(available_elements) if available_elements else None

        most_used = max(self.element_frequency, key=self.element_frequency.get)
        counter_map = {
            'Pyro': ['Hydro', 'Cryo'],
            'Hydro': ['Electro'],
            'Cryo': ['Pyro', 'Electro'],
            'Electro': ['Pyro', 'Cryo'],
        }

        counters = counter_map.get(most_used, [])
        available_counters = [e for e in counters if e in available_elements]
        return random.choice(available_counters) if available_counters else random.choice(available_elements)

    def select_cards_for_attack(self, hand: List[Card]) -> Tuple[Card, Card]:
        if len(hand) < 2: return hand[0], hand[0]
        
        best_score = -1
        best_pair = (hand[0], hand[1])

        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                card1, card2 = hand[i], hand[j]
                _, multiplier, _ = ReactionMatrix.get_reaction(card1.element, card2.element)
                if multiplier > best_score:
                    best_score = multiplier
                    best_pair = (card1, card2)
        return best_pair

# ============================================================================
# GAME STATE MANAGER
# ============================================================================

class GameState:
    def __init__(self):
        self.phase = GamePhase.DRAFT
        self.turn_count = 0
        self.draft_pool: List[Card] = []
        self.player_hand: List[Card] = []
        self.ai_hand: List[Card] = []
        self.player_status = CharacterStatus(hp=200)
        self.ai_status = CharacterStatus(hp=200)
        self.ai = PredictiveAI()
        self.combat_log: List[str] = []
        self.game_winner: Optional[str] = None
        self.card_counter = 0
        self.base_damage = 20

    def generate_draft_pool(self) -> None:
        # Smart RNG: 12 Cards Total
        elements = ['Pyro', 'Hydro', 'Cryo', 'Electro']
        pool_elements = []
        
        # 1. Guarantee 2 of each element (8 cards)
        for el in elements:
            pool_elements.extend([el, el])
            
        # 2. Add 4 completely random elements to reach 12
        for _ in range(4):
            pool_elements.append(random.choice(elements))
            
        # 3. Shuffle them up!
        random.shuffle(pool_elements)
        
        self.draft_pool = []
        for element in pool_elements:
            self.draft_pool.append(Card(element=element, card_id=self.card_counter))
            self.card_counter += 1

    def start_draft_phase(self) -> None:
        self.phase = GamePhase.DRAFT
        self.player_hand.clear()
        self.ai_hand.clear()
        self.generate_draft_pool()
        self.combat_log.append(f"--- ROUND {self.turn_count + 1} DRAFT ---")

    def player_pick_card(self, card: Card) -> bool:
        if card not in self.draft_pool: return False
        self.draft_pool.remove(card)
        self.player_hand.append(card)
        
        # Check if hands have 6 cards to trigger Combat Phase
        if len(self.player_hand) == 6 and len(self.ai_hand) == 6:
            self.phase = GamePhase.CAST
            return True

        self.ai_pick_card()
        
        if len(self.player_hand) == 6 and len(self.ai_hand) == 6:
            self.phase = GamePhase.CAST
        return True

    def ai_pick_card(self) -> None:
        if not self.draft_pool: return
        available_elements = [c.element for c in self.draft_pool]
        pref = self.ai.get_counter_element(available_elements)
        pref_cards = [c for c in self.draft_pool if c.element == pref]
        selected = random.choice(pref_cards) if pref_cards else random.choice(self.draft_pool)
        self.draft_pool.remove(selected)
        self.ai_hand.append(selected)

    def execute_combat(self, card1: Card, card2: Card, is_player_turn: bool) -> None:
        attacker = "Player" if is_player_turn else "AI"
        defender = "AI" if is_player_turn else "Player"
        attacker_status = self.player_status if is_player_turn else self.ai_status
        defender_status = self.ai_status if is_player_turn else self.player_status

        # Remove cards from hand safely
        if is_player_turn:
            if card1 in self.player_hand: self.player_hand.remove(card1)
            if card2 in self.player_hand: self.player_hand.remove(card2)
            self.ai.record_player_action([card1, card2])
        else:
            if card1 in self.ai_hand: self.ai_hand.remove(card1)
            if card2 in self.ai_hand: self.ai_hand.remove(card2)

        reaction, multiplier, status = ReactionMatrix.get_reaction(card1.element, card2.element)
        damage = self.base_damage * multiplier

        self.combat_log.append(f"{attacker} cast {card1.element}+{card2.element}: {reaction.name}! (x{multiplier})")

        if reaction == ReactionType.VAPORIZE: attacker_status.clear_negative_effects()
        actual_damage = defender_status.take_damage(damage)
        
        if reaction == ReactionType.OVERLOAD:
            attacker_status.take_damage(damage * 0.1)

        if status == StatusEffect.STUNNED: defender_status.is_stunned_next_turn = True
        elif status == StatusEffect.DEFENSE_DOWN: defender_status.defense_modifier = 1.2

        if defender_status.hp <= 0:
            self.phase = GamePhase.GAME_OVER
            self.game_winner = attacker
            self.combat_log.append(f"*** {attacker} WINS! ***")
        elif is_player_turn and len(self.ai_hand) >= 2:
            self.player_status.reset_turn_status()
            c1, c2 = self.ai.select_cards_for_attack(self.ai_hand)
            self.execute_combat(c1, c2, False)
            self.ai_status.reset_turn_status()
        elif not is_player_turn:
            self.ai_status.reset_turn_status()