"""
Poker Game API Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import asyncio

from app.poker_game import PokerGame
from app.poker_ai import AIManager

router = APIRouter(prefix="/api/poker", tags=["poker"])

# In-memory game storage
games: Dict[str, PokerGame] = {}
ai_managers: Dict[str, AIManager] = {}

class CreateGameRequest(BaseModel):
    player_name: str = "Player"

class ActionRequest(BaseModel):
    player_id: str
    action: str  # fold, check, call, raise
    amount: Optional[int] = None

@router.post("/games")
async def create_game(request: CreateGameRequest):
    """Create a new poker game with AI opponents"""
    game_id = str(uuid.uuid4())[:8]
    game = PokerGame(game_id)
    
    # Add human player
    human = game.add_player(request.player_name, is_human=True)
    
    # Add AI bots with varying aggression
    ai_manager = AIManager(game)
    ai_manager.add_bot("Alex", aggression=0.3)  # Tight
    ai_manager.add_bot("Bob", aggression=0.5)  # Balanced
    ai_manager.add_bot("Charlie", aggression=0.7)  # Loose
    ai_manager.add_bot("Diana", aggression=0.6)  # Aggressive
    ai_manager.add_bot("Eve", aggression=0.4)  # Balanced
    
    # Start first hand
    game.start_hand()
    
    # Store game
    games[game_id] = game
    ai_managers[game_id] = ai_manager
    
    return {
        "game_id": game_id,
        "player_id": human.id,
        "state": game.to_dict(for_player=human.id)
    }

@router.get("/games/{game_id}")
async def get_game_state(game_id: str, player_id: str):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    return game.to_dict(for_player=player_id)

@router.post("/games/{game_id}/action")
async def player_action(game_id: str, request: ActionRequest):
    """Execute player action"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Verify it's player's turn
    current = game.get_current_player()
    if not current or current.id != request.player_id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Execute action
    success = False
    if request.action == "fold":
        success = game.action_fold(request.player_id)
    elif request.action == "check":
        success = game.action_check(request.player_id)
    elif request.action == "call":
        success = game.action_call(request.player_id)
    elif request.action == "raise":
        if request.amount is None:
            raise HTTPException(status_code=400, detail="Amount required for raise")
        success = game.action_raise(request.player_id, request.amount)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if not success:
        raise HTTPException(status_code=400, detail="Action failed")
    
    # Process AI turns
    ai_manager = ai_managers[game_id]
    while True:
        current = game.get_current_player()
        if not current or current.is_human:
            break
        
        # Small delay for realism
        await asyncio.sleep(0.5)
        ai_manager.process_bot_turn()
    
    return game.to_dict(for_player=request.player_id)

@router.post("/games/{game_id}/next-hand")
async def next_hand(game_id: str, player_id: str):
    """Start next hand"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Only proceed if hand is complete
    if game.phase not in ['showdown', 'waiting']:
        raise HTTPException(status_code=400, detail="Hand still in progress")
    
    # Move dealer button
    game.dealer_index = (game.dealer_index + 1) % len(game.players)
    
    # Start new hand
    game.start_hand()
    
    # Process AI blinds and early action
    ai_manager = ai_managers[game_id]
    current = game.get_current_player()
    while current and not current.is_human:
        await asyncio.sleep(0.3)
        ai_manager.process_bot_turn()
        current = game.get_current_player()
    
    return game.to_dict(for_player=player_id)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "active_games": len(games)}
