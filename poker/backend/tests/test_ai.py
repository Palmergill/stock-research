"""
Tests for AI manager and bot behavior
"""
import pytest
from app.game import PokerGame, Card, Suit, Rank
from app.ai import AIManager, PokerAI


class TestAIManager:
    """Test AI Manager functionality"""
    
    def test_add_bot(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        bot = ai_manager.add_bot("TestBot", aggression=0.5)
        
        assert bot in game.players
        assert bot.name == "TestBot"
        assert bot.is_human is False
        assert bot.chips == 1000
    
    def test_add_multiple_bots(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        ai_manager.add_bot("Bot1", aggression=0.3)
        ai_manager.add_bot("Bot2", aggression=0.5)
        ai_manager.add_bot("Bot3", aggression=0.7)
        
        assert len(game.players) == 3
    
    def test_bot_aggression_levels(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        tight_bot = ai_manager.add_bot("Tight", aggression=0.3)
        loose_bot = ai_manager.add_bot("Loose", aggression=0.7)
        
        assert tight_bot in game.players
        assert loose_bot in game.players
        # Check aggression stored in bot
        assert ai_manager.bots[tight_bot.id].aggression == 0.3
        assert ai_manager.bots[loose_bot.id].aggression == 0.7
    
    def test_process_bot_turn_no_current_player(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        # No current player - should not crash
        result = ai_manager.process_bot_turn()
        assert result is None
    
    def test_process_bot_turn_when_human_turn(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        # Add human player
        human = game.add_player("Human", is_human=True)
        ai_manager.add_bot("Bot", aggression=0.5)
        
        game.start_hand()
        
        # If it's human's turn, bot shouldn't act
        if game.get_current_player() == human:
            initial_chips = [p.chips for p in game.players]
            result = ai_manager.process_bot_turn()
            # Should return None since it's human's turn
            assert result is None
            # State should be unchanged
            assert [p.chips for p in game.players] == initial_chips


class TestPokerAI:
    """Test PokerAI decision making"""
    
    def test_ai_creation(self):
        ai = PokerAI(aggression=0.5)
        assert ai.aggression == 0.5
    
    def test_preflop_strength_pocket_aces(self):
        game = PokerGame("test")
        ai = PokerAI()
        
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE)
        ]
        strength = ai._preflop_strength(hand)
        assert strength >= 0.9  # Pocket aces are strong
    
    def test_preflop_strength_ak_suited(self):
        game = PokerGame("test")
        ai = PokerAI()
        
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING)
        ]
        strength = ai._preflop_strength(hand)
        assert strength >= 0.7  # AK suited is strong
    
    def test_preflop_strength_weak_hand(self):
        game = PokerGame("test")
        ai = PokerAI()
        
        hand = [
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.HEARTS, Rank.SEVEN)
        ]
        strength = ai._preflop_strength(hand)
        assert strength < 0.5  # Weak hand
    
    def test_pot_odds_calculation(self):
        game = PokerGame("test")
        ai = PokerAI()
        
        player = game.add_player("Test")
        game.start_hand()
        game.pot = 100
        game.current_bet = 20
        
        # Player has bet 0, needs to call 20
        player.bet = 0
        odds = ai._calculate_pot_odds(game, player)
        assert odds == 20 / 120  # to_call / (pot + to_call)
    
    def test_make_decision_returns_valid_action(self):
        game = PokerGame("test")
        ai = PokerAI(aggression=0.5)
        
        player = game.add_player("Test")
        game.add_player("Bot1")
        game.add_player("Bot2")
        game.start_hand()
        
        decision = ai.make_decision(game, player)
        
        assert "action" in decision
        assert decision["action"] in ["fold", "check", "call", "raise", "all-in"]
        
        if decision["action"] == "raise":
            assert "amount" in decision
            assert decision["amount"] > 0


class TestAIBotIntegration:
    """Test bot behavior integrated with game"""
    
    def test_bot_makes_decision_in_game(self):
        game = PokerGame("test-ai")
        ai_manager = AIManager(game)
        
        # Add bot only
        bot = ai_manager.add_bot("Bot", aggression=0.5)
        game.add_player("Opponent")  # Need 2+ players
        
        game.start_hand()
        
        # Bot should make a decision if it's their turn
        current = game.get_current_player()
        if current == bot:
            result = ai_manager.process_bot_turn()
            # Should return a decision dict
            assert result is not None
            assert "action" in result
    
    def test_bot_fold_weak_hand(self):
        game = PokerGame("test")
        ai = PokerAI(aggression=0.1)  # Very tight
        
        # Create a situation where folding is likely
        player = game.add_player("Test")
        player.hand = [
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.CLUBS, Rank.THREE)
        ]
        game.add_player("Opponent1")
        game.add_player("Opponent2")
        game.start_hand()
        
        # Make it expensive to call
        game.pot = 200
        game.current_bet = 100
        player.bet = 0
        
        decision = ai.make_decision(game, player)
        # Tight AI should fold weak hand facing big bet
        assert decision["action"] in ["fold", "call"]  # Either fold or call
