from dataclasses import dataclass
from typing import List, Optional, Dict
import os

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
        
        # Lazy load dependencies
        try:
            import imageio_ffmpeg
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            self.ffmpeg_path = "ffmpeg"  # Normal system ffmpeg as fallback
            print("ViralCutterAgent: imageio_ffmpeg not found, using 'ffmpeg'")
            
    def generate_clip_specs(self, understanding_data: dict) -> List[ClipSpec]:
        """Analysis se diverse and high-potential clip specifications generate karo"""
        clips = []
        segments = understanding_data.get("lyrics_segments", [])
        drops = (understanding_data.get("beat_analysis", {}).get("drop_timestamps", []) or 
                 understanding_data.get("beat_analysis", {}).get("drop_times", []))

        # Strategy 1: Top 3 High viral potential lines (spread them out)
        potential_lines = [s for s in segments if s.get("viral_potential", 0) > 0.6]
        potential_lines.sort(key=lambda s: s.get("viral_potential", 0), reverse=True)
        
        seen_ranges = []
        for seg in potential_lines[:5]:
            # Ensure we don't pick lines too close to each other
            is_too_close = any(abs(seg["start"] - r) < 20 for r in seen_ranges)
            if not is_too_close:
                clips.append(self._create_hook_first_clip(seg, segments))
                seen_ranges.append(seg["start"])

        # Strategy 2: Top 3 unique beat drops
        for drop_time in drops[:5]:
            is_too_close = any(abs(drop_time - r) < 15 for r in seen_ranges)
            if not is_too_close:
                clips.append(self._create_drop_clip(drop_time, segments))
                seen_ranges.append(drop_time)

        # Strategy 3: Chorus Loops (diverse parts)
        chorus = (understanding_data.get("beat_analysis", {}).get("chorus_timestamps", []) or 
                  understanding_data.get("beat_analysis", {}).get("chorus_times", []))
        for ct in chorus[:3]:
            start_t = ct[0] if isinstance(ct, list) else ct
            is_too_close = any(abs(start_t - r) < 10 for r in seen_ranges)
            if not is_too_close:
                 clips.append(self._create_chorus_clip(ct, segments))
                 seen_ranges.append(start_t)

        # Strategy 4: Final Emotion Check (unique only)
        for index, seg in enumerate(segments):
            if "akad" in seg.get("emotions", []) and seg.get("viral_potential", 0) > 0.8:
                if not any(abs(seg["start"] - r) < 15 for r in seen_ranges):
                    clips.append(self._create_hook_first_clip(seg, segments))
                    seen_ranges.append(seg["start"])

        return self._deduplicate_and_rank(clips)
    
    def _create_hook_first_clip(self, hook_segment: dict, all_segments: list) -> ClipSpec:
        """Pehle few sec mein hook wali clip"""
        start = max(0, hook_segment["start"] - 0.5)
        end = min(hook_segment.get("end", start+15) + 18, start + 35)
        
        return ClipSpec(
            start_time=start,
            end_time=end,
            hook_line=hook_segment["text"],
            target_audience=self._determine_audience(hook_segment.get("emotions", [])),
            viral_reason=f"Hook: '{hook_segment['text'][:20]}'",
            platform="instagram_reel",
            aspect_ratio="9:16",
            score=hook_segment.get("viral_potential", 0.5)
        )
    
    def _create_drop_clip(self, drop_time: float, segments: list) -> ClipSpec:
        """Beat drop clip"""
        hook_text = "DUNIYA DEKHEGI 🔥"
        for seg in segments:
            if seg["start"] <= drop_time <= seg["end"]:
                hook_text = seg["text"]
                break
                
        return ClipSpec(
            start_time=max(0, drop_time - 5),
            end_time=drop_time + 20,
            hook_line=hook_text,
            target_audience="party_youth",
            viral_reason="High energy beat drop moment",
            platform="instagram_reel",
            aspect_ratio="9:16",
            score=0.8
        )

    def _create_chorus_clip(self, chorus_time: float, segments: list) -> ClipSpec:
        """Chorus clip"""
        start_t = chorus_time[0] if isinstance(chorus_time, list) else chorus_time
        
        return ClipSpec(
             start_time=max(0, start_t),
             end_time=start_t + 25,
             hook_line="CHORUS VIBE 🚀",
             target_audience="general",
             viral_reason="Catchy chorus loop",
             platform="instagram_reel",
             aspect_ratio="9:16",
             score=0.7
        )

    def _create_emotion_clips(self, segments: list) -> List[ClipSpec]:
        """Additional emotion based clips - Handled in generate_clip_specs main now"""
        return []

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
        """Smarter deduplication: avoid overlapping clips and rank by score"""
        if not clips:
            return []
            
        clips.sort(key=lambda x: x.score, reverse=True)
        
        unique_clips = []
        for new_clip in clips:
            is_duplicate = False
            for existing in unique_clips:
                overlap_start = max(new_clip.start_time, existing.start_time)
                overlap_end = min(new_clip.end_time, existing.end_time)
                
                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    shorter_duration = min(new_clip.end_time - new_clip.start_time, 
                                          existing.end_time - existing.start_time)
                    
                    if overlap_duration > (shorter_duration * 0.4): # Strict overlap check
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_clips.append(new_clip)
        
        return unique_clips

    def cut_video(self, video_path: str, clip_spec: ClipSpec, output_path: str):
        """FFmpeg se actual cutting with 9:16 crop, Hook Text, and Desi Effects"""
        duration = clip_spec.end_time - clip_spec.start_time
        
        import subprocess
        
        # Determine Font (Windows vs Linux)
        font_path = "C\\\\:/Windows/Fonts/arialbd.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        # Clean hook line for FFmpeg drawtext (remove quotes etc)
        display_text = clip_spec.hook_line.replace("'", "").replace('"', '').upper()
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."
            
        # Video Filters: Crop -> Scale -> Color Grade (CLEAN - NO TEXT)
        video_filters = (
            f"crop=ih*(9/16):ih,scale=720:1280,"
            f"eq=contrast=1.2:saturation=1.4:brightness=0.02,"
            f"unsharp=3:3:1.5:3:3:0.5"
        )
        
        cmd = [
            self.ffmpeg_path,
            '-ss', f"{clip_spec.start_time:.3f}",
            '-i', video_path,
            '-t', f"{duration:.3f}",
            '-vf', video_filters,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '21',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y', 
            output_path
        ]
        
        print(f"🎬 Creating Reel: {display_text}")
        subprocess.run(cmd, check=True)
        print(f"✅ Saved: {output_path}")

    def add_captions_to_clip(self, video_path: str, text: str, style: str = "desi"):
        """Clip pe text overlay"""
        # Placeholder
        print(f"Adding caption '{text}' to {video_path} with style {style}")
        pass

if __name__ == "__main__":
    agent = ViralCutterAgent()
    print("Viral Cutter Agent initialized.")
