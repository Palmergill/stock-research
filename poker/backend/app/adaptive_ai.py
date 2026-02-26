"""
Adaptive AI - Tracks player tendencies and adjusts AI behavior
"""
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time


class PlayerTendencyTracker:
    """Tracks a single player's tendencies over time"""
    
    def __init__(self, player_id: str, player_name: str):
        self.player_id = player_id
        self.player_name = player_name
        
        # Action tracking
        self.total_actions = 0
        self.folds = 0
        self.calls = 0
        self.raises = 0
        self.checks = 0
        self.all_ins = 0
        
        # Phase-specific actions
        self.preflop_raises = 0
        self.preflop_calls = 0
        self.preflop_folds = 0
        
        # Aggression metrics
        self.total_bets = 0
        self.total_bet_amount = 0
        self.biggest_pot_won = 0
        
        # Behavioral patterns
        self.hands_played = 0
        self.hands_won = 0
        self.showdowns_reached = 0
        self.bluffs_attempted = 0  # Tracked via weak hand raises
        
        # Timing patterns
        self.decision_times: List[float] = []
        
        # Session tracking
        self.first_seen = time.time()
        self.last_seen = time.time()
    
    def record_action(self, action: str, amount: int, game_phase: str, 
                     hand_strength: float, decision_time_ms: Optional[int] = None):
        """Record a player action"""
        self.total_actions += 1
        self.last_seen = time.time()
        
        # Track action type
        if action == 'fold':
            self.folds += 1
            if game_phase == 'preflop':
                self.preflop_folds += 1
        elif action == 'call':
            self.calls += 1
            if game_phase == 'preflop':
                self.preflop_calls += 1
        elif action == 'raise':
            self.raises += 1
            self.total_bets += 1
            self.total_bet_amount += amount
            if game_phase == 'preflop':
                self.preflop_raises += 1
            # Track potential bluffs (weak hand raises)
            if hand_strength < 0.4:
                self.bluffs_attempted += 1
        elif action == 'check':
            self.checks += 1
        elif action == 'all-in':
            self.all_ins += 1
        
        # Track decision time
        if decision_time_ms:
            self.decision_times.append(decision_time_ms)
            # Keep last 50 times
            if len(self.decision_times) > 50:
                self.decision_times = self.decision_times[-50:]
    
    def record_hand_result(self, won: bool, reached_showdown: bool, pot_size: int = 0):
        """Record the result of a hand"""
        self.hands_played += 1
        if won:
            self.hands_won += 1
            self.biggest_pot_won = max(self.biggest_pot_won, pot_size)
        if reached_showdown:
            self.showdowns_reached += 1
    
    def get_vpip(self) -> float:
        """Voluntarily Put $ In Pot - % of hands where player calls/raises preflop"""
        preflop_opportunities = self.preflop_raises + self.preflop_calls + self.preflop_folds
        if preflop_opportunities == 0:
            return 0.0
        return (self.preflop_raises + self.preflop_calls) / preflop_opportunities
    
    def get_pfr(self) -> float:
        """Pre-Flop Raise %"""
        preflop_opportunities = self.preflop_raises + self.preflop_calls + self.preflop_folds
        if preflop_opportunities == 0:
            return 0.0
        return self.preflop_raises / preflop_opportunities
    
    def get_af(self) -> float:
        """Aggression Factor - (raises + bets) / calls"""
        if self.calls == 0:
            return float(self.raises) if self.raises > 0 else 0.0
        return self.raises / self.calls
    
    def get_fold_to_3bet(self) -> float:
        """How often player folds to aggression (simplified)"""
        if self.total_actions == 0:
            return 0.0
        return self.folds / self.total_actions
    
    def get_avg_decision_time(self) -> float:
        """Average decision time in milliseconds"""
        if not self.decision_times:
            return 0.0
        return sum(self.decision_times) / len(self.decision_times)
    
    def get_win_rate(self) -> float:
        """Win rate percentage"""
        if self.hands_played == 0:
            return 0.0
        return self.hands_won / self.hands_played
    
    def get_showdown_percentage(self) -> float:
        """% of hands that reach showdown"""
        if self.hands_played == 0:
            return 0.0
        return self.showdowns_reached / self.hands_played
    
    def get_bluff_frequency(self) -> float:
        """Estimated bluff frequency based on weak hand raises"""
        if self.raises == 0:
            return 0.0
        return self.bluffs_attempted / self.raises
    
    def get_tendency_summary(self) -> Dict[str, Any]:
        """Get a summary of player tendencies"""
        return {
            "player_name": self.player_name,
            "hands_played": self.hands_played,
            "hands_won": self.hands_won,
            "win_rate": round(self.get_win_rate(), 3),
            "vpip": round(self.get_vpip(), 3),
            "pfr": round(self.get_pfr(), 3),
            "aggression_factor": round(self.get_af(), 2),
            "fold_percentage": round(self.get_fold_to_3bet(), 3),
            "showdown_percentage": round(self.get_showdown_percentage(), 3),
            "bluff_frequency": round(self.get_bluff_frequency(), 3),
            "avg_decision_time_ms": round(self.get_avg_decision_time(), 0),
            "total_actions": self.total_actions,
            "biggest_pot_won": self.biggest_pot_won,
            "session_duration_minutes": round((self.last_seen - self.first_seen) / 60, 1),
        }
    
    def get_player_type(self) -> str:
        """Classify player type based on tendencies"""
        vpip = self.get_vpip()
        pfr = self.get_pfr()
        af = self.get_af()
        
        if self.hands_played < 5:
            return "Unknown"
        
        # Tight-Aggressive (TAG)
        if vpip < 0.25 and pfr > 0.15 and af > 1.5:
            return "TAG (Tight-Aggressive)"
        
        # Loose-Aggressive (LAG)
        if vpip > 0.35 and af > 2.0:
            return "LAG (Loose-Aggressive)"
        
        # Tight-Passive (Rock)
        if vpip < 0.25 and af < 1.2:
            return "Rock (Tight-Passive)"
        
        # Loose-Passive (Calling Station)
        if vpip > 0.35 and af < 1.0:
            return "Calling Station"
        
        # Passive-Aggressive (Nit)
        if vpip < 0.20 and pfr < 0.10:
            return "Nit"
        
        return "Balanced"


class AdaptiveAIManager:
    """Manages adaptive AI adjustments based on player tendencies"""
    
    def __init__(self):
        self.player_trackers: Dict[str, PlayerTendencyTracker] = {}
        self.game_sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_or_create_tracker(self, player_id: str, player_name: str) -> PlayerTendencyTracker:
        """Get existing tracker or create new one"""
        if player_id not in self.player_trackers:
            self.player_trackers[player_id] = PlayerTendencyTracker(player_id, player_name)
        return self.player_trackers[player_id]
    
    def record_player_action(self, player_id: str, player_name: str, action: str, 
                            amount: int, game_phase: str, hand_strength: float = 0.5,
                            decision_time_ms: Optional[int] = None):
        """Record a player action for tendency tracking"""
        tracker = self.get_or_create_tracker(player_id, player_name)
        tracker.record_action(action, amount, game_phase, hand_strength, decision_time_ms)
    
    def record_hand_result(self, player_id: str, won: bool, reached_showdown: bool, 
                          pot_size: int = 0):
        """Record hand result"""
        if player_id in self.player_trackers:
            self.player_trackers[player_id].record_hand_result(won, reached_showdown, pot_size)
    
    def get_adjustment_factors(self, player_id: str) -> Dict[str, float]:
        """
        Get AI adjustment factors based on player tendencies.
        Returns multipliers for AI behavior adjustments.
        """
        if player_id not in self.player_trackers:
            return {
                "bluff_frequency_multiplier": 1.0,
                "call_threshold_multiplier": 1.0,
                "raise_threshold_multiplier": 1.0,
                "hand_strength_threshold_multiplier": 1.0,
            }
        
        tracker = self.player_trackers[player_id]
        player_type = tracker.get_player_type()
        vpip = tracker.get_vpip()
        af = tracker.get_af()
        fold_pct = tracker.get_fold_to_3bet()
        
        adjustments = {
            "bluff_frequency_multiplier": 1.0,
            "call_threshold_multiplier": 1.0,
            "raise_threshold_multiplier": 1.0,
            "hand_strength_threshold_multiplier": 1.0,
        }
        
        # Adjust based on player type
        if player_type == "Calling Station":
            # Bluff less, value bet more - they call everything
            adjustments["bluff_frequency_multiplier"] = 0.5
            adjustments["raise_threshold_multiplier"] = 0.8  # Raise more for value
        
        elif player_type == "Rock (Tight-Passive)":
            # Bluff more, they fold too much
            adjustments["bluff_frequency_multiplier"] = 1.5
            adjustments["call_threshold_multiplier"] = 1.2  # Call less against their strong range
        
        elif player_type == "LAG (Loose-Aggressive)":
            # Play tighter, trap them when you have hands
            adjustments["hand_strength_threshold_multiplier"] = 0.85  # Play tighter
            adjustments["raise_threshold_multiplier"] = 0.9  # Raise more to punish
        
        elif player_type == "TAG (Tight-Aggressive)":
            # Respect their raises, steal blinds more
            adjustments["call_threshold_multiplier"] = 1.3  # Call less against their range
            adjustments["hand_strength_threshold_multiplier"] = 0.9  # Slightly tighter
        
        elif player_type == "Nit":
            # Steal their blinds constantly, fold to their raises
            adjustments["bluff_frequency_multiplier"] = 1.8  # Bluff more preflop
            adjustments["call_threshold_multiplier"] = 1.5  # Fold more to their raises
        
        # Additional adjustments based on specific stats
        if fold_pct > 0.6:
            # Player folds too much - exploit with more bluffs
            adjustments["bluff_frequency_multiplier"] *= 1.3
        
        if vpip > 0.5:
            # Player plays too loose - tighten up and punish
            adjustments["raise_threshold_multiplier"] *= 0.85
        
        return adjustments
    
    def get_player_analysis(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis for a player"""
        if player_id not in self.player_trackers:
            return None
        
        tracker = self.player_trackers[player_id]
        summary = tracker.get_tendency_summary()
        summary["player_type"] = tracker.get_player_type()
        summary["ai_adjustments"] = self.get_adjustment_factors(player_id)
        
        # Add recommendations
        player_type = tracker.get_player_type()
        recommendations = []
        
        if player_type == "Calling Station":
            recommendations.append("Don't bluff - they call everything")
            recommendations.append("Value bet thinner - they call with weak hands")
            recommendations.append("Avoid marginal bluffs post-flop")
        elif player_type == "Rock (Tight-Passive)":
            recommendations.append("Steal their blinds frequently")
            recommendations.append("Fold to their raises - they have it")
            recommendations.append("Bluff more when they show weakness")
        elif player_type == "LAG (Loose-Aggressive)":
            recommendations.append("Let them bluff into your strong hands")
            recommendations.append("Don't try to bluff them")
            recommendations.append("Play tighter ranges against them")
        elif player_type == "TAG (Tight-Aggressive)":
            recommendations.append("Respect their aggression")
            recommendations.append("Steal blinds when they're not in the hand")
            recommendations.append("Play position against them")
        
        summary["recommendations"] = recommendations
        return summary
    
    def get_all_analyses(self) -> Dict[str, Dict[str, Any]]:
        """Get analysis for all tracked players"""
        return {
            player_id: self.get_player_analysis(player_id)
            for player_id in self.player_trackers
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics"""
        if not self.player_trackers:
            return {
                "total_players_tracked": 0,
                "total_hands_played": 0,
                "avg_vpip": 0,
                "avg_af": 0,
            }
        
        total_hands = sum(t.hands_played for t in self.player_trackers.values())
        avg_vpip = sum(t.get_vpip() for t in self.player_trackers.values()) / len(self.player_trackers)
        avg_af = sum(t.get_af() for t in self.player_trackers.values()) / len(self.player_trackers)
        
        return {
            "total_players_tracked": len(self.player_trackers),
            "total_hands_played": total_hands,
            "avg_vpip": round(avg_vpip, 3),
            "avg_af": round(avg_af, 2),
        }


# Global adaptive AI manager instance
adaptive_ai_manager = AdaptiveAIManager()
