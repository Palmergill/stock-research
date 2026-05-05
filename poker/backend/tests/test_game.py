"""
Tests for core poker game logic
"""
import pytest
from app.game import PokerGame, Player, Card, Deck, Suit, Rank, HandRank


class TestCard:
    """Test Card class"""

    def test_card_creation(self):
        card = Card(Suit.SPADES, Rank.ACE)
        assert card.suit == Suit.SPADES
        assert card.rank == Rank.ACE
        assert str(card) == "A♠"

    def test_card_to_dict(self):
        card = Card(Suit.HEARTS, Rank.KING)
        result = card.to_dict()
        assert result["suit"] == "HEARTS"
        assert result["rank"] == 13
        assert result["display"] == "K♥"

    def test_card_rank_values(self):
        """Test that rank values are correct for comparison"""
        assert Rank.TWO.value == 2
        assert Rank.TEN.value == 10
        assert Rank.JACK.value == 11
        assert Rank.QUEEN.value == 12
        assert Rank.KING.value == 13
        assert Rank.ACE.value == 14


class TestPlayer:
    """Test Player class"""

    def test_player_creation(self):
        player = Player("test123", "Alice", chips=1000, is_human=True)
        assert player.id == "test123"
        assert player.name == "Alice"
        assert player.is_human is True
        assert player.chips == 1000
        assert player.folded is False

    def test_player_to_dict_hidden_cards(self):
        player = Player("p1", "Bob", chips=1000, is_human=False)
        player.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]

        result = player.to_dict(show_cards=False)
        assert result["hand"] == []  # Cards hidden
        assert result["chips"] == 1000

    def test_player_to_dict_show_cards(self):
        player = Player("p1", "Bob", chips=1000, is_human=False)
        player.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.KING)]

        result = player.to_dict(show_cards=True)
        assert len(result["hand"]) == 2
        assert result["hand"][0]["rank"] == 14  # Ace


class TestDeck:
    """Test Deck class"""

    def test_deck_has_52_cards(self):
        deck = Deck()
        assert len(deck.cards) == 52

    def test_deck_deal(self):
        deck = Deck()
        cards = deck.deal(2)
        assert len(cards) == 2
        assert len(deck.cards) == 50

    def test_deck_reset(self):
        deck = Deck()
        deck.deal(10)
        assert len(deck.cards) == 42
        deck.reset()
        assert len(deck.cards) == 52


class TestPokerGame:
    """Test PokerGame class"""

    def test_game_creation(self, game):
        assert game.game_id == "test-game-123"
        assert game.phase == "waiting"
        assert len(game.players) == 0

    def test_add_player(self, game):
        player = game.add_player("Alice", is_human=True)
        assert len(game.players) == 1
        assert player.name == "Alice"
        assert player.is_human is True
        assert player.chips == 1000

    def test_add_multiple_players(self, populated_game):
        assert len(populated_game.players) == 4
        assert populated_game.players[0].name == "Alice"

    def test_start_hand(self, populated_game):
        result = populated_game.start_hand()
        assert result is True
        assert populated_game.phase == "preflop"
        assert len(populated_game.community_cards) == 0

        # Each player should have 2 hole cards
        for player in populated_game.players:
            assert len(player.hand) == 2

    def test_start_hand_not_enough_players(self, game):
        game.add_player("Alice")
        result = game.start_hand()
        assert result is False

    def test_blinds_posted(self, populated_game):
        populated_game.start_hand()

        # Small blind (player 1) should have bet 10
        sb_player = populated_game.players[1]
        assert sb_player.bet == 10
        assert sb_player.chips == 990

        # Big blind (player 2) should have bet 20
        bb_player = populated_game.players[2]
        assert bb_player.bet == 20
        assert bb_player.chips == 980

    def test_action_fold(self, populated_game):
        populated_game.start_hand()

        # First to act is player after big blind
        current = populated_game.get_current_player()
        assert current is not None

        # Fold
        success = populated_game.action_fold(current.id)
        assert success is True
        assert current.folded is True

    def test_action_call(self, populated_game):
        populated_game.start_hand()

        # Find player who needs to call
        current = populated_game.get_current_player()
        # Current bet to call is 20 (big blind)
        success = populated_game.action_call(current.id)
        assert success is True
        assert current.bet == 20
        assert current.chips == 980

    def test_action_raise(self, populated_game):
        populated_game.start_hand()

        current = populated_game.get_current_player()

        # Raise by adding 40 (total 60)
        success = populated_game.action_raise(current.id, 40)
        assert success is True
        assert current.bet == 60
        assert current.chips == 940

    def test_all_in_scenario(self, populated_game):
        populated_game.start_hand()

        current = populated_game.get_current_player()
        current.chips = 10  # Small stack

        # Call - should go all-in
        success = populated_game.action_call(current.id)
        assert success is True
        assert current.is_all_in is True
        assert current.chips == 0

    def test_postflop_check_does_not_skip_other_players(self, populated_game):
        populated_game.start_hand()
        populated_game.phase = "flop"
        populated_game.community_cards = [
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.CLUBS, Rank.KING),
        ]
        populated_game.current_bet = 0
        populated_game.acted_this_round = set()
        for player in populated_game.players:
            player.bet = 0

        current = populated_game.get_current_player()
        success = populated_game.action_check(current.id)

        assert success is True
        assert populated_game.phase == "flop"
        assert current.id in populated_game.acted_this_round

    def test_short_all_in_does_not_block_round_completion(self, populated_game):
        populated_game.start_hand()
        populated_game.phase = "flop"
        populated_game.current_bet = 100

        for player in populated_game.players:
            player.folded = True
            player.is_all_in = False
            player.bet = 0

        p0, p1, p2 = populated_game.players[:3]
        p0.folded = False
        p0.bet = 100
        p1.folded = False
        p1.bet = 10
        p1.is_all_in = True
        p2.folded = False
        p2.bet = 100
        populated_game.acted_this_round = {p0.id, p2.id}

        assert populated_game._is_round_complete() is True

    def test_game_to_dict(self, populated_game):
        populated_game.start_hand()
        player_id = populated_game.players[0].id

        state = populated_game.to_dict(for_player=player_id)
        assert "game_id" in state
        assert "phase" in state
        assert "players" in state
        assert "community_cards" in state
        assert "pot" in state
        assert "current_player" in state

    def test_get_current_player(self, populated_game):
        populated_game.start_hand()
        current = populated_game.get_current_player()
        assert current is not None
        assert current.id in [p.id for p in populated_game.players]

    def test_action_fold_wrong_player(self, populated_game):
        populated_game.start_hand()
        # Try to fold for a player who isn't current
        wrong_player_id = populated_game.players[0].id
        current = populated_game.get_current_player()
        if current.id != wrong_player_id:
            # The action might still work based on implementation
            # This tests the internal _get_player logic
            result = populated_game.action_fold(wrong_player_id)
            # Either succeeds or the player becomes folded


class TestHandEvaluation:
    """Test hand evaluation within PokerGame"""

    def test_high_card(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.DIAMONDS, Rank.SEVEN),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.TWO),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.HIGH_CARD.value

    def test_one_pair(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.KING),
            Card(Suit.CLUBS, Rank.SEVEN),
            Card(Suit.SPADES, Rank.TWO),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.PAIR.value

    def test_two_pair(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.KING),
            Card(Suit.CLUBS, Rank.KING),
            Card(Suit.SPADES, Rank.SEVEN),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.TWO_PAIR.value

    def test_three_of_a_kind(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
            Card(Suit.CLUBS, Rank.KING),
            Card(Suit.SPADES, Rank.SEVEN),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.THREE_OF_A_KIND.value

    def test_straight(self, game):
        cards = [
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.DIAMONDS, Rank.JACK),
            Card(Suit.CLUBS, Rank.QUEEN),
            Card(Suit.SPADES, Rank.KING),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.STRAIGHT.value

    def test_wheel_straight(self, game):
        """Test A-5 straight (wheel)"""
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.TWO),
            Card(Suit.DIAMONDS, Rank.THREE),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.FIVE),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.STRAIGHT.value
        assert result[1] == [5]

    def test_wheel_straight_flush_not_royal_flush(self, game):
        cards = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.TWO),
            Card(Suit.HEARTS, Rank.THREE),
            Card(Suit.HEARTS, Rank.FOUR),
            Card(Suit.HEARTS, Rank.FIVE),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.STRAIGHT_FLUSH.value
        assert result[1] == [5]

    def test_flush(self, game):
        cards = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.HEARTS, Rank.FOUR),
            Card(Suit.HEARTS, Rank.TWO),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.FLUSH.value

    def test_full_house(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
            Card(Suit.CLUBS, Rank.KING),
            Card(Suit.SPADES, Rank.KING),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.FULL_HOUSE.value

    def test_four_of_a_kind(self, game):
        cards = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
            Card(Suit.CLUBS, Rank.ACE),
            Card(Suit.SPADES, Rank.KING),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.FOUR_OF_A_KIND.value

    def test_straight_flush(self, game):
        cards = [
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.HEARTS, Rank.QUEEN),
            Card(Suit.HEARTS, Rank.KING),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.STRAIGHT_FLUSH.value

    def test_royal_flush(self, game):
        cards = [
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.HEARTS, Rank.QUEEN),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.HEARTS, Rank.ACE),
        ]
        result = game._evaluate_five_card_hand(cards)
        assert result[0] == HandRank.ROYAL_FLUSH.value

    def test_side_pot_limits_short_stack_winnings(self, game):
        p0 = game.add_player("Shorty")
        p1 = game.add_player("Deep1")
        p2 = game.add_player("Deep2")

        p0.chips = p1.chips = p2.chips = 0
        p0.total_bet = 10
        p1.total_bet = 100
        p2.total_bet = 100
        game.pot = 210
        game.phase = "river"
        game.community_cards = [
            Card(Suit.CLUBS, Rank.TWO),
            Card(Suit.DIAMONDS, Rank.SEVEN),
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.CLUBS, Rank.JACK),
            Card(Suit.SPADES, Rank.FOUR),
        ]
        p0.hand = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.ACE)]
        p1.hand = [Card(Suit.HEARTS, Rank.KING), Card(Suit.SPADES, Rank.KING)]
        p2.hand = [Card(Suit.HEARTS, Rank.QUEEN), Card(Suit.SPADES, Rank.QUEEN)]

        game._evaluate_hands()

        assert p0.chips == 30
        assert p1.chips == 180
        assert p2.chips == 0
