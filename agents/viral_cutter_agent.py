import ffmpeg
from dataclasses import dataclass
from typing import List, Optional, Dict
import os
import imageio_ffmpeg

@dataclass
class ClipSpec:
    start_time: float
    end_time: float
    hook_line: str
    target_audience: str
    viral_reason: str
    platform: str
    aspect_ratio: str
    score: float = 0.0

class ViralCutterAgent:
    def __init__(self):
        self.clip_templates = {
            "instagram_reel": {"duration": (7, 15), "aspect": "9:16"},
            "youtube_shorts": {"duration": (15, 60), "aspect": "9:16"},
            "facebook_reel": {"duration": (15, 30), "aspect": "9:16"},
            "story": {"duration": (5, 15), "aspect": "9:16"}
        }
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
    def generate_clip_specs(self, understanding_data: dict) -> List[ClipSpec]:
        """Analysis se clip specifications generate karo"""
        clips = []
        segments = understanding_data.get("lyrics_segments", [])
        drops = (understanding_data.get("beat_analysis", {}).get("drop_timestamps", []) or 
                 understanding_data.get("beat_analysis", {}).get("drop_times", []))

        # Strategy 1: High viral potential lines (lowered threshold for more clips)
        for seg in segments:
            if seg.get("viral_potential", 0) > 0.6:
                clip = self._create_hook_first_clip(seg, segments)
                clips.append(clip)

        # Strategy 2: Beat drop moments
        for drop_time in drops[:5]:  # Top 5 drops
            clip = self._create_drop_clip(drop_time, segments)
            clips.append(clip)

        # Strategy 3: Chorus loops (all occurrences)
        chorus = (understanding_data.get("beat_analysis", {}).get("chorus_timestamps", []) or 
                  understanding_data.get("beat_analysis", {}).get("chorus_times", []))
        for ct in chorus[:3]:
            clip = self._create_chorus_clip(ct, segments)
            clips.append(clip)

        # Strategy 4: Emotion-based clips
        clips.extend(self._create_emotion_clips(segments))

        # Strategy 5: Evenly spaced segments across the song for variety
        if segments:
            duration = segments[-1].get("end", 0)
            if duration > 30:
                for offset in range(0, int(duration) - 15, int(duration // 6)):
                    nearby = [s for s in segments if abs(s["start"] - offset) < 5]
                    if nearby:
                        best = max(nearby, key=lambda s: s.get("viral_potential", 0))
                        clips.append(self._create_hook_first_clip(best, segments))

        return self._deduplicate_and_rank(clips)
    
    def _create_hook_first_clip(self, hook_segment: dict, all_segments: list) -> ClipSpec:
        """Pehle few sec mein hook wali clip - Increased duration for 'lambi reel'"""
        start = max(0, hook_segment["start"] - 0.5)
        # Increased duration from 12s to 30s
        end = min(hook_segment.get("end", start+15) + 15, start + 35)
        
        return ClipSpec(
            start_time=start,
            end_time=end,
            hook_line=hook_segment["text"],
            target_audience=self._determine_audience(hook_segment.get("emotions", [])),
            viral_reason=f"Hook in first 1.5s: '{hook_segment['text'][:30]}...'",
            platform="instagram_reel",
            aspect_ratio="9:16",
            score=hook_segment.get("viral_potential", 0.5)
        )
    
    def _create_drop_clip(self, drop_time: float, segments: list) -> ClipSpec:
        """Beat drop clip - Increased duration"""
        hook_text = "Beat Drop 🔥"
        for seg in segments:
            if seg["start"] <= drop_time <= seg["end"]:
                hook_text = seg["text"]
                break
                
        return ClipSpec(
            start_time=max(0, drop_time - 10),
            end_time=drop_time + 20,
            hook_line=hook_text,
            target_audience="party_youth",
            viral_reason="High energy beat drop moment",
            platform="instagram_reel",
            aspect_ratio="9:16",
            score=0.8
        )

    def _create_chorus_clip(self, chorus_time: float, segments: list) -> ClipSpec:
        """Chorus clip - Increased duration"""
        # If chorus_time is a list, take the first one or iterate (simplified here to take first)
        start_t = chorus_time[0] if isinstance(chorus_time, list) else chorus_time
        
        return ClipSpec(
             start_time=max(0, start_t),
             end_time=start_t + 35,
             hook_line="Chorus Loop",
             target_audience="general",
             viral_reason="Repetitive catchy chorus",
             platform="instagram_reel",
             aspect_ratio="9:16",
             score=0.7
        )

    def _create_emotion_clips(self, segments: list) -> List[ClipSpec]:
        """Additional emotion based clips"""
        clips = []
        for index, seg in enumerate(segments):
            if "akad" in seg.get("emotions", []) and seg.get("viral_potential", 0) > 0.6:
                clips.append(self._create_hook_first_clip(seg, segments)) 
        return clips

    def _determine_audience(self, emotions: list) -> str:
        """Emotion se audience map karo"""
        audience_map = {
            "akad": "ladke_18_30_gaon_shehar",
            "dard": "all_sad_mood",
            "pyaar": "couples_romantic",
            "gaon_pride": "gaon_haryana_specific",
            "mauj": "party_mood_youth"
        }
        for emotion in emotions:
            if emotion in audience_map:
                return audience_map[emotion]
        return "general_haryanvi"
    
    def _deduplicate_and_rank(self, clips: List[ClipSpec]) -> List[ClipSpec]:
        """Remove duplicates and rank by score"""
        seen = set()
        unique_clips = []
        for clip in clips:
             # simple dedup key
             key = (round(clip.start_time, 1), round(clip.end_time, 1))
             if key not in seen:
                 seen.add(key)
                 unique_clips.append(clip)
        
        # Sort by score descending
        unique_clips.sort(key=lambda x: x.score, reverse=True)
        return unique_clips

    def cut_video(self, video_path: str, clip_spec: ClipSpec, output_path: str):
        """FFmpeg se actual cutting using full subprocess instead of wrapper to force binary path"""
        duration = clip_spec.end_time - clip_spec.start_time
        
        # Construct ffmpeg command directly
        import subprocess
        
        cmd = [
            self.ffmpeg_path,
            '-ss', str(clip_spec.start_time),
            '-i', video_path,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-y', # overwrite
            output_path
        ]
        
        # Optional: Add crop filter if needed
        # cmd.extend(['-vf', "crop=ih*(9/16):ih"]) 
        
        # Execute
        subprocess.run(cmd, check=True)
        print(f"Clip saved: {output_path}")

    def add_captions_to_clip(self, video_path: str, text: str, style: str = "desi"):
        """Clip pe text overlay"""
        # Placeholder
        print(f"Adding caption '{text}' to {video_path} with style {style}")
        pass

if __name__ == "__main__":
    agent = ViralCutterAgent()
    print("Viral Cutter Agent initialized.")
