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
    """Poker AI with configurable difficulty levels and human-like tells"""
    
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
        
        # AI tells - behavioral patterns that make AI more human-like
        self.tells = {
            "timing_pattern": random.choice(["fast", "normal", "deliberate", "tanker"]),
            "betting_style": random.choice(["precise", "rounded", "psychological"]),
            "bluff_reveal_tendency": random.random() * 0.3,  # Chance to show bluff when winning
            "chat_frequency": random.random() * 0.2,  # Chance to send chat message
        }
        
        # Decision history for pattern analysis
        self.decision_history: List[Dict[str, Any]] = []
        self.hands_played = 0
        self.hands_won = 0
        
    def get_decision_delay(self, hand_strength: float, decision_type: str) -> float:
        """
        Calculate human-like decision delay based on hand strength and decision type.
        Returns delay in seconds.
        """
        import random
        
        base_delay = 0.5
        
        # Timing tell patterns
        if self.tells["timing_pattern"] == "fast":
            base_delay = 0.3
        elif self.tells["timing_pattern"] == "deliberate":
            base_delay = 1.2
        elif self.tells["timing_pattern"] == "tanker":
            base_delay = 2.0
        
        # Adjust based on decision type and hand strength
        if decision_type == "fold":
            # Quick folds with weak hands, sometimes tank with medium hands
            if hand_strength < 0.3:
                delay = base_delay * 0.5 + random.uniform(0, 0.3)
            else:
                delay = base_delay * 1.5 + random.uniform(0, 1.0)
        elif decision_type == "call":
            # Calls take moderate time, longer with marginal hands
            if hand_strength < 0.5:
                delay = base_delay * 1.5 + random.uniform(0, 1.5)
            else:
                delay = base_delay + random.uniform(0, 0.5)
        elif decision_type == "raise":
            # Raises can be quick (value) or slow (deciding bet size)
            if hand_strength > 0.8:
                delay = base_delay * 0.8 + random.uniform(0, 0.5)
            else:
                delay = base_delay * 1.8 + random.uniform(0, 1.0)
        else:
            delay = base_delay + random.uniform(0, 0.5)
        
        # Add some randomness for realism
        delay += random.gauss(0, 0.2)
        
        return max(0.1, delay)
    
    def get_bet_size(self, base_amount: int, game: PokerGame, hand_strength: float) -> int:
        """
        Apply betting style patterns to determine final bet size.
        Makes AI betting look more human and less algorithmic.
        """
        import random
        
        style = self.tells["betting_style"]
        
        if style == "precise":
            # Bets exact calculated amounts (slight randomization)
            variance = random.uniform(0.95, 1.05)
            return int(base_amount * variance)
        
        elif style == "rounded":
            # Bets nice round numbers
            if base_amount < 100:
                return round(base_amount / 5) * 5
            elif base_amount < 500:
                return round(base_amount / 25) * 25
            else:
                return round(base_amount / 50) * 50
        
        elif style == "psychological":
            # Bets to create specific psychological effects
            pot = game.pot
            to_call = game.current_bet
            
            # Just over the pot (looks strong)
            if random.random() < 0.3 and base_amount > pot * 0.8:
                return int(pot * 1.1) + random.randint(1, 10)
            
            # Just enough to make it "hard to call" (uncomfortable number)
            if to_call > 0 and random.random() < 0.2:
                uncomfortable = to_call + int(base_amount * 1.1) + random.randint(1, 5)
                return uncomfortable
            
            # Standard sizing
            return base_amount
        
        return base_amount
    
    def record_decision(self, decision: Dict[str, Any], hand_strength: float, 
                       game_phase: str, was_winner: bool = False):
        """Record decision for pattern analysis"""
        self.decision_history.append({
            "decision": decision,
            "hand_strength": hand_strength,
            "phase": game_phase,
            "was_winner": was_winner,
        })
        
        if was_winner:
            self.hands_won += 1
        
        # Keep only last 50 decisions
        if len(self.decision_history) > 50:
            self.decision_history = self.decision_history[-50:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI stats and tendencies"""
        if not self.decision_history:
            return {
                "hands_played": self.hands_played,
                "hands_won": self.hands_won,
                "win_rate": 0,
                "avg_hand_strength": 0,
                "fold_frequency": 0,
                "raise_frequency": 0,
            }
        
        total = len(self.decision_history)
        folds = sum(1 for d in self.decision_history if d["decision"].get("action") == "fold")
        raises = sum(1 for d in self.decision_history if d["decision"].get("action") == "raise")
        avg_strength = sum(d["hand_strength"] for d in self.decision_history) / total
        
        return {
            "hands_played": self.hands_played,
            "hands_won": self.hands_won,
            "win_rate": self.hands_won / max(1, self.hands_played),
            "avg_hand_strength": round(avg_strength, 3),
            "fold_frequency": round(folds / total, 3),
            "raise_frequency": round(raises / total, 3),
            "timing_pattern": self.tells["timing_pattern"],
            "betting_style": self.tells["betting_style"],
        }
    
    def make_decision(self, game: PokerGame, player: Player) -> Dict[str, Any]:
        """Returns action dict with 'action' and optional 'amount'"""
        hand_strength = self._estimate_hand_strength(game, player)
        pot_odds = self._calculate_pot_odds(game, player)
        to_call = game.current_bet - player.bet
        cfg = self.config
        
        # Calculate effective pot odds including implied odds
        effective_pot_odds = pot_odds * (1.0 - cfg["aggression"] * 0.2)
        
        # Get stack size and positional factors
        stack_factor = self._calculate_stack_factor(game, player)
        position_factor = self._calculate_position_factor(game, player)
        
        # Adjust thresholds based on stack and position
        adjusted_strength_threshold = cfg["hand_strength_threshold"] * stack_factor * position_factor
        adjusted_call_threshold = cfg["call_threshold"] * stack_factor * position_factor
        
        decision = None
        
        # Very strong hand - raise or all-in
        strong_threshold = 0.85 - (cfg["aggression"] * 0.1)
        if hand_strength > strong_threshold:
            if player.chips > to_call + game.min_raise:
                # Use difficulty-based raise sizing
                raise_multiplier = cfg["raise_multiplier"]
                base_raise = min(
                    player.chips - to_call,
                    max(int(game.min_raise * raise_multiplier), int(game.pot * 0.75))
                )
                raise_amount = self.get_bet_size(base_raise, game, hand_strength)
                decision = {'action': 'raise', 'amount': raise_amount}
            elif player.chips > to_call:
                decision = {'action': 'all-in'}
            else:
                decision = {'action': 'call'}
        
        # Strong hand - raise or call
        if decision is None:
            medium_strong_threshold = adjusted_strength_threshold + 0.25
            if hand_strength > medium_strong_threshold:
                # More likely to raise with higher aggression
                raise_chance = cfg["aggression"] * 0.8
                if random.random() < raise_chance and player.chips > to_call + game.min_raise:
                    base_raise = min(
                        int(game.min_raise * cfg["raise_multiplier"]), 
                        player.chips - to_call
                    )
                    raise_amount = self.get_bet_size(base_raise, game, hand_strength)
                    decision = {'action': 'raise', 'amount': raise_amount}
                elif to_call == 0:
                    decision = {'action': 'check'}
                else:
                    decision = {'action': 'call'}
        
        # Medium hand - call if good pot odds, otherwise fold
        if decision is None:
            if hand_strength > adjusted_strength_threshold:
                if to_call == 0:
                    decision = {'action': 'check'}
                elif pot_odds > adjusted_call_threshold or hand_strength > pot_odds * 1.5:
                    decision = {'action': 'call'}
                else:
                    decision = {'action': 'fold'}
        
        # Weak hand - fold unless free to check or bluffing
        if decision is None:
            if to_call == 0:
                # Bluff based on difficulty bluff frequency
                if random.random() < cfg["bluff_frequency"]:
                    base_raise = min(
                        int(game.min_raise * cfg["raise_multiplier"]), 
                        player.chips
                    )
                    raise_amount = self.get_bet_size(base_raise, game, hand_strength)
                    decision = {'action': 'raise', 'amount': raise_amount}
                else:
                    decision = {'action': 'check'}
            else:
                # Occasional bluff call with weak hand (hero call)
                if random.random() < cfg["bluff_frequency"] * 0.3:
                    decision = {'action': 'call'}
                else:
                    decision = {'action': 'fold'}
        
        # Record the decision for pattern analysis
        self.record_decision(decision, hand_strength, game.phase)
        
        return decision
    
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
    
    def _calculate_stack_factor(self, game: PokerGame, player: Player) -> float:
        """
        Calculate stack size factor for decision adjustment.
        Short stacks should play tighter, deep stacks can play more speculative hands.
        Returns a multiplier between 0.7 (very short) and 1.3 (very deep).
        """
        # Calculate stack in big blinds
        bb_stack = player.chips / game.big_blind if game.big_blind > 0 else player.chips / 20
        
        # Very short stack (< 10 BB) - desperation mode, play tighter but shove stronger hands
        if bb_stack < 10:
            return 0.7  # Tighten up significantly, only premium hands
        
        # Short stack (10-20 BB) - cautious play
        elif bb_stack < 20:
            return 0.85
        
        # Medium stack (20-50 BB) - standard play
        elif bb_stack < 50:
            return 1.0
        
        # Deep stack (50-100 BB) - can play more speculative hands
        elif bb_stack < 100:
            return 1.15
        
        # Very deep stack (> 100 BB) - lots of room for post-flop play
        else:
            return 1.3
    
    def _calculate_position_factor(self, game: PokerGame, player: Player) -> float:
        """
        Calculate positional factor for decision adjustment.
        Late position (closer to button) allows looser play.
        Returns a multiplier between 0.85 (early) and 1.25 (late position/button).
        """
        if not game.players:
            return 1.0
        
        # Find player position relative to dealer
        num_players = len(game.players)
        dealer_pos = game.dealer_index
        
        # Find player's position
        player_pos = -1
        for i, p in enumerate(game.players):
            if p.id == player.id:
                player_pos = i
                break
        
        if player_pos == -1:
            return 1.0
        
        # Calculate position relative to dealer (0 = button, higher = earlier)
        # Position 0 = dealer/button (best position)
        # Position num_players-1 = small blind (worst position post-flop)
        pos_from_button = (player_pos - dealer_pos) % num_players
        
        # Button/Dealer (0)
        if pos_from_button == 0:
            return 1.25  # Can play loosest from button
        
        # Cutoff (1 away from button)
        elif pos_from_button == 1:
            return 1.15
        
        # Hijack (2 away from button)
        elif pos_from_button == 2:
            return 1.05
        
        # Early position (3-4 away from button)
        elif pos_from_button <= 4:
            return 0.9  # Play tighter early
        
        # Blinds (worst position post-flop)
        else:
            return 0.85  # Play tightest from blinds


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
    
    async def process_bot_turn_async(self) -> Optional[Dict[str, Any]]:
        """Process the current bot's turn with human-like timing delays"""
        import asyncio
        
        current = self.game.get_current_player()
        
        if not current or current.is_human:
            return None
        
        if current.id not in self.bots:
            return None
        
        bot = self.bots[current.id]
        
        # Make decision first to know what delay to apply
        decision = bot.make_decision(self.game, current)
        
        # Estimate hand strength for timing calculation
        hand_strength = bot._estimate_hand_strength(self.game, current)
        
        # Calculate and apply human-like delay
        delay = bot.get_decision_delay(hand_strength, decision['action'])
        await asyncio.sleep(delay)
        
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
    
    def process_bot_turn(self) -> Optional[Dict[str, Any]]:
        """Process the current bot's turn if it's an AI (synchronous version)"""
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
    
    def get_bot_stats(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific bot"""
        if bot_id in self.bots:
            return self.bots[bot_id].get_stats()
        return None
    
    def get_all_bot_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all bots"""
        stats = {}
        for player in self.game.players:
            if not player.is_human and player.id in self.bots:
                stats[player.name] = self.bots[player.id].get_stats()
        return stats
