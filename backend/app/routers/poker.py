"""
Poker Game API Router
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
game_last_accessed: Dict[str, float] = {}  # Track last access time for cleanup

# Cleanup games older than 1 hour
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

class ActionRequest(BaseModel):
    player_id: str
    action: str  # fold, check, call, raise
    amount: Optional[int] = None

@router.post("/games")
async def create_game(request: CreateGameRequest):
    """Create a new poker game with AI opponents"""
    import logging
    logger = logging.getLogger(__name__)
    
    game_id = str(uuid.uuid4())[:8]
    logger.info(f"Creating new poker game: {game_id}")
    
    game = PokerGame(game_id)
    
    # Add human player
    human = game.add_player(request.player_name, is_human=True)
    logger.info(f"Added human player: {human.name} ({human.id})")
    
    # Add AI bots with varying aggression
    ai_manager = AIManager(game)
    ai_manager.add_bot("Alex", aggression=0.3)  # Tight
    ai_manager.add_bot("Bob", aggression=0.5)  # Balanced
    ai_manager.add_bot("Charlie", aggression=0.7)  # Loose
    ai_manager.add_bot("Diana", aggression=0.6)  # Aggressive
    ai_manager.add_bot("Eve", aggression=0.4)  # Balanced
    logger.info(f"Added {len(ai_manager.bots)} AI bots")
    
    # Start first hand
    success = game.start_hand()
    logger.info(f"Hand started: {success}, Phase: {game.phase}, Current player: {game.get_current_player().name if game.get_current_player() else 'None'}")
    
    # Store game
    games[game_id] = game
    ai_managers[game_id] = ai_manager
    update_game_access(game_id)
    
    # Cleanup old games periodically
    cleanup_old_games()
    
    # Process AI turns until it's human's turn
    max_turns = 20
    turns = 0
    while turns < max_turns:
        current = game.get_current_player()
        if not current or current.is_human:
            break
        ai_manager.process_bot_turn()
        turns += 1
    
    logger.info(f"Processed {turns} AI turns, current player: {game.get_current_player().name if game.get_current_player() else 'None'}")
    
    return {
        "game_id": game_id,
        "player_id": human.id,
        "state": game.to_dict(for_player=human.id)
    }

@router.get("/games/{game_id}")
async def get_game_state(game_id: str, player_id: str, process_ai: bool = True):
    """Get current game state, optionally processing AI turns"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    update_game_access(game_id)
    game = games[game_id]
    
    # Process AI turns if requested and it's not human's turn
    if process_ai and game.phase != 'showdown':
        current = game.get_current_player()
        if current and not current.is_human:
            ai_manager = ai_managers[game_id]
            max_turns = 5  # Process a few turns per request
            for _ in range(max_turns):
                current = game.get_current_player()
                if not current or current.is_human or game.phase == 'showdown':
                    break
                ai_manager.process_bot_turn()
                await asyncio.sleep(0.1)
    
    return game.to_dict(for_player=player_id)

@router.post("/games/{game_id}/action")
async def player_action(game_id: str, request: ActionRequest):
    """Execute player action"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    update_game_access(game_id)
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
    
    # Process AI turns until it's human's turn or hand is over
    ai_manager = ai_managers[game_id]
    max_turns = 20
    turns = 0
    
    while turns < max_turns:
        current = game.get_current_player()
        if not current or current.is_human or game.phase == 'showdown':
            break
        
        await asyncio.sleep(0.2)  # Small delay between AI actions
        result = ai_manager.process_bot_turn()
        turns += 1
        
        if not result:
            break
    
    return game.to_dict(for_player=request.player_id)

class NextHandRequest(BaseModel):
    player_id: str

@router.post("/games/{game_id}/next-hand")
async def next_hand(game_id: str, player_id: str):
    """Start next hand"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Next hand requested for game {game_id}, player {player_id}")
    
    if game_id not in games:
        logger.error(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")
    
    update_game_access(game_id)
    game = games[game_id]
    logger.info(f"Game phase: {game.phase}")
    
    # Only proceed if hand is complete
    if game.phase not in ['showdown', 'waiting']:
        logger.warning(f"Hand still in progress, phase: {game.phase}")
        raise HTTPException(status_code=400, detail="Hand still in progress")
    
    # Move dealer button
    game.dealer_index = (game.dealer_index + 1) % len(game.players)
    
    # Start new hand
    success = game.start_hand()
    logger.info(f"Hand started: {success}, new phase: {game.phase}")
    
    # Process AI blinds and early action
    ai_manager = ai_managers[game_id]
    current = game.get_current_player()
    turns = 0
    while current and not current.is_human and turns < 10:
        await asyncio.sleep(0.3)
        ai_manager.process_bot_turn()
        current = game.get_current_player()
        turns += 1
    
    logger.info(f"Processed {turns} AI turns, current player: {current.id if current else 'None'}")
    
    return game.to_dict(for_player=player_id)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    # Cleanup old games and return count
    cleaned = cleanup_old_games()
    return {"status": "ok", "active_games": len(games), "cleaned_games": cleaned}
