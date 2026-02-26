"""
Tournament Mode - Sit & Go Tournaments with Increasing Blinds
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


class TournamentStatus(Enum):
    WAITING = "waiting"      # Waiting for players to register
    ACTIVE = "active"        # Tournament in progress
    COMPLETED = "completed"  # Tournament finished


@dataclass
class BlindLevel:
    """Represents a blind level in tournament"""
    level: int
    small_blind: int
    big_blind: int
    ante: int = 0
    duration_minutes: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'ante': self.ante,
            'duration_minutes': self.duration_minutes
        }


# Standard blind structure for Sit & Go tournaments
DEFAULT_BLIND_STRUCTURE = [
    BlindLevel(1, 10, 20, 0, 10),
    BlindLevel(2, 15, 30, 0, 10),
    BlindLevel(3, 25, 50, 0, 10),
    BlindLevel(4, 40, 80, 0, 10),
    BlindLevel(5, 60, 120, 0, 10),
    BlindLevel(6, 100, 200, 0, 10),
    BlindLevel(7, 150, 300, 0, 10),
    BlindLevel(8, 200, 400, 0, 10),
    BlindLevel(9, 300, 600, 0, 10),
    BlindLevel(10, 500, 1000, 0, 10),
    BlindLevel(11, 800, 1600, 0, 10),
    BlindLevel(12, 1000, 2000, 0, 10),
    BlindLevel(13, 1500, 3000, 0, 10),
    BlindLevel(14, 2000, 4000, 0, 10),
    BlindLevel(15, 3000, 6000, 0, 10),
]


@dataclass
class TournamentPlayer:
    """Player in tournament context"""
    player_id: str
    name: str
    is_human: bool = False
    eliminated: bool = False
    eliminated_at: Optional[datetime] = None
    final_position: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'player_id': self.player_id,
            'name': self.name,
            'is_human': self.is_human,
            'eliminated': self.eliminated,
            'eliminated_at': self.eliminated_at.isoformat() if self.eliminated_at else None,
            'final_position': self.final_position
        }


@dataclass
class TournamentPrize:
    """Prize distribution for a position"""
    position: int
    percentage: float  # Percentage of total prize pool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': self.position,
            'percentage': self.percentage
        }


# Standard prize structure for 6-player SNG
SIX_PLAYER_PRIZE_STRUCTURE = [
    TournamentPrize(1, 50.0),   # 1st place: 50%
    TournamentPrize(2, 30.0),   # 2nd place: 30%
    TournamentPrize(3, 20.0),   # 3rd place: 20%
]


class Tournament:
    """Sit & Go Tournament"""
    
    def __init__(
        self,
        tournament_id: str,
        max_players: int = 6,
        buy_in: int = 1000,
        blind_structure: Optional[List[BlindLevel]] = None,
        prize_structure: Optional[List[TournamentPrize]] = None
    ):
        self.tournament_id = tournament_id
        self.max_players = max_players
        self.buy_in = buy_in
        self.status = TournamentStatus.WAITING
        
        self.blind_structure = blind_structure or DEFAULT_BLIND_STRUCTURE
        self.prize_structure = prize_structure or SIX_PLAYER_PRIZE_STRUCTURE
        
        self.players: List[TournamentPlayer] = []
        self.registered_players: List[str] = []  # Player IDs registered
        
        self.current_level_index = 0
        self.level_start_time: Optional[datetime] = None
        self.tournament_start_time: Optional[datetime] = None
        self.tournament_end_time: Optional[datetime] = None
        
        self.total_prize_pool = 0
        self.house_fee_percentage = 0.0  # 0% for play money
        
        self.elimination_count = 0
        self.game_id: Optional[str] = None  # Associated poker game
        
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @property
    def current_blind_level(self) -> BlindLevel:
        """Get current blind level"""
        if self.current_level_index < len(self.blind_structure):
            return self.blind_structure[self.current_level_index]
        # If exceeded defined levels, keep doubling
        last_level = self.blind_structure[-1]
        return BlindLevel(
            self.current_level_index + 1,
            last_level.small_blind * 2,
            last_level.big_blind * 2,
            last_level.ante,
            last_level.duration_minutes
        )
    
    @property
    def time_in_current_level(self) -> Optional[int]:
        """Get seconds elapsed in current level"""
        if not self.level_start_time:
            return None
        elapsed = datetime.now() - self.level_start_time
        return int(elapsed.total_seconds())
    
    @property
    def time_remaining_in_level(self) -> Optional[int]:
        """Get seconds remaining in current level"""
        if not self.level_start_time:
            return None
        current = self.current_blind_level
        elapsed = datetime.now() - self.level_start_time
        remaining = timedelta(minutes=current.duration_minutes) - elapsed
        return max(0, int(remaining.total_seconds()))
    
    @property
    def active_players(self) -> List[TournamentPlayer]:
        """Get non-eliminated players"""
        return [p for p in self.players if not p.eliminated]
    
    @property
    def eliminated_players(self) -> List[TournamentPlayer]:
        """Get eliminated players sorted by elimination time (most recent first)"""
        eliminated = [p for p in self.players if p.eliminated and p.eliminated_at]
        eliminated.sort(key=lambda p: p.eliminated_at, reverse=True)
        return eliminated
    
    def register_player(self, player_id: str, name: str, is_human: bool = False) -> bool:
        """Register a player for the tournament"""
        if self.status != TournamentStatus.WAITING:
            return False
        if len(self.players) >= self.max_players:
            return False
        if player_id in self.registered_players:
            return False
        
        player = TournamentPlayer(
            player_id=player_id,
            name=name,
            is_human=is_human
        )
        self.players.append(player)
        self.registered_players.append(player_id)
        self.updated_at = datetime.now()
        return True
    
    def start_tournament(self, game_id: str) -> bool:
        """Start the tournament"""
        if self.status != TournamentStatus.WAITING:
            return False
        if len(self.players) < 2:
            return False
        
        self.status = TournamentStatus.ACTIVE
        self.tournament_start_time = datetime.now()
        self.level_start_time = datetime.now()
        self.game_id = game_id
        self.total_prize_pool = len(self.players) * self.buy_in
        self.updated_at = datetime.now()
        return True
    
    def eliminate_player(self, player_id: str) -> Optional[int]:
        """Eliminate a player and return their final position"""
        player = next((p for p in self.players if p.player_id == player_id), None)
        if not player or player.eliminated:
            return None
        
        self.elimination_count += 1
        position = self.max_players - self.elimination_count + 1
        
        player.eliminated = True
        player.eliminated_at = datetime.now()
        player.final_position = position
        self.updated_at = datetime.now()
        
        # Check if tournament is complete (1 player remaining)
        if len(self.active_players) <= 1:
            self._complete_tournament()
        
        return position
    
    def _complete_tournament(self):
        """Mark tournament as complete"""
        self.status = TournamentStatus.COMPLETED
        self.tournament_end_time = datetime.now()
        
        # Assign 1st place to remaining active player
        for player in self.players:
            if not player.eliminated:
                player.final_position = 1
                player.eliminated_at = datetime.now()  # Mark when they "finished"
    
    def advance_level(self) -> bool:
        """Manually advance to next blind level"""
        if self.status != TournamentStatus.ACTIVE:
            return False
        
        self.current_level_index += 1
        self.level_start_time = datetime.now()
        self.updated_at = datetime.now()
        return True
    
    def check_level_advance(self) -> bool:
        """Check if it's time to advance blinds and do so if needed"""
        if self.status != TournamentStatus.ACTIVE:
            return False
        if not self.level_start_time:
            return False
        
        current = self.current_blind_level
        elapsed = datetime.now() - self.level_start_time
        
        if elapsed >= timedelta(minutes=current.duration_minutes):
            return self.advance_level()
        return False
    
    def get_prizes(self) -> List[Dict[str, Any]]:
        """Get prize distribution with actual chip amounts"""
        prizes = []
        for prize in self.prize_structure:
            amount = int(self.total_prize_pool * prize.percentage / 100)
            prizes.append({
                'position': prize.position,
                'percentage': prize.percentage,
                'amount': amount
            })
        return prizes
    
    def get_prize_for_position(self, position: int) -> int:
        """Get prize amount for a specific position"""
        for prize in self.prize_structure:
            if prize.position == position:
                return int(self.total_prize_pool * prize.percentage / 100)
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tournament to dictionary"""
        return {
            'tournament_id': self.tournament_id,
            'status': self.status.value,
            'max_players': self.max_players,
            'registered_players': len(self.players),
            'active_players': len(self.active_players),
            'eliminated_players': self.elimination_count,
            'buy_in': self.buy_in,
            'total_prize_pool': self.total_prize_pool,
            'current_level': self.current_blind_level.to_dict(),
            'level_index': self.current_level_index + 1,
            'time_in_level': self.time_in_current_level,
            'time_remaining_in_level': self.time_remaining_in_level,
            'players': [p.to_dict() for p in self.players],
            'prizes': self.get_prizes(),
            'game_id': self.game_id,
            'can_start': self.status == TournamentStatus.WAITING and len(self.players) >= 2,
            'created_at': self.created_at.isoformat(),
            'started_at': self.tournament_start_time.isoformat() if self.tournament_start_time else None,
            'completed_at': self.tournament_end_time.isoformat() if self.tournament_end_time else None
        }


class TournamentManager:
    """Manages all active tournaments"""
    
    def __init__(self):
        self.tournaments: Dict[str, Tournament] = {}
    
    def create_tournament(
        self,
        max_players: int = 6,
        buy_in: int = 1000,
        blind_structure: Optional[List[BlindLevel]] = None,
        prize_structure: Optional[List[TournamentPrize]] = None
    ) -> Tournament:
        """Create a new tournament"""
        import uuid
        tournament_id = f"tourn_{uuid.uuid4().hex[:8]}"
        
        tournament = Tournament(
            tournament_id=tournament_id,
            max_players=max_players,
            buy_in=buy_in,
            blind_structure=blind_structure,
            prize_structure=prize_structure
        )
        self.tournaments[tournament_id] = tournament
        return tournament
    
    def get_tournament(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        return self.tournaments.get(tournament_id)
    
    def list_tournaments(self, status: Optional[str] = None) -> List[Tournament]:
        """List all tournaments, optionally filtered by status"""
        tournaments = list(self.tournaments.values())
        if status:
            tournaments = [t for t in tournaments if t.status.value == status]
        return tournaments
    
    def cleanup_old_tournaments(self, max_age_hours: int = 24):
        """Remove completed tournaments older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for tid, tournament in self.tournaments.items():
            if tournament.status == TournamentStatus.COMPLETED:
                if tournament.tournament_end_time and tournament.tournament_end_time < cutoff:
                    to_remove.append(tid)
            elif tournament.status == TournamentStatus.WAITING:
                # Also clean up old waiting tournaments
                if tournament.created_at < cutoff:
                    to_remove.append(tid)
        
        for tid in to_remove:
            del self.tournaments[tid]
        
        return len(to_remove)
    
    def check_all_blind_levels(self) -> List[str]:
        """Check all active tournaments for blind level advancement"""
        advanced = []
        for tournament in self.tournaments.values():
            if tournament.status == TournamentStatus.ACTIVE:
                if tournament.check_level_advance():
                    advanced.append(tournament.tournament_id)
        return advanced


# Global tournament manager instance
tournament_manager = TournamentManager()
