"""
Game State Persistence Module

Provides file-based persistence for poker games to survive backend restarts.
Games are saved periodically and on graceful shutdown, then restored on startup.
"""
import json
import os
import asyncio
import time
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path

from .config import Config, get_logger
from .game import PokerGame, Player, Card, Suit, Rank

logger = get_logger()

# Persistence configuration
PERSISTENCE_DIR = os.getenv("PERSISTENCE_DIR", "/tmp/poker_persistence")
SAVE_INTERVAL_SECONDS = int(os.getenv("SAVE_INTERVAL_SECONDS", "300"))  # 5 minutes
MAX_PERSISTENCE_AGE_HOURS = int(os.getenv("MAX_PERSISTENCE_AGE_HOURS", "24"))


class GameStateEncoder(json.JSONEncoder):
    """Custom JSON encoder for game state objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Card):
            return {
                "suit": obj.suit.name,
                "rank": obj.rank.value
            }
        if isinstance(obj, Suit):
            return obj.name
        if isinstance(obj, Rank):
            return obj.value
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


def card_from_dict(data: dict) -> Card:
    """Reconstruct a Card from serialized data"""
    suit = Suit[data["suit"]]
    rank = Rank(data["rank"])
    return Card(suit, rank)


def player_to_dict(player: Player) -> dict:
    """Serialize a Player to dictionary"""
    return {
        "id": player.id,
        "name": player.name,
        "chips": player.chips,
        "hand": [c.to_dict() for c in player.hand],
        "bet": player.bet,
        "folded": player.folded,
        "is_all_in": player.is_all_in,
        "is_human": player.is_human
    }


def player_from_dict(data: dict) -> Player:
    """Reconstruct a Player from serialized data"""
    player = Player(
        id=data["id"],
        name=data["name"],
        chips=data["chips"],
        is_human=data.get("is_human", False)
    )
    player.hand = [card_from_dict(c) for c in data.get("hand", [])]
    player.bet = data.get("bet", 0)
    player.folded = data.get("folded", False)
    player.is_all_in = data.get("is_all_in", False)
    return player


def game_to_dict(game: PokerGame) -> dict:
    """Serialize a PokerGame to dictionary"""
    return {
        "game_id": game.game_id,
        "phase": game.phase,
        "hand_number": game.hand_number,
        "community_cards": [c.to_dict() for c in game.community_cards],
        "pot": game.pot,
        "current_bet": game.current_bet,
        "min_raise": game.min_raise,
        "dealer_index": game.dealer_index,
        "current_player_index": game.current_player_index,
        "players": [player_to_dict(p) for p in game.players],
        "deck": {
            "cards": [c.to_dict() for c in game.deck.cards]
        },
        "side_pots": getattr(game, "side_pots", []),
        "last_action": game.last_action,
        "hand_history": game.hand_history,
        "chat_messages": game.chat_messages,
        "created_at": getattr(game, "created_at", datetime.now()).isoformat(),
        "saved_at": datetime.now().isoformat()
    }


def game_from_dict(data: dict) -> PokerGame:
    """Reconstruct a PokerGame from serialized data"""
    from .game import PokerGame  # Avoid circular import
    
    game = PokerGame(data["game_id"])
    game.phase = data["phase"]
    game.hand_number = data["hand_number"]
    game.community_cards = [card_from_dict(c) for c in data.get("community_cards", [])]
    game.pot = data["pot"]
    game.current_bet = data["current_bet"]
    game.min_raise = data.get("min_raise", Config.BIG_BLIND)
    game.dealer_index = data["dealer_index"]
    game.current_player_index = data.get("current_player_index", 0)
    game.players = [player_from_dict(p) for p in data.get("players", [])]
    game.deck.cards = [card_from_dict(c) for c in data.get("deck", {}).get("cards", [])]
    game.side_pots = data.get("side_pots", [])
    game.last_action = data.get("last_action")
    game.hand_history = data.get("hand_history", [])
    game.chat_messages = data.get("chat_messages", [])
    game.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
    
    return game


class GamePersistence:
    """Manages persistence of game state to disk"""
    
    def __init__(self, persistence_dir: Optional[str] = None):
        self.persistence_dir = Path(persistence_dir or PERSISTENCE_DIR)
        self.games_file = self.persistence_dir / "games.json"
        self.metadata_file = self.persistence_dir / "metadata.json"
        self._shutdown_event = asyncio.Event()
        self._save_task: Optional[asyncio.Task] = None
        self._enabled = os.getenv("ENABLE_PERSISTENCE", "true").lower() == "true"
        
        # Ensure persistence directory exists
        if self._enabled:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Game persistence enabled. Data directory: {self.persistence_dir}")
    
    def is_enabled(self) -> bool:
        """Check if persistence is enabled"""
        return self._enabled
    
    def save_games(self, games: Dict[str, PokerGame]) -> bool:
        """
        Save all games to disk.
        
        Args:
            games: Dictionary of game_id -> PokerGame
            
        Returns:
            True if save was successful
        """
        if not self._enabled:
            return False
        
        try:
            # Serialize all games
            games_data = {
                game_id: game_to_dict(game)
                for game_id, game in games.items()
            }
            
            # Write to temp file first, then atomic move
            temp_file = self.games_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(games_data, f, cls=GameStateEncoder, indent=2)
            
            # Atomic rename
            temp_file.replace(self.games_file)
            
            # Save metadata
            metadata = {
                "last_save": datetime.now().isoformat(),
                "game_count": len(games),
                "version": "1.0.0"
            }
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved {len(games)} games to {self.games_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save games: {e}")
            return False
    
    def load_games(self) -> Dict[str, PokerGame]:
        """
        Load games from disk.
        
        Returns:
            Dictionary of game_id -> PokerGame
        """
        if not self._enabled:
            return {}
        
        if not self.games_file.exists():
            logger.info("No persisted games found")
            return {}
        
        try:
            # Check file age
            file_age_hours = (time.time() - self.games_file.stat().st_mtime) / 3600
            if file_age_hours > MAX_PERSISTENCE_AGE_HOURS:
                logger.warning(f"Persisted games are {file_age_hours:.1f} hours old, ignoring")
                return {}
            
            with open(self.games_file, "r") as f:
                games_data = json.load(f)
            
            games = {}
            for game_id, game_dict in games_data.items():
                try:
                    game = game_from_dict(game_dict)
                    games[game_id] = game
                except Exception as e:
                    logger.error(f"Failed to load game {game_id}: {e}")
            
            logger.info(f"Loaded {len(games)} games from persistence (file age: {file_age_hours:.1f}h)")
            return games
            
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted persistence file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load games: {e}")
            return {}
    
    async def start_periodic_save(self, games_provider):
        """
        Start background task for periodic saves.
        
        Args:
            games_provider: Callable that returns the games dictionary
        """
        if not self._enabled:
            return
        
        async def save_loop():
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=SAVE_INTERVAL_SECONDS
                    )
                except asyncio.TimeoutError:
                    # Time to save
                    games = games_provider()
                    self.save_games(games)
        
        self._save_task = asyncio.create_task(save_loop())
        logger.info(f"Started periodic save task (interval: {SAVE_INTERVAL_SECONDS}s)")
    
    async def stop(self, games: Dict[str, PokerGame]):
        """Stop periodic saves and perform final save"""
        if not self._enabled:
            return
        
        logger.info("Stopping persistence and saving games...")
        self._shutdown_event.set()
        
        if self._save_task:
            try:
                await asyncio.wait_for(self._save_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Save task did not stop in time")
        
        # Final save
        self.save_games(games)
    
    def get_persistence_status(self) -> dict:
        """Get current persistence status"""
        if not self._enabled:
            return {"enabled": False}
        
        status = {
            "enabled": True,
            "persistence_dir": str(self.persistence_dir),
            "save_interval_seconds": SAVE_INTERVAL_SECONDS,
            "max_age_hours": MAX_PERSISTENCE_AGE_HOURS
        }
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
                status["last_save"] = metadata.get("last_save")
                status["saved_game_count"] = metadata.get("game_count", 0)
            except Exception:
                pass
        
        if self.games_file.exists():
            status["file_size_bytes"] = self.games_file.stat().st_size
            status["file_age_hours"] = round(
                (time.time() - self.games_file.stat().st_mtime) / 3600, 2
            )
        
        return status


# Global persistence instance
persistence = GamePersistence()
