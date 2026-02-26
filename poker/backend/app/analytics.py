"""
Usage Analytics - Lightweight session and usage tracking
"""
import time
import uuid
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class SessionTracker:
    """Tracks a single user session"""
    
    def __init__(self, session_id: str, player_id: str, player_name: str, ip_address: Optional[str] = None):
        self.session_id = session_id
        self.player_id = player_id
        self.player_name = player_name
        self.ip_address = ip_address
        
        self.created_at = time.time()
        self.last_activity = time.time()
        self.ended_at: Optional[float] = None
        
        # Activity tracking
        self.request_count = 0
        self.actions_taken = 0
        self.hands_played = 0
        self.games_created = 0
        
        # Session duration tracking
        self.total_time_active = 0
        self.last_activity_start = time.time()
    
    def record_activity(self, activity_type: str = "request"):
        """Record activity in the session"""
        now = time.time()
        self.last_activity = now
        self.request_count += 1
        
        if activity_type == "action":
            self.actions_taken += 1
        elif activity_type == "hand":
            self.hands_played += 1
        elif activity_type == "game_created":
            self.games_created += 1
    
    def get_duration_seconds(self) -> float:
        """Get session duration in seconds"""
        if self.ended_at:
            return self.ended_at - self.created_at
        return time.time() - self.created_at
    
    def get_duration_minutes(self) -> float:
        """Get session duration in minutes"""
        return self.get_duration_seconds() / 60
    
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """Check if session is still active (default 5 min timeout)"""
        if self.ended_at:
            return False
        return (time.time() - self.last_activity) < timeout_seconds
    
    def end_session(self):
        """Mark session as ended"""
        self.ended_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "player_name": self.player_name,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_activity": datetime.fromtimestamp(self.last_activity).isoformat(),
            "duration_minutes": round(self.get_duration_minutes(), 2),
            "is_active": self.is_active(),
            "request_count": self.request_count,
            "actions_taken": self.actions_taken,
            "hands_played": self.hands_played,
            "games_created": self.games_created,
        }


class UsageAnalytics:
    """Tracks overall usage analytics for the poker app"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionTracker] = {}
        self.player_sessions: Dict[str, List[str]] = defaultdict(list)  # player_id -> session_ids
        
        # Daily aggregations
        self.daily_stats: Dict[str, Dict[str, Any]] = {}
        
        # Hourly activity (last 24 hours)
        self.hourly_activity: Dict[str, int] = {}
        
        # Overall metrics
        self.total_requests = 0
        self.total_games_created = 0
        self.total_hands_played = 0
        self.total_actions = 0
        
        self.startup_time = time.time()
    
    def _get_today_key(self) -> str:
        """Get today's date key for daily stats"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_hour_key(self) -> str:
        """Get current hour key"""
        return datetime.now().strftime("%Y-%m-%d-%H")
    
    def _init_daily_stats(self, date_key: str):
        """Initialize daily stats if not exists"""
        if date_key not in self.daily_stats:
            self.daily_stats[date_key] = {
                "date": date_key,
                "unique_sessions": 0,
                "unique_players": set(),
                "total_requests": 0,
                "total_games": 0,
                "total_hands": 0,
                "total_actions": 0,
                "avg_session_duration": 0,
            }
    
    def start_session(self, player_id: str, player_name: str, ip_address: Optional[str] = None) -> str:
        """Start a new session"""
        session_id = str(uuid.uuid4())[:12]
        session = SessionTracker(session_id, player_id, player_name, ip_address)
        self.sessions[session_id] = session
        self.player_sessions[player_id].append(session_id)
        
        # Update daily stats
        today = self._get_today_key()
        self._init_daily_stats(today)
        self.daily_stats[today]["unique_sessions"] += 1
        self.daily_stats[today]["unique_players"].add(player_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionTracker]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def record_request(self, session_id: Optional[str] = None):
        """Record an API request"""
        self.total_requests += 1
        
        # Update hourly activity
        hour_key = self._get_hour_key()
        self.hourly_activity[hour_key] = self.hourly_activity.get(hour_key, 0) + 1
        
        # Update daily stats
        today = self._get_today_key()
        self._init_daily_stats(today)
        self.daily_stats[today]["total_requests"] += 1
        
        # Update session if provided
        if session_id and session_id in self.sessions:
            self.sessions[session_id].record_activity("request")
    
    def record_game_created(self, session_id: Optional[str] = None):
        """Record a new game creation"""
        self.total_games_created += 1
        
        today = self._get_today_key()
        self._init_daily_stats(today)
        self.daily_stats[today]["total_games"] += 1
        
        if session_id and session_id in self.sessions:
            self.sessions[session_id].record_activity("game_created")
    
    def record_hand_played(self, session_id: Optional[str] = None):
        """Record a hand being played"""
        self.total_hands_played += 1
        
        today = self._get_today_key()
        self._init_daily_stats(today)
        self.daily_stats[today]["total_hands"] += 1
        
        if session_id and session_id in self.sessions:
            self.sessions[session_id].record_activity("hand")
    
    def record_action(self, session_id: Optional[str] = None):
        """Record a player action"""
        self.total_actions += 1
        
        today = self._get_today_key()
        self._init_daily_stats(today)
        self.daily_stats[today]["total_actions"] += 1
        
        if session_id and session_id in self.sessions:
            self.sessions[session_id].record_activity("action")
    
    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.sessions:
            self.sessions[session_id].end_session()
    
    def get_active_sessions(self, timeout_seconds: int = 300) -> List[SessionTracker]:
        """Get all currently active sessions"""
        return [s for s in self.sessions.values() if s.is_active(timeout_seconds)]
    
    def get_active_session_count(self, timeout_seconds: int = 300) -> int:
        """Get count of active sessions"""
        return len(self.get_active_sessions(timeout_seconds))
    
    def get_unique_player_count(self, hours: int = 24) -> int:
        """Get count of unique players in last N hours"""
        cutoff = time.time() - (hours * 3600)
        unique_players = set()
        
        for session in self.sessions.values():
            if session.created_at > cutoff:
                unique_players.add(session.player_id)
        
        return len(unique_players)
    
    def get_hourly_activity_data(self, hours: int = 24) -> Dict[str, int]:
        """Get hourly activity for last N hours"""
        result = {}
        now = datetime.now()
        
        for i in range(hours):
            hour_time = now - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%d-%H")
            result[hour_key] = self.hourly_activity.get(hour_key, 0)
        
        return result
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily stats for last N days"""
        result = []
        now = datetime.now()
        
        for i in range(days):
            day_time = now - timedelta(days=i)
            day_key = day_time.strftime("%Y-%m-%d")
            
            if day_key in self.daily_stats:
                stats = self.daily_stats[day_key].copy()
                stats["unique_players"] = len(stats["unique_players"])
                result.append(stats)
            else:
                result.append({
                    "date": day_key,
                    "unique_sessions": 0,
                    "unique_players": 0,
                    "total_requests": 0,
                    "total_games": 0,
                    "total_hands": 0,
                    "total_actions": 0,
                })
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall usage summary"""
        uptime_hours = (time.time() - self.startup_time) / 3600
        
        # Calculate average session duration
        completed_sessions = [s for s in self.sessions.values() if s.ended_at]
        avg_session_duration = (
            sum(s.get_duration_minutes() for s in completed_sessions) / len(completed_sessions)
            if completed_sessions else 0
        )
        
        # Get today's stats
        today = self._get_today_key()
        today_stats = self.daily_stats.get(today, {
            "unique_sessions": 0,
            "unique_players": set(),
            "total_requests": 0,
            "total_games": 0,
            "total_hands": 0,
            "total_actions": 0,
        })
        
        return {
            "uptime_hours": round(uptime_hours, 2),
            "active_sessions": self.get_active_session_count(),
            "active_sessions_5min": self.get_active_session_count(300),
            "total_sessions": len(self.sessions),
            "unique_players_24h": self.get_unique_player_count(24),
            "avg_session_duration_minutes": round(avg_session_duration, 2),
            "total_requests": self.total_requests,
            "total_games_created": self.total_games_created,
            "total_hands_played": self.total_hands_played,
            "total_actions": self.total_actions,
            "requests_per_hour": round(self.total_requests / max(uptime_hours, 0.1), 2),
            "today": {
                "unique_sessions": today_stats.get("unique_sessions", 0),
                "unique_players": len(today_stats.get("unique_players", set())),
                "requests": today_stats.get("total_requests", 0),
                "games_created": today_stats.get("total_games", 0),
                "hands_played": today_stats.get("total_hands", 0),
                "actions": today_stats.get("total_actions", 0),
            },
            "hourly_activity": self.get_hourly_activity_data(24),
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours"""
        cutoff = time.time() - (max_age_hours * 3600)
        
        sessions_to_remove = [
            sid for sid, session in self.sessions.items()
            if session.created_at < cutoff and session.ended_at
        ]
        
        for sid in sessions_to_remove:
            if sid in self.sessions:
                session = self.sessions[sid]
                # Remove from player_sessions
                if session.player_id in self.player_sessions:
                    self.player_sessions[session.player_id] = [
                        s for s in self.player_sessions[session.player_id] if s != sid
                    ]
                # Remove session
                del self.sessions[sid]
        
        return len(sessions_to_remove)


# Global usage analytics instance
usage_analytics = UsageAnalytics()
