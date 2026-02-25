"""
Game Metrics Tracking for Poker
Tracks performance stats, player behavior, and game analytics
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class PlayerBehavior:
    """Tracks individual player behavior patterns"""
    player_id: str
    player_name: str
    total_actions: int = 0
    folds: int = 0
    calls: int = 0
    raises: int = 0
    all_ins: int = 0
    checks: int = 0
    
    @property
    def fold_percentage(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return (self.folds / self.total_actions) * 100
    
    @property
    def call_percentage(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return (self.calls / self.total_actions) * 100
    
    @property
    def raise_percentage(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return (self.raises / self.total_actions) * 100
    
    def record_action(self, action: str):
        """Record a player action"""
        self.total_actions += 1
        if action == 'fold':
            self.folds += 1
        elif action == 'call':
            self.calls += 1
        elif action == 'raise':
            self.raises += 1
        elif action == 'all-in':
            self.all_ins += 1
        elif action == 'check':
            self.checks += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'player_id': self.player_id,
            'player_name': self.player_name,
            'total_actions': self.total_actions,
            'fold_percentage': round(self.fold_percentage, 1),
            'call_percentage': round(self.call_percentage, 1),
            'raise_percentage': round(self.raise_percentage, 1),
            'all_ins': self.all_ins,
            'checks': self.checks
        }


@dataclass
class GameMetrics:
    """Tracks overall game metrics and statistics"""
    game_id: str
    session_start: datetime = field(default_factory=datetime.utcnow)
    hands_played: int = 0
    total_pot_size: int = 0
    hand_start_times: List[datetime] = field(default_factory=list)
    player_behaviors: Dict[str, PlayerBehavior] = field(default_factory=dict)
    phase_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_hand_start(self):
        """Record the start of a new hand"""
        self.hands_played += 1
        self.hand_start_times.append(datetime.utcnow())
        # Keep only last 100 hand times for efficiency
        if len(self.hand_start_times) > 100:
            self.hand_start_times = self.hand_start_times[-100:]
    
    def record_hand_end(self, pot_size: int, phase: str):
        """Record the end of a hand"""
        self.total_pot_size += pot_size
        self.phase_counts[phase] += 1
    
    def record_player_action(self, player_id: str, player_name: str, action: str):
        """Record a player action for behavior tracking"""
        if player_id not in self.player_behaviors:
            self.player_behaviors[player_id] = PlayerBehavior(
                player_id=player_id,
                player_name=player_name
            )
        self.player_behaviors[player_id].record_action(action)
    
    @property
    def average_pot_size(self) -> float:
        """Calculate average pot size"""
        if self.hands_played == 0:
            return 0.0
        return self.total_pot_size / self.hands_played
    
    @property
    def hands_per_hour(self) -> float:
        """Calculate hands per hour based on recent activity"""
        if len(self.hand_start_times) < 2:
            return 0.0
        
        # Use last 10 hands or all hands, whichever is less
        recent_times = self.hand_start_times[-10:]
        if len(recent_times) < 2:
            return 0.0
        
        time_span = (recent_times[-1] - recent_times[0]).total_seconds()
        if time_span == 0:
            return 0.0
        
        hands = len(recent_times) - 1
        hours = time_span / 3600
        return hands / hours if hours > 0 else 0.0
    
    @property
    def session_duration_minutes(self) -> float:
        """Calculate session duration in minutes"""
        elapsed = datetime.utcnow() - self.session_start
        return elapsed.total_seconds() / 60
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        return {
            'game_id': self.game_id,
            'session_start': self.session_start.isoformat(),
            'session_duration_minutes': round(self.session_duration_minutes, 1),
            'hands_played': self.hands_played,
            'average_pot_size': round(self.average_pot_size, 0),
            'hands_per_hour': round(self.hands_per_hour, 1),
            'total_pot_accumulated': self.total_pot_size,
            'phase_distribution': dict(self.phase_counts),
            'player_behaviors': [
                behavior.to_dict() 
                for behavior in self.player_behaviors.values()
            ]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Alias for get_summary"""
        return self.get_summary()


class MetricsManager:
    """Manages metrics for multiple games"""
    
    def __init__(self):
        self.game_metrics: Dict[str, GameMetrics] = {}
    
    def get_or_create_metrics(self, game_id: str) -> GameMetrics:
        """Get existing metrics or create new ones for a game"""
        if game_id not in self.game_metrics:
            self.game_metrics[game_id] = GameMetrics(game_id=game_id)
        return self.game_metrics[game_id]
    
    def record_hand_start(self, game_id: str):
        """Record hand start for a game"""
        metrics = self.get_or_create_metrics(game_id)
        metrics.record_hand_start()
    
    def record_hand_end(self, game_id: str, pot_size: int, phase: str):
        """Record hand end for a game"""
        metrics = self.get_or_create_metrics(game_id)
        metrics.record_hand_end(pot_size, phase)
    
    def record_player_action(self, game_id: str, player_id: str, player_name: str, action: str):
        """Record a player action"""
        metrics = self.get_or_create_metrics(game_id)
        metrics.record_player_action(player_id, player_name, action)
    
    def get_metrics(self, game_id: str) -> Optional[GameMetrics]:
        """Get metrics for a specific game"""
        return self.game_metrics.get(game_id)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all games"""
        return {
            game_id: metrics.get_summary() 
            for game_id, metrics in self.game_metrics.items()
        }
    
    def cleanup_old_games(self, max_age_hours: float = 24.0):
        """Remove metrics for games older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = [
            game_id for game_id, metrics in self.game_metrics.items()
            if metrics.session_start < cutoff
        ]
        for game_id in to_remove:
            del self.game_metrics[game_id]
        return len(to_remove)


# Global metrics manager instance
metrics_manager = MetricsManager()
