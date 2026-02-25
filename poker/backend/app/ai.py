"""
AI Bot for Texas Hold'em Poker
"""
import random
from typing import Optional, Dict, Any, List, Tuple
from .game import PokerGame, Player, Card, HandRank

class AIDifficulty:
    """AI difficulty presets with configurable parameters"""
    
    EASY = {
        "name": "easy",
        "aggression": 0.2,
        "bluff_frequency": 0.05,
        "hand_strength_threshold": 0.6,  # Needs stronger hands to continue
        "raise_multiplier": 1.0,  # Minimum raises
        "fold_to_raise": 0.4,  # Often folds to raises
        "call_threshold": 0.5,  # Needs 50%+ equity to call
    }
    
    MEDIUM = {
        "name": "medium",
        "aggression": 0.5,
        "bluff_frequency": 0.15,
        "hand_strength_threshold": 0.45,
        "raise_multiplier": 1.5,
        "fold_to_raise": 0.25,
        "call_threshold": 0.35,
    }
    
    HARD = {
        "name": "hard",
        "aggression": 0.7,
        "bluff_frequency": 0.25,
        "hand_strength_threshold": 0.35,
        "raise_multiplier": 2.0,
        "fold_to_raise": 0.15,
        "call_threshold": 0.25,
    }
    
    EXPERT = {
        "name": "expert",
        "aggression": 0.85,
        "bluff_frequency": 0.35,
        "hand_strength_threshold": 0.25,  # Can play weaker hands
        "raise_multiplier": 3.0,  # Larger raises for pressure
        "fold_to_raise": 0.08,  # Rarely folds to raises
        "call_threshold": 0.18,  # Calls with thinner equity
    }
    
    @classmethod
    def get_preset(cls, difficulty: str) -> Dict[str, Any]:
        """Get difficulty preset by name"""
        presets = {
            "easy": cls.EASY,
            "medium": cls.MEDIUM,
            "hard": cls.HARD,
            "expert": cls.EXPERT,
        }
        return presets.get(difficulty.lower(), cls.MEDIUM)


class PokerAI:
    """Poker AI with configurable difficulty levels"""
    
    def __init__(self, aggression: float = 0.5, difficulty: Optional[str] = None):
        """
        Initialize AI with either legacy aggression or new difficulty preset.
        
        Args:
            aggression: Legacy parameter (0 = tight, 1 = loose) - used if difficulty not set
            difficulty: Difficulty level - 'easy', 'medium', 'hard', 'expert'
        """
        if difficulty:
            self.config = AIDifficulty.get_preset(difficulty)
            self.aggression = self.config["aggression"]
        else:
            self.aggression = aggression
            self.config = {
                "name": "custom",
                "aggression": aggression,
                "bluff_frequency": aggression * 0.3,
                "hand_strength_threshold": 0.5 - (aggression * 0.2),
                "raise_multiplier": 1.0 + aggression,
                "fold_to_raise": 0.3 - (aggression * 0.2),
                "call_threshold": 0.4 - (aggression * 0.2),
            }
    
    def make_decision(self, game: PokerGame, player: Player) -> Dict[str, Any]:
        """Returns action dict with 'action' and optional 'amount'"""
        hand_strength = self._estimate_hand_strength(game, player)
        pot_odds = self._calculate_pot_odds(game, player)
        to_call = game.current_bet - player.bet
        cfg = self.config
        
        # Calculate effective pot odds including implied odds
        effective_pot_odds = pot_odds * (1.0 - cfg["aggression"] * 0.2)
        
        # Very strong hand - raise or all-in
        strong_threshold = 0.85 - (cfg["aggression"] * 0.1)
        if hand_strength > strong_threshold:
            if player.chips > to_call + game.min_raise:
                # Use difficulty-based raise sizing
                raise_multiplier = cfg["raise_multiplier"]
                raise_amount = min(
                    player.chips - to_call,
                    max(int(game.min_raise * raise_multiplier), int(game.pot * 0.75))
                )
                return {'action': 'raise', 'amount': raise_amount}
            elif player.chips > to_call:
                return {'action': 'all-in'}
            else:
                return {'action': 'call'}
        
        # Strong hand - raise or call
        medium_strong_threshold = cfg["hand_strength_threshold"] + 0.25
        if hand_strength > medium_strong_threshold:
            # More likely to raise with higher aggression
            raise_chance = cfg["aggression"] * 0.8
            if random.random() < raise_chance and player.chips > to_call + game.min_raise:
                raise_amount = min(
                    int(game.min_raise * cfg["raise_multiplier"]), 
                    player.chips - to_call
                )
                return {'action': 'raise', 'amount': raise_amount}
            elif to_call == 0:
                return {'action': 'check'}
            else:
                return {'action': 'call'}
        
        # Medium hand - call if good pot odds, otherwise fold
        if hand_strength > cfg["hand_strength_threshold"]:
            if to_call == 0:
                return {'action': 'check'}
            elif pot_odds > cfg["call_threshold"] or hand_strength > pot_odds * 1.5:
                return {'action': 'call'}
            else:
                return {'action': 'fold'}
        
        # Weak hand - fold unless free to check or bluffing
        if to_call == 0:
            # Bluff based on difficulty bluff frequency
            if random.random() < cfg["bluff_frequency"]:
                raise_amount = min(
                    int(game.min_raise * cfg["raise_multiplier"]), 
                    player.chips
                )
                return {'action': 'raise', 'amount': raise_amount}
            return {'action': 'check'}
        
        # Occasional bluff call with weak hand (hero call)
        if random.random() < cfg["bluff_frequency"] * 0.3:
            return {'action': 'call'}
        
        return {'action': 'fold'}
    
    def _estimate_hand_strength(self, game: PokerGame, player: Player) -> float:
        """Estimate hand strength from 0-1 using Monte Carlo simulation"""
        from .game import Deck
        
        if game.phase == 'preflop':
            return self._preflop_strength(player.hand)
        
        # Run Monte Carlo simulation
        wins = 0
        trials = 100
        
        known_cards = player.hand + game.community_cards
        deck = Deck()
        deck.cards = [c for c in deck.cards if c not in known_cards]
        
        for _ in range(trials):
            deck_copy = deck.cards.copy()
            random.shuffle(deck_copy)
            
            # Complete community cards
            remaining_community = 5 - len(game.community_cards)
            simulated_community = game.community_cards + deck_copy[:remaining_community]
            
            # Opponent hand
            opponent_hand = deck_copy[remaining_community:remaining_community+2]
            
            # Compare hands
            my_best = game._get_best_hand(player.hand + simulated_community)
            opp_best = game._get_best_hand(opponent_hand + simulated_community)
            
            if my_best > opp_best:
                wins += 1
            elif my_best == opp_best:
                wins += 0.5
        
        return wins / trials
    
    def _preflop_strength(self, hand: List[Card]) -> float:
        """Quick estimate of preflop hand strength"""
        if len(hand) != 2:
            return 0.5
        
        r1, r2 = hand[0].rank.value, hand[1].rank.value
        suited = hand[0].suit == hand[1].suit
        
        # Premium pairs
        if r1 == r2:
            if r1 >= 10:
                return 0.9
            elif r1 >= 7:
                return 0.75
            else:
                return 0.5 + (r1 / 20)
        
        # High cards
        high = max(r1, r2)
        low = min(r1, r2)
        
        # AK, AQ, AJ, AT
        if high == 14:
            if low >= 10:
                return 0.8 if suited else 0.7
            elif low >= 8:
                return 0.65 if suited else 0.55
        
        # KQ, KJ, QJ
        if high == 13 and low >= 11:
            return 0.65 if suited else 0.55
        
        # Suited connectors
        if suited and abs(r1 - r2) <= 2 and high >= 10:
            return 0.6
        
        # Any suited
        if suited and high >= 10:
            return 0.5
        
        # Weak hand
        return 0.3 + (high / 50)
    
    def _calculate_pot_odds(self, game: PokerGame, player: Player) -> float:
        """Calculate pot odds (what % of pot we need to call)"""
        to_call = game.current_bet - player.bet
        if to_call <= 0:
            return 1.0  # Free to check
        
        return to_call / (game.pot + to_call)


class AIManager:
    """Manages AI bots for a poker game"""
    
    # Default bot configurations with difficulty levels
    DEFAULT_BOTS = [
        ("Alex", "easy"),
        ("Bob", "medium"),
        ("Charlie", "hard"),
        ("Diana", "hard"),
        ("Eve", "medium"),
    ]
    
    def __init__(self, game: PokerGame):
        self.game = game
        self.bots: Dict[str, PokerAI] = {}
    
    def add_bot(self, name: str, aggression: Optional[float] = None, 
                difficulty: Optional[str] = None) -> Player:
        """
        Add an AI bot to the game.
        
        Args:
            name: Display name for the bot
            aggression: Legacy aggression parameter (0-1)
            difficulty: Difficulty preset ('easy', 'medium', 'hard', 'expert')
        
        Returns:
            The created Player object
        """
        player = self.game.add_player(name, is_human=False)
        
        if difficulty:
            self.bots[player.id] = PokerAI(difficulty=difficulty)
        elif aggression is not None:
            self.bots[player.id] = PokerAI(aggression=aggression)
        else:
            # Default to medium difficulty
            self.bots[player.id] = PokerAI(difficulty="medium")
        
        return player
    
    def add_default_bots(self) -> List[Player]:
        """Add the default set of 5 bots with varied difficulties"""
        players = []
        for name, difficulty in self.DEFAULT_BOTS:
            player = self.add_bot(name, difficulty=difficulty)
            players.append(player)
        return players
    
    def process_bot_turn(self) -> Optional[Dict[str, Any]]:
        """Process the current bot's turn if it's an AI"""
        current = self.game.get_current_player()
        
        if not current or current.is_human:
            return None
        
        if current.id not in self.bots:
            return None
        
        bot = self.bots[current.id]
        decision = bot.make_decision(self.game, current)
        
        # Execute the decision
        if decision['action'] == 'fold':
            self.game.action_fold(current.id)
        elif decision['action'] == 'check':
            self.game.action_check(current.id)
        elif decision['action'] == 'call':
            self.game.action_call(current.id)
        elif decision['action'] == 'raise':
            self.game.action_raise(current.id, decision['amount'])
        elif decision['action'] == 'all-in':
            to_call = self.game.current_bet - current.bet
            all_in_amount = current.chips - to_call
            self.game.action_raise(current.id, all_in_amount)
        
        return decision
