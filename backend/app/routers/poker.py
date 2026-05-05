"""
Poker Game API Router - Simplified for debugging
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import asyncio
import time

from app.poker_game import PokerGame
from app.poker_ai import AIManager

router = APIRouter(prefix="/api/poker", tags=["poker"])

# In-memory game storage
games: Dict[str, PokerGame] = {}
ai_managers: Dict[str, AIManager] = {}
game_last_accessed: Dict[str, float] = {}

GAME_MAX_AGE_SECONDS = 3600

def cleanup_old_games():
    """Remove games that haven't been accessed in a while"""
    current_time = time.time()
    games_to_remove = []
    for game_id, last_access in list(game_last_accessed.items()):
        if current_time - last_access > GAME_MAX_AGE_SECONDS:
            games_to_remove.append(game_id)
    for game_id in games_to_remove:
        games.pop(game_id, None)
        ai_managers.pop(game_id, None)
        game_last_accessed.pop(game_id, None)
    return len(games_to_remove)

def update_game_access(game_id: str):
    """Update last access time for a game"""
    game_last_accessed[game_id] = time.time()

class CreateGameRequest(BaseModel):
    player_name: str = "Player"
    game_type: str = "single"
    max_players: int = 6

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str = "Player"

class ActionRequest(BaseModel):
    player_id: str
    action: str
    amount: Optional[int] = None

class BuyBackRequest(BaseModel):
    player_id: str
    amount: int = 1000

@router.post("/games")
async def create_game(request: CreateGameRequest):
    """Create a new poker game"""
    game_id = str(uuid.uuid4())[:8]
    game = PokerGame(game_id)
    game.game_type = request.game_type
    game.max_players = request.max_players

    # Add first player
    human = game.add_player(request.player_name, is_human=True)

    if request.game_type == "single":
        # Add AI bots
        ai_manager = AIManager(game)
        ai_manager.add_bot("Shelby", aggression=0.3)
        ai_manager.add_bot("Freya", aggression=0.5)
        ai_manager.add_bot("Charlie", aggression=0.7)
        ai_manager.add_bot("Diana", aggression=0.6)
        ai_manager.add_bot("Eve", aggression=0.4)

        game.start_hand()
        games[game_id] = game
        ai_managers[game_id] = ai_manager
        update_game_access(game_id)
        cleanup_old_games()

        # Process AI turns
        max_turns = 20
        turns = 0
        while turns < max_turns:
            active = [p for p in game.players if not p.folded and not p.is_all_in]
            if len(active) <= 1 or game.phase == 'showdown':
                break
            current = game.get_current_player()
            if not current or current.is_human:
                break
            ai_manager.process_bot_turn()
            turns += 1

        return {
            "game_id": game_id,
            "player_id": human.id,
            "state": game.to_dict(for_player=human.id),
            "game_type": "single"
        }
    else:
        # Multiplayer - waiting for players
        games[game_id] = game
        ai_managers[game_id] = None
        update_game_access(game_id)
        cleanup_old_games()

        return {
            "game_id": game_id,
            "player_id": human.id,
            "state": game.to_dict(for_player=human.id),
            "game_type": "multiplayer",
            "players": [p.to_dict() for p in game.players],
            "waiting": True
        }

@router.post("/games/join")
async def join_game(request: JoinGameRequest):
    """Join an existing multiplayer game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[request.game_id]

    if getattr(game, 'game_type', 'single') != "multiplayer":
        raise HTTPException(status_code=400, detail="Cannot join single player game")

    if len(game.players) >= getattr(game, 'max_players', 6):
        raise HTTPException(status_code=400, detail="Game is full")

    if game.phase != 'waiting':
        raise HTTPException(status_code=400, detail="Game already started")

    # Add new player
    player = game.add_player(request.player_name, is_human=True)
    update_game_access(request.game_id)

    return {
        "game_id": request.game_id,
        "player_id": player.id,
        "state": game.to_dict(for_player=player.id),
        "players": [p.to_dict() for p in game.players],
        "waiting": len(game.players) < 2
    }

@router.post("/games/{game_id}/start")
async def start_multiplayer_game(game_id: str, player_id: str):
    """Start a multiplayer game (host only)"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]

    if getattr(game, 'game_type', 'single') != "multiplayer":
        raise HTTPException(status_code=400, detail="Not a multiplayer game")

    if len(game.players) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players")

    if game.players[0].id != player_id:
        raise HTTPException(status_code=403, detail="Only host can start")

    game.waiting_for_players = False
    game.start_hand()
    update_game_access(game_id)

    return game.to_dict(for_player=player_id)

@router.get("/games/{game_id}")
async def get_game_state(game_id: str, player_id: str, process_ai: bool = True):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    update_game_access(game_id)
    game = games[game_id]

    # Process AI turns for single player
    is_single_player = getattr(game, 'game_type', 'single') == 'single'
    if process_ai and is_single_player and game.phase not in ('showdown', 'waiting'):
        active = [p for p in game.players if not p.folded and not p.is_all_in]
        if len(active) <= 1:
            game._advance_phase()
        else:
            current = game.get_current_player()
            if current and not current.is_human:
                ai_manager = ai_managers.get(game_id)
                if ai_manager:
                    ai_manager.process_bot_turn()
                    await asyncio.sleep(1.5)

    return game.to_dict(for_player=player_id)

@router.post("/games/{game_id}/action")
async def player_action(game_id: str, request: ActionRequest):
    """Execute player action"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    update_game_access(game_id)
    game = games[game_id]

    current = game.get_current_player()
    if not current or current.id != request.player_id:
        raise HTTPException(status_code=400, detail="Not your turn")

    success = False
    if request.action == "fold":
        success = game.action_fold(request.player_id)
    elif request.action == "check":
        success = game.action_check(request.player_id)
    elif request.action == "call":
        success = game.action_call(request.player_id)
    elif request.action == "raise":
        if request.amount is None:
            raise HTTPException(status_code=400, detail="Amount required")
        success = game.action_raise(request.player_id, request.amount)

    if not success:
        raise HTTPException(status_code=400, detail="Action failed")

    # Process AI turns for single player
    if getattr(game, 'game_type', 'single') == "single":
        ai_manager = ai_managers.get(game_id)
        if ai_manager:
            max_turns = 20
            turns = 0
            while turns < max_turns:
                current = game.get_current_player()
                if not current or current.is_human or game.phase == 'showdown':
                    break
                await asyncio.sleep(0.5)
                ai_manager.process_bot_turn()
                turns += 1

    return game.to_dict(for_player=request.player_id)

@router.post("/games/{game_id}/buy-back")
async def buy_back(game_id: str, request: BuyBackRequest):
    """Add chips for a busted player before the next hand."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Buy-back amount must be positive")

    game = games[game_id]
    player = game._get_player(request.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if game.phase not in ('showdown', 'waiting'):
        raise HTTPException(status_code=400, detail="Buy-back is only available between hands")

    player.chips += request.amount
    if player.chips > 0:
        player.is_all_in = False

    update_game_access(game_id)
    return game.to_dict(for_player=request.player_id)

@router.post("/games/{game_id}/next-hand")
async def next_hand(game_id: str, player_id: str):
    """Start next hand"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]

    if game.phase not in ('showdown', 'waiting'):
        raise HTTPException(status_code=400, detail="Hand still in progress")

    game.dealer_index = (game.dealer_index + 1) % len(game.players)
    game.start_hand()

    # Process AI turns for single player
    if getattr(game, 'game_type', 'single') == "single":
        ai_manager = ai_managers.get(game_id)
        if ai_manager:
            current = game.get_current_player()
            turns = 0
            while current and not current.is_human and turns < 10:
                await asyncio.sleep(0.3)
                ai_manager.process_bot_turn()
                current = game.get_current_player()
                turns += 1

    return game.to_dict(for_player=player_id)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    cleaned = cleanup_old_games()
    return {"status": "ok", "active_games": len(games), "cleaned_games": cleaned}
