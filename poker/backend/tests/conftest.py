"""
Pytest configuration and shared fixtures for poker tests
"""
import pytest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.game import PokerGame, Player, Card, Deck, Suit, Rank, HandRank


@pytest.fixture
def game():
    """Create a fresh poker game for testing"""
    return PokerGame("test-game-123")


@pytest.fixture
def populated_game():
    """Create a game with 4 players"""
    game = PokerGame("test-game-456")
    game.add_player("Alice", is_human=True)
    game.add_player("Bob", is_human=False)
    game.add_player("Charlie", is_human=False)
    game.add_player("Diana", is_human=False)
    return game


@pytest.fixture
def sample_cards():
    """Sample cards for testing"""
    return {
        "ace_spades": Card(Suit.SPADES, Rank.ACE),
        "king_hearts": Card(Suit.HEARTS, Rank.KING),
        "queen_diamonds": Card(Suit.DIAMONDS, Rank.QUEEN),
        "jack_clubs": Card(Suit.CLUBS, Rank.JACK),
        "ten_spades": Card(Suit.SPADES, Rank.TEN),
        "five_hearts": Card(Suit.HEARTS, Rank.FIVE),
        "two_clubs": Card(Suit.CLUBS, Rank.TWO),
    }
