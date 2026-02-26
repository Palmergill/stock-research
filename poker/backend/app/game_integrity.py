"""
Game Integrity Module - Anti-cheating and exploit prevention

This module provides security measures to prevent common exploits:
- Replay attack prevention via action tokens
- Player session validation
- State integrity checks
- Rate limiting per player
"""
import hashlib
import secrets
import time
from typing import Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from .config import Config, get_logger

logger = get_logger()


@dataclass
class PlayerSession:
    """Tracks a player's session for security validation"""
    player_id: str
    game_id: str
    created_at: float
    last_action_at: float
    action_sequence: int = 0
    tokens_used: Set[str] = field(default_factory=set)
    action_count: int = 0
    
    def is_expired(self, max_age_minutes: int = 120) -> bool:
        """Check if session has expired (default 2 hours)"""
        return time.time() - self.created_at > (max_age_minutes * 60)
    
    def generate_action_token(self) -> str:
        """Generate a unique token for the next action"""
        self.action_sequence += 1
        token_data = f"{self.player_id}:{self.game_id}:{self.action_sequence}:{time.time()}"
        return hashlib.sha256(token_data.encode()).hexdigest()[:16]
    
    def record_action(self):
        """Record that an action was taken"""
        self.last_action_at = time.time()
        self.action_count += 1


class GameIntegrityManager:
    """
    Manages game integrity and anti-cheating measures.
    
    Features:
    - Action tokens to prevent replay attacks
    - Player session tracking
    - Per-player rate limiting
    - State validation fingerprints
    """
    
    def __init__(self):
        # Player sessions: (game_id, player_id) -> PlayerSession
        self._sessions: Dict[Tuple[str, str], PlayerSession] = {}
        
        # Used action tokens (prevents replay attacks)
        self._used_tokens: Set[str] = set()
        
        # Per-player rate limiting: (game_id, player_id) -> list of timestamps
        self._player_action_times: Dict[Tuple[str, str], list] = defaultdict(list)
        
        # State fingerprints: game_id -> hash of last known state
        self._state_fingerprints: Dict[str, str] = {}
        
        # Suspicious activity tracking
        self._suspicious_activity: Dict[str, list] = defaultdict(list)
        
        # Configuration
        self.max_actions_per_minute = 30
        self.token_cleanup_interval = 3600  # 1 hour
        self.session_cleanup_interval = 7200  # 2 hours
        self._last_cleanup = time.time()
    
    def create_session(self, game_id: str, player_id: str) -> PlayerSession:
        """Create a new player session"""
        session = PlayerSession(
            player_id=player_id,
            game_id=game_id,
            created_at=time.time(),
            last_action_at=time.time()
        )
        self._sessions[(game_id, player_id)] = session
        logger.info(f"Created integrity session for player {player_id} in game {game_id}")
        return session
    
    def get_session(self, game_id: str, player_id: str) -> Optional[PlayerSession]:
        """Get an existing player session"""
        return self._sessions.get((game_id, player_id))
    
    def validate_action_request(
        self, 
        game_id: str, 
        player_id: str, 
        action: str,
        token: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate an action request for integrity.
        
        Returns:
            (is_valid, error_message)
        """
        # Cleanup old data periodically
        self._maybe_cleanup()
        
        # Check if session exists
        session = self._sessions.get((game_id, player_id))
        if not session:
            return False, "Invalid or expired session"
        
        # Check session expiry
        if session.is_expired():
            del self._sessions[(game_id, player_id)]
            return False, "Session expired, please refresh"
        
        # Check rate limiting
        if not self._check_rate_limit(game_id, player_id):
            self._log_suspicious_activity(game_id, player_id, "rate_limit_exceeded")
            return False, "Too many actions, please slow down"
        
        # Validate action token if provided (prevents replay attacks)
        if token and not self._validate_token(token):
            self._log_suspicious_activity(game_id, player_id, "invalid_token")
            return False, "Invalid action token"
        
        return True, ""
    
    def _check_rate_limit(self, game_id: str, player_id: str) -> bool:
        """Check if player is within rate limits"""
        key = (game_id, player_id)
        now = time.time()
        
        # Get recent actions (last 60 seconds)
        cutoff = now - 60
        recent_actions = [t for t in self._player_action_times[key] if t > cutoff]
        self._player_action_times[key] = recent_actions
        
        if len(recent_actions) >= self.max_actions_per_minute:
            return False
        
        recent_actions.append(now)
        return True
    
    def _validate_token(self, token: str) -> bool:
        """Validate and consume an action token"""
        if token in self._used_tokens:
            return False
        
        self._used_tokens.add(token)
        return True
    
    def generate_action_token(self, game_id: str, player_id: str) -> Optional[str]:
        """Generate a new action token for a player"""
        session = self._sessions.get((game_id, player_id))
        if not session:
            return None
        
        return session.generate_action_token()
    
    def record_action(self, game_id: str, player_id: str, action: str, token: Optional[str] = None):
        """Record that an action was taken"""
        session = self._sessions.get((game_id, player_id))
        if session:
            session.record_action()
        
        # Mark token as used if provided
        if token:
            self._used_tokens.add(token)
    
    def compute_state_fingerprint(self, game_state: dict) -> str:
        """Compute a fingerprint of the game state for integrity checking"""
        # Create a deterministic string representation
        state_str = (
            f"{game_state.get('game_id')}:{game_state.get('phase')}:"
            f"{game_state.get('hand_number')}:{game_state.get('pot')}:"
            f"{game_state.get('current_bet')}:{game_state.get('current_player')}"
        )
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]
    
    def store_state_fingerprint(self, game_id: str, game_state: dict):
        """Store the fingerprint of a game state"""
        self._state_fingerprints[game_id] = self.compute_state_fingerprint(game_state)
    
    def validate_state_integrity(self, game_id: str, game_state: dict) -> bool:
        """Check if current state matches expected fingerprint"""
        stored = self._state_fingerprints.get(game_id)
        if not stored:
            return True  # No stored fingerprint to compare against
        
        current = self.compute_state_fingerprint(game_state)
        return stored == current
    
    def _log_suspicious_activity(self, game_id: str, player_id: str, reason: str):
        """Log potentially suspicious activity"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "game_id": game_id,
            "player_id": player_id,
            "reason": reason
        }
        self._suspicious_activity[game_id].append(entry)
        logger.warning(f"Suspicious activity detected: {reason} by player {player_id} in game {game_id}")
    
    def get_suspicious_activity(self, game_id: str) -> list:
        """Get list of suspicious activities for a game"""
        return self._suspicious_activity.get(game_id, [])
    
    def _maybe_cleanup(self):
        """Periodically clean up old data"""
        now = time.time()
        
        # Cleanup used tokens every hour
        if now - self._last_cleanup > self.token_cleanup_interval:
            # Keep only tokens from last hour
            # (In practice, we'd need timestamps; for now just clear if too many)
            if len(self._used_tokens) > 10000:
                logger.info("Cleaning up old action tokens")
                self._used_tokens.clear()
        
        # Cleanup old sessions every 2 hours
        if now - self._last_cleanup > self.session_cleanup_interval:
            expired = [
                key for key, session in self._sessions.items()
                if session.is_expired()
            ]
            for key in expired:
                del self._sessions[key]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        self._last_cleanup = now
    
    def end_session(self, game_id: str, player_id: str):
        """End a player session (e.g., when they leave)"""
        key = (game_id, player_id)
        if key in self._sessions:
            del self._sessions[key]
            logger.info(f"Ended integrity session for player {player_id}")
    
    def get_session_stats(self, game_id: str) -> dict:
        """Get statistics for a game's sessions"""
        sessions = [
            s for (gid, _), s in self._sessions.items()
            if gid == game_id
        ]
        
        return {
            "active_sessions": len(sessions),
            "total_actions": sum(s.action_count for s in sessions),
            "suspicious_events": len(self._suspicious_activity.get(game_id, []))
        }


# Global integrity manager instance
integrity_manager = GameIntegrityManager()
