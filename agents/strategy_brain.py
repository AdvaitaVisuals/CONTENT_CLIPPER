from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import json

@dataclass
class ContentDecision:
    action: str  # "post", "hold", "repeat", "stop"
    content_id: str
    platform: str
    scheduled_time: str # datetime string
    reason: str
    priority: int  # 1-5, 1 is highest
    emotion: str
    predicted_score: float

class StrategyBrain:
    def __init__(self):
        self.content_queue = []
        
    def make_decisions(self, 
                       clips: List[Dict],
                       trend_insights: List[Dict],
                       memory_data: Dict,
                       duration_days: int = 15) -> Dict[str, Any]:
        """Pura content calendar aur strategy decide karo"""
        
        # 1. Rank clips by predicted performance
        ranked_clips = self._rank_clips(clips, trend_insights, memory_data)
        
        # 2. Identify weak content (Stop List)
        stop_list = self._identify_weak_content(ranked_clips, memory_data)
        
        # Filter out weak clips for scheduling
        active_clips = [c for c in ranked_clips if c not in [s['clip'] for s in stop_list]]
        
        # 3. Create posting schedule
        schedule, platform_decisions = self._create_schedule(active_clips, duration_days)
        
        # 4. Generate simple action commands
        action_commands = self._generate_commands(schedule)
        
        return {
            "content_calendar": [asdict(s) for s in schedule],
            "platform_strategy": platform_decisions,
            "action_commands": action_commands,
            "stop_list": [{"clip_id": s['clip']['clip_id'], "reason": s['reason'], "action": s['action']} for s in stop_list],
            "weekly_guidance": self._generate_guidance(trend_insights, active_clips)
        }
    
    def _rank_clips(self, clips: List[Dict], trends: List[Dict], memory: Dict) -> List[Dict]:
        """Clips ko predicted performance se rank karo"""
        ranked = []
        for clip in clips:
            # Base score from viral cutter
            score = clip.get("score", 0.5)
            
            # Trend alignment bonus
            clip_emotion = self._get_emotion(clip)
            for trend in trends:
                if trend.get("trend_type") == "content_format":
                    if clip_emotion in trend.get("description", "").lower():
                        score += 0.15
            
            # Memory-based adjustment (Mocked logic if memory empty)
            emotion_perf = memory.get("emotion_performance", {}).get(clip_emotion, {})
            if emotion_perf.get("avg_engagement", 0) > 0.05:
                score += 0.1
            
            # Duration alignment
            # Assume trends have a duration finding, else default
            optimal_duration_range = (6, 8) # Default
            # logic to parse trends for duration would go here
            
            clip_duration = clip.get("end_time", 0) - clip.get("start_time", 0)
            if optimal_duration_range[0] <= clip_duration <= optimal_duration_range[1]:
                score += 0.1
            
            # Create a copy to avoid mutating original list permanently if re-used
            clip_copy = clip.copy()
            clip_copy["predicted_score"] = min(score, 1.0)
            clip_copy["emotion"] = clip_emotion
            
            # Ensure clip_id exists (might come from filename in real app, here we assign if missing)
            if "clip_id" not in clip_copy:
                 # Generate a temp/mock ID based on index or content
                 clip_copy["clip_id"] = f"clip_{int(clip.get('start_time', 0))}_{clip_emotion}"

            ranked.append(clip_copy)
        
        return sorted(ranked, key=lambda x: x["predicted_score"], reverse=True)
    
    def _get_emotion(self, clip: Dict) -> str:
        """Helper to safely get emotion string"""
        emotions = clip.get("emotions", [])
        if not emotions:
             # Infer from reasoning if needed
             reason = clip.get("viral_reason", "").lower()
             if "akad" in reason: return "akad"
             if "sad" in reason: return "dard"
        return emotions[0] if emotions else "general"

    def _identify_weak_content(self, ranked_clips: List[Dict], memory: Dict) -> List[Dict]:
        """Kaunsa content band karna chahiye"""
        weak = []
        failing_emotions = [
            emotion for emotion, data in memory.get("emotion_performance", {}).items()
            if data.get("avg_engagement", 0) < 0.02
        ]
        
        for clip in ranked_clips:
            reason = ""
            action = ""
            
            if clip.get("predicted_score", 0) < 0.4:
                reason = "Low viral potential score (< 0.4)"
                action = "SKIP"
            
            elif clip.get("emotion") in failing_emotions:
                reason = f"'{clip.get('emotion')}' consistently underperforms"
                action = "CAUTION"

            if action:
                weak.append({"clip": clip, "reason": reason, "action": action})
                
        return weak
    
    def _create_schedule(self, active_clips: List[Dict], days: int) -> tuple[List[ContentDecision], Dict]:
        """Content calendar banao"""
        schedule = []
        platform_decisions = {}
        
        if not active_clips:
            return [], {}
            
        clips_per_day = max(1, len(active_clips) // days)
        start_date = datetime.now() + timedelta(days=1) # Start tomorrow
        
        # Sort by score primarily
        clip_pool = active_clips.copy()
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Pick top clips for this day
            day_clips = []
            for _ in range(clips_per_day):
                if clip_pool:
                    day_clips.append(clip_pool.pop(0))
            
            for i, clip in enumerate(day_clips):
                emotion = clip.get("emotion", "general")
                
                # Time slot logic
                if emotion == "dard":
                    time_slot = "07:00"
                elif emotion == "akad":
                    time_slot = "19:00"
                else:
                    time_slot = "12:00" if i == 0 else "18:00"
                
                platform = self._select_best_platform(clip)
                
                scheduled_dt = f"{current_date.strftime('%Y-%m-%d')} {time_slot}"
                
                decision = ContentDecision(
                    action="post",
                    content_id=clip["clip_id"],
                    platform=platform,
                    scheduled_time=scheduled_dt,
                    reason=f"High score ({clip['predicted_score']:.2f}) & {emotion} fit for {time_slot}",
                    priority=1 if clip['predicted_score'] > 0.8 else 2,
                    emotion=emotion,
                    predicted_score=clip['predicted_score']
                )
                
                schedule.append(decision)
                
                # Track platform distribution
                platform_decisions[platform] = platform_decisions.get(platform, 0) + 1
                
        return schedule, platform_decisions
    
    def _select_best_platform(self, clip: Dict) -> str:
        """Clip ke liye best platform choose karo"""
        # If we had platform_fit data from cutter, use it. 
        # Fallback to defaults.
        
        duration = clip.get("end_time", 0) - clip.get("start_time", 0)
        
        if duration <= 15:
            return "instagram_reel"
        elif duration <= 60:
            return "youtube_shorts"
        else:
            return "facebook"
    
    def _generate_commands(self, schedule: List[ContentDecision]) -> List[str]:
        """Simple Hinglish commands generate karo"""
        commands = []
        
        # Group by date for clearer reading
        schedule.sort(key=lambda x: x.scheduled_time)
        
        for decision in schedule[:7]: # Show next few decisions
            # Parse date for simple display "Day 1", "Day 2" logic or just date
            dt = datetime.strptime(decision.scheduled_time, "%Y-%m-%d %H:%M")
            date_str = dt.strftime("%d %b")
            time_str = dt.strftime("%I:%M %p")
            
            cmd = f"[{date_str}] {decision.content_id}: {decision.platform} pe {time_str} post karo"
            
            if decision.emotion == "akad":
                cmd += " (akad content = evening rush)"
            elif decision.emotion == "dard":
                cmd += " (sad content = morning vibe)"
                
            commands.append(cmd)
        
        return commands

    def _generate_guidance(self, trends: List[Dict], active_clips: List[Dict]) -> str:
        count = len(active_clips)
        if not count: return "Content khatam! Naya banao."
        
        top_emotion = "general"
        if active_clips:
             # simple mode
             emotions = [c.get("emotion") for c in active_clips]
             top_emotion = max(set(emotions), key=emotions.count)
             
        return f"Total {count} clips ready. '{top_emotion}' content dominant hai. Schedule follow karo."

if __name__ == "__main__":
    brain = StrategyBrain()
    print("Strategy Brain initialized.")
