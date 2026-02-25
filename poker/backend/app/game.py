"""
Texas Hold'em Poker Game Logic
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import random
from datetime import datetime

from .config import Config

# Use config values for game constants
STARTING_CHIPS = Config.STARTING_CHIPS
SMALL_BLIND = Config.SMALL_BLIND
BIG_BLIND = Config.BIG_BLIND
MIN_RAISE = Config.MIN_RAISE

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

@dataclass
class Card:
    suit: Suit
    rank: Rank
    
    def __str__(self):
        rank_str = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}.get(self.rank.value, str(self.rank.value))
        return f"{rank_str}{self.suit.value}"
    
    def to_dict(self):
        return {
            'suit': self.suit.name,
            'rank': self.rank.value,
            'display': str(self)
        }

class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        random.shuffle(self.cards)
    
    def deal(self, count: int = 1) -> List[Card]:
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

@dataclass
class Player:
    id: str
    name: str
    chips: int
    hand: List[Card] = field(default_factory=list)
    bet: int = 0
    folded: bool = False
    is_all_in: bool = False
    is_human: bool = False
    
    def to_dict(self, show_cards: bool = False):
        return {
            'id': self.id,
            'name': self.name,
            'chips': self.chips,
            'hand': [c.to_dict() for c in self.hand] if show_cards else [],
            'bet': self.bet,
            'folded': self.folded,
            'is_all_in': self.is_all_in,
            'is_human': self.is_human
        }

@dataclass
class HandHistory:
    """Record of a completed hand"""
    hand_number: int
    timestamp: str
    players: List[Dict[str, Any]]  # Player snapshots at start
    community_cards: List[Dict[str, Any]]
    pot: int
    winners: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]  # Action log
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hand_number': self.hand_number,
            'timestamp': self.timestamp,
            'players': self.players,
            'community_cards': [f"{c['rank']}{c['suit']}" for c in self.community_cards],
            'pot': self.pot,
            'winners': self.winners,
        }


class PokerGame:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players: List[Player] = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot: int = 0
        self.current_bet: int = 0
        self.dealer_index: int = 0
        self.current_player_index: int = 0
        self.small_blind: int = SMALL_BLIND
        self.big_blind: int = BIG_BLIND
        self.phase: str = 'waiting'  # waiting, preflop, flop, turn, river, showdown
        self.round_bets: Dict[str, int] = {}  # Track bets per player for this round
        self.min_raise: int = MIN_RAISE
        self.winners: List[Dict] = []
        self.last_action: Optional[Dict] = None
        self.hand_number: int = 0
        
        # Hand history
        self.hand_history: List[HandHistory] = []
        self._current_hand_actions: List[Dict[str, Any]] = []
        self._current_hand_start: Optional[Dict[str, Any]] = None
    
    def add_player(self, name: str, is_human: bool = False) -> Player:
        player_id = f"p{len(self.players)}"
        player = Player(
            id=player_id,
            name=name,
            chips=STARTING_CHIPS,
            is_human=is_human
        )
        self.players.append(player)
        return player
    
    def start_hand(self):
        if len(self.players) < 2:
            return False
        
        self.hand_number += 1
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.phase = 'preflop'
        self.round_bets = {}
        self.winners = []
        self.last_action = None
        self._current_hand_actions = []
        
        # Reset players
        for player in self.players:
            player.hand = []
            player.bet = 0
            player.folded = False
            player.is_all_in = False
        
        # Deal cards
        for _ in range(2):
            for player in self.players:
                player.hand.extend(self.deck.deal(1))
        
        # Record starting state for history
        self._current_hand_start = {
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'chips': p.chips,
                    'hand': [c.to_dict() for c in p.hand],
                    'is_human': p.is_human
                }
                for p in self.players
            ],
            'dealer_index': self.dealer_index
        }
        
        # Post blinds
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)
        
        self._post_blind(self.players[sb_index], self.small_blind)
        self._post_blind(self.players[bb_index], self.big_blind)
        
        self.current_bet = self.big_blind
        self.current_player_index = (bb_index + 1) % len(self.players)
        self.min_raise = self.big_blind
        
        return True
    
    def _post_blind(self, player: Player, amount: int):
        actual_bet = min(amount, player.chips)
        player.chips -= actual_bet
        player.bet = actual_bet
        self.pot += actual_bet
        self.round_bets[player.id] = actual_bet
        
        if player.chips == 0:
            player.is_all_in = True
    
    def get_current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]
    
    def action_fold(self, player_id: str) -> bool:
        player = self._get_player(player_id)
        if not player or player.folded:
            return False
        
        player.folded = True
        self.last_action = {'player': player.name, 'action': 'fold'}
        self._log_action(player.name, 'fold')
        
        if self._is_round_complete():
            self._advance_phase()
        else:
            self._next_player()
        
        return True
    
    def action_check(self, player_id: str) -> bool:
        player = self._get_player(player_id)
        if not player or player.folded or player.is_all_in:
            return False
        
        if player.bet < self.current_bet:
            return False  # Can't check, must call or raise
        
        self.last_action = {'player': player.name, 'action': 'check'}
        self._log_action(player.name, 'check')
        
        if self._is_round_complete():
            self._advance_phase()
        else:
            self._next_player()
        
        return True
    
    def action_call(self, player_id: str) -> bool:
        player = self._get_player(player_id)
        if not player or player.folded or player.is_all_in:
            return False
        
        call_amount = self.current_bet - player.bet
        if call_amount <= 0:
            return self.action_check(player_id)
        
        actual_call = min(call_amount, player.chips)
        player.chips -= actual_call
        player.bet += actual_call
        self.pot += actual_call
        
        if player.chips == 0:
            player.is_all_in = True
            self.last_action = {'player': player.name, 'action': 'all-in'}
            self._log_action(player.name, 'all-in', actual_call)
        else:
            self.last_action = {'player': player.name, 'action': 'call', 'amount': actual_call}
            self._log_action(player.name, 'call', actual_call)
        
        if self._is_round_complete():
            self._advance_phase()
        else:
            self._next_player()
        
        return True
    
    def action_raise(self, player_id: str, amount: int) -> bool:
        player = self._get_player(player_id)
        if not player or player.folded or player.is_all_in:
            return False
        
        call_amount = self.current_bet - player.bet
        total_needed = call_amount + amount
        
        if amount < self.min_raise and player.chips > total_needed:
            return False  # Raise too small
        
        if player.chips <= total_needed:
            # All-in raise
            actual_raise = player.chips - call_amount
            player.chips = 0
            player.bet += call_amount + actual_raise
            self.pot += call_amount + actual_raise
            player.is_all_in = True
            
            if player.bet > self.current_bet:
                self.current_bet = player.bet
                self.min_raise = actual_raise
            
            self.last_action = {'player': player.name, 'action': 'all-in', 'amount': player.bet}
            self._log_action(player.name, 'all-in', player.bet)
        else:
            player.chips -= total_needed
            player.bet += total_needed
            self.pot += total_needed
            self.current_bet = player.bet
            self.min_raise = amount
            self.last_action = {'player': player.name, 'action': 'raise', 'amount': amount}
            self._log_action(player.name, 'raise', amount)
        
        if self._is_round_complete():
            self._advance_phase()
        else:
            self._next_player()
        
        return True
    
    def _get_player(self, player_id: str) -> Optional[Player]:
        for p in self.players:
            if p.id == player_id:
                return p
        return None
    
    def _log_action(self, player_name: str, action: str, amount: Optional[int] = None):
        """Log an action for hand history"""
        action_entry = {
            'phase': self.phase,
            'player': player_name,
            'action': action,
            'pot': self.pot,
            'timestamp': datetime.utcnow().isoformat()
        }
        if amount is not None:
            action_entry['amount'] = amount
        self._current_hand_actions.append(action_entry)
    
    def _next_player(self):
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            player = self.players[self.current_player_index]
            if not player.folded and not player.is_all_in:
                break
    
    def _is_round_complete(self) -> bool:
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) <= 1:
            return True
        
        # Check if all active players have matched the current bet
        for p in active_players:
            if not p.is_all_in and p.bet < self.current_bet:
                return False
        
        # Check if we've gone around once (current player has acted)
        # This is simplified - real poker tracks action more carefully
        return True
    
    def _advance_phase(self):
        active_players = [p for p in self.players if not p.folded]
        
        if len(active_players) == 1:
            # Everyone folded, hand is over
            self._award_pot([active_players[0]])
            self.phase = 'showdown'
            return
        
        # Reset bets for new round
        for p in self.players:
            p.bet = 0
        self.current_bet = 0
        self.min_raise = self.big_blind
        
        if self.phase == 'preflop':
            self.phase = 'flop'
            self.community_cards.extend(self.deck.deal(3))
        elif self.phase == 'flop':
            self.phase = 'turn'
            self.community_cards.extend(self.deck.deal(1))
        elif self.phase == 'turn':
            self.phase = 'river'
            self.community_cards.extend(self.deck.deal(1))
        elif self.phase == 'river':
            self.phase = 'showdown'
            self._evaluate_hands()
            return
        
        # Find first active player after dealer
        self.current_player_index = (self.dealer_index + 1) % len(self.players)
        while self.players[self.current_player_index].folded:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
    
    def _evaluate_hands(self):
        active_players = [p for p in self.players if not p.folded]
        
        if len(active_players) == 1:
            self._award_pot([active_players[0]])
            return
        
        # Evaluate each hand
        hand_evaluations = []
        for player in active_players:
            best_hand = self._get_best_hand(player.hand + self.community_cards)
            hand_evaluations.append((player, best_hand))
        
        # Sort by hand strength (highest first)
        hand_evaluations.sort(key=lambda x: x[1], reverse=True)
        
        # Find winners (could be tie)
        best_hand = hand_evaluations[0][1]
        winners = [p for p, h in hand_evaluations if h == best_hand]
        
        self._award_pot(winners)
    
    def _get_best_hand(self, cards: List[Card]) -> tuple:
        """Returns tuple (hand_rank, tiebreakers) for comparing hands"""
        from itertools import combinations
        
        best = (HandRank.HIGH_CARD.value, [0])
        
        for combo in combinations(cards, 5):
            rank = self._evaluate_five_card_hand(list(combo))
            if rank > best:
                best = rank
        
        return best
    
    def _evaluate_five_card_hand(self, cards: List[Card]) -> tuple:
        """Evaluate a 5-card hand and return (rank, tiebreakers)"""
        ranks = sorted([c.rank.value for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        
        is_flush = len(set(suits)) == 1
        is_straight = self._is_straight(ranks)
        
        # Royal Flush / Straight Flush
        if is_flush and is_straight:
            if ranks[0] == 14:  # Ace high
                return (HandRank.ROYAL_FLUSH.value, [])
            return (HandRank.STRAIGHT_FLUSH.value, [ranks[0]])
        
        # Count ranks
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Four of a Kind
        if counts[0] == 4:
            quad_rank = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r in ranks if r != quad_rank][0]
            return (HandRank.FOUR_OF_A_KIND.value, [quad_rank, kicker])
        
        # Full House
        if counts[0] == 3 and counts[1] == 2:
            trip_rank = [r for r, c in rank_counts.items() if c == 3][0]
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            return (HandRank.FULL_HOUSE.value, [trip_rank, pair_rank])
        
        # Flush
        if is_flush:
            return (HandRank.FLUSH.value, ranks)
        
        # Straight
        if is_straight:
            return (HandRank.STRAIGHT.value, [ranks[0]])
        
        # Three of a Kind
        if counts[0] == 3:
            trip_rank = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = [r for r in ranks if r != trip_rank]
            return (HandRank.THREE_OF_A_KIND.value, [trip_rank] + kickers)
        
        # Two Pair
        if counts[0] == 2 and counts[1] == 2:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r in ranks if r not in pairs][0]
            return (HandRank.TWO_PAIR.value, pairs + [kicker])
        
        # Pair
        if counts[0] == 2:
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = [r for r in ranks if r != pair_rank]
            return (HandRank.PAIR.value, [pair_rank] + kickers)
        
        # High Card
        return (HandRank.HIGH_CARD.value, ranks)
    
    def _is_straight(self, ranks: List[int]) -> bool:
        unique = sorted(set(ranks), reverse=True)
        if len(unique) < 5:
            return False
        
        # Check for regular straight
        for i in range(len(unique) - 4):
            if unique[i] - unique[i+4] == 4:
                return True
        
        # Check for A-5 straight (wheel)
        if set([14, 2, 3, 4, 5]).issubset(unique):
            return True
        
        return False
    
    def _award_pot(self, winners: List[Player]):
        split_amount = self.pot // len(winners)
        remainder = self.pot % len(winners)
        
        for i, winner in enumerate(winners):
            amount = split_amount + (1 if i < remainder else 0)
            winner.chips += amount
        
        self.winners = [{
            'id': w.id,
            'name': w.name,
            'amount': split_amount + (1 if i < remainder else 0),
            'hand': [c.to_dict() for c in w.hand]
        } for i, w in enumerate(winners)]
        
        # Save hand to history
        self._save_hand_history()
    
    def _save_hand_history(self):
        """Save the completed hand to history"""
        if not self._current_hand_start:
            return
        
        hand_record = HandHistory(
            hand_number=self.hand_number,
            timestamp=datetime.utcnow().isoformat(),
            players=self._current_hand_start['players'],
            community_cards=[c.to_dict() for c in self.community_cards],
            pot=self.pot,
            winners=self.winners,
            actions=self._current_hand_actions.copy()
        )
        
        self.hand_history.append(hand_record)
        
        # Clear current hand data
        self._current_hand_start = None
        self._current_hand_actions = []
    
    def get_hand_history(self) -> List[Dict[str, Any]]:
        """Get list of completed hands"""
        return [h.to_dict() for h in self.hand_history]
    
    def to_dict(self, for_player: Optional[str] = None) -> dict:
        """Convert game state to dict for API response"""
        return {
            'game_id': self.game_id,
            'phase': self.phase,
            'pot': self.pot,
            'current_bet': self.current_bet,
            'community_cards': [c.to_dict() for c in self.community_cards],
            'players': [p.to_dict(show_cards=for_player == p.id or self.phase == 'showdown') for p in self.players],
            'current_player': self.get_current_player().id if self.get_current_player() else None,
            'dealer_index': self.dealer_index,
            'winners': self.winners,
            'last_action': self.last_action,
            'hand_number': self.hand_number,
            'min_raise': self.min_raise
        }
