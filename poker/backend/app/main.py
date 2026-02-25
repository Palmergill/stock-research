"""
Poker Game API - FastAPI Backend
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import asyncio

from .game import PokerGame
from .ai import AIManager
from .config import Config, get_logger, set_correlation_id, clear_correlation_id

# Setup logging
logger = get_logger()

app = FastAPI(title="Texas Hold'em Poker API", debug=Config.DEBUG)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to each request for tracing"""
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
    set_correlation_id(cid)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    
    clear_correlation_id()
    return response


# In-memory game storage
games: Dict[str, PokerGame] = {}
ai_managers: Dict[str, AIManager] = {}


class CreateGameRequest(BaseModel):
    player_name: str = "Player"


class ActionRequest(BaseModel):
    player_id: str
    action: str  # fold, check, call, raise
    amount: Optional[int] = None


class GameResponse(BaseModel):
    game_id: str
    player_id: str
    state: dict


@app.post("/api/poker/games", response_model=GameResponse)
async def create_game(request: CreateGameRequest):
    """Create a new poker game with AI opponents"""
    game_id = str(uuid.uuid4())[:8]
    logger.info(f"Creating new game: {game_id}, player: {request.player_name}")
    
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
    
    logger.info(f"Game {game_id} created successfully with {len(game.players)} players")
    
    return {
        "game_id": game_id,
        "player_id": human.id,
        "state": game.to_dict(for_player=human.id)
    }


@app.get("/api/poker/games/{game_id}")
async def get_game_state(game_id: str, player_id: str):
    """Get current game state"""
    if game_id not in games:
        logger.warning(f"Game not found: {game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    return game.to_dict(for_player=player_id)


@app.post("/api/poker/games/{game_id}/action")
async def player_action(game_id: str, request: ActionRequest):
    """Execute player action"""
    if game_id not in games:
        logger.warning(f"Action on non-existent game: {game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Verify it's player's turn
    current = game.get_current_player()
    if not current or current.id != request.player_id:
        logger.warning(f"Action attempted out of turn: game={game_id}, player={request.player_id}")
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Execute action
    logger.info(f"Player action: game={game_id}, player={request.player_id}, action={request.action}")
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
        logger.warning(f"Action failed: game={game_id}, action={request.action}")
        raise HTTPException(status_code=400, detail="Action failed")
    
    # Process AI turns with turn limit protection
    ai_manager = ai_managers[game_id]
    ai_turns = 0
    
    while ai_turns < Config.MAX_AI_TURNS:
        current = game.get_current_player()
        if not current or current.is_human:
            break
        
        # Small delay for realism
        await asyncio.sleep(Config.AI_DECISION_DELAY)
        ai_manager.process_bot_turn()
        ai_turns += 1
    
    if ai_turns >= Config.MAX_AI_TURNS:
        logger.error(f"AI turn limit reached in game {game_id} - possible infinite loop")
    
    return game.to_dict(for_player=request.player_id)


@app.post("/api/poker/games/{game_id}/next-hand")
async def next_hand(game_id: str, player_id: str):
    """Start next hand"""
    if game_id not in games:
        logger.warning(f"Next hand on non-existent game: {game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Only proceed if hand is complete
    if game.phase not in ['showdown', 'waiting']:
        raise HTTPException(status_code=400, detail="Hand still in progress")
    
    logger.info(f"Starting next hand: game={game_id}, hand_number={game.hand_number + 1}")
    
    # Move dealer button
    game.dealer_index = (game.dealer_index + 1) % len(game.players)
    
    # Start new hand
    game.start_hand()
    
    # Process AI blinds and early action
    ai_manager = ai_managers[game_id]
    current = game.get_current_player()
    ai_turns = 0
    
    while current and not current.is_human and ai_turns < Config.MAX_AI_TURNS:
        await asyncio.sleep(Config.AI_BLIND_DELAY)
        ai_manager.process_bot_turn()
        current = game.get_current_player()
        ai_turns += 1
    
    if ai_turns >= Config.MAX_AI_TURNS:
        logger.error(f"AI turn limit reached during blinds in game {game_id}")
    
    return game.to_dict(for_player=player_id)


@app.get("/api/poker/games/{game_id}/history")
async def get_game_history(game_id: str):
    """Get game history (placeholder for future)"""
    return {"game_id": game_id, "hands": []}


@app.get("/api/poker/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "active_games": len(games),
        "config": {
            "starting_chips": Config.STARTING_CHIPS,
            "small_blind": Config.SMALL_BLIND,
            "big_blind": Config.BIG_BLIND,
        }
    }


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("Poker API starting up")
    logger.info(f"Configuration: chips={Config.STARTING_CHIPS}, blinds={Config.SMALL_BLIND}/{Config.BIG_BLIND}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Poker API shutting down")
    logger.info(f"Active games at shutdown: {len(games)}")