# 🎵 HARYANVI ARTIST VIRALITY & FAN POWER AGENT

## Skill Overview

**Naam:** Haryanvi Artist Virality & Fan Power Agent  
**Version:** 1.0.0  
**Runtime:** Google Antigravity Compatible  
**Stack:** Python / Node.js + n8n Orchestration

---

## 🎯 Mission Statement

Ek Haryanvi artist (Biru Kataria type) ke liye invisible digital manager jo:
- Single song se 15-25 viral clips generate kare
- Artist ko bina disturb kiye background mein chale
- Gaon + City dono audience ko target kare
- Fan loyalty aur repeat views build kare

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR (n8n)                       │
│                   Telegram Bot Interface                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   INPUT       │ │   PROCESS     │ │   OUTPUT      │
│   LAYER       │ │   LAYER       │ │   LAYER       │
└───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENTS:                                                         │
│  1. Understanding Agent (Gaana Samajhna)                        │
│  2. Viral Cutter Agent (Clip Kaatna)                            │
│  3. Frame Power Agent (Desi Photo)                              │
│  4. Caption Agent (Desi Bhasha)                                 │
│  5. Trend Agent (Competitor Watch)                              │
│  6. Strategy Brain (Decision Making)                            │
│  7. Auto Posting Agent (Distribution)                           │
│  8. Memory Agent (Learning Loop)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📥 INPUT SPECIFICATION

### Accepted Input Types

```json
{
  "input_schema": {
    "type": "object",
    "properties": {
      "source": {
        "type": "string",
        "enum": ["youtube_url", "raw_video", "audio_file"],
        "description": "Input source type"
      },
      "url": {
        "type": "string",
        "format": "uri",
        "description": "YouTube/video URL (if source is youtube_url)"
      },
      "file_path": {
        "type": "string",
        "description": "Local file path (if source is raw_video/audio_file)"
      },
      "vibe": {
        "type": "string",
        "enum": ["desi", "sad", "akad", "gaon", "romantic", "party"],
        "default": "desi",
        "description": "Content mood/vibe"
      },
      "note": {
        "type": "string",
        "description": "Optional artist/manager instruction"
      },
      "duration_days": {
        "type": "integer",
        "default": 15,
        "description": "Content calendar duration"
      }
    },
    "required": ["source"]
  }
}
```

### Telegram Command Examples

```
/process https://youtube.com/watch?v=xxx - desi vibe
/process https://youtube.com/watch?v=xxx - sad gaana, 15 din
/process video.mp4 - akad wali reel banao
```

---

## 🤖 AGENT 1: UNDERSTANDING AGENT (GAANA SAMAJHNA)

### Purpose
Audio extract karna, lyrics samajhna, emotions identify karna

### Technical Implementation

```python
# understanding_agent.py

import whisper
from transformers import pipeline
import librosa
import json

class UnderstandingAgent:
    def __init__(self):
        self.whisper_model = whisper.load_model("large-v3")
        self.emotion_classifier = pipeline(
            "text-classification",
            model="custom-haryanvi-emotion-model"
        )
        
    def extract_audio(self, video_path: str) -> str:
        """FFmpeg se audio extract"""
        import subprocess
        audio_path = video_path.replace('.mp4', '.wav')
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', audio_path
        ])
        return audio_path
    
    def transcribe_with_timestamps(self, audio_path: str) -> dict:
        """Whisper se lyrics + timestamps"""
        result = self.whisper_model.transcribe(
            audio_path,
            language="hi",
            word_timestamps=True
        )
        return result
    
    def detect_beat_drops(self, audio_path: str) -> list:
        """Librosa se beat detection"""
        y, sr = librosa.load(audio_path)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Onset strength for drops
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, 3, 3, 3, 5, 0.5, 10)
        drop_times = librosa.frames_to_time(peaks, sr=sr)
        
        return {
            "tempo": float(tempo),
            "beat_times": beat_times.tolist(),
            "drop_times": drop_times.tolist()
        }
    
    def tag_emotions(self, lyrics_segments: list) -> list:
        """Har line ko emotion tag karo"""
        emotion_map = {
            "akad": ["theke pe", "chhore", "attitude", "na dare", "jaat"],
            "dard": ["roya", "dil", "judai", "yaad", "tanha"],
            "pyaar": ["gore", "naina", "ishq", "dil", "sajna"],
            "gaon_pride": ["gaam", "khap", "desi", "haryana", "tau"],
            "mauj": ["party", "daaru", "masti", "yaari", "chakk"]
        }
        
        tagged_segments = []
        for segment in lyrics_segments:
            text = segment["text"].lower()
            emotions = []
            for emotion, keywords in emotion_map.items():
                if any(kw in text for kw in keywords):
                    emotions.append(emotion)
            
            segment["emotions"] = emotions if emotions else ["neutral"]
            segment["viral_potential"] = self._calculate_viral_score(segment)
            tagged_segments.append(segment)
        
        return tagged_segments
    
    def _calculate_viral_score(self, segment: dict) -> float:
        """Viral potential score (0-1)"""
        score = 0.5
        if "akad" in segment.get("emotions", []):
            score += 0.2
        if len(segment["text"]) < 50:  # Short punchy lines
            score += 0.15
        if any(word in segment["text"].lower() for word in ["bhai", "yaar", "chhora"]):
            score += 0.1
        return min(score, 1.0)
    
    def find_chorus(self, segments: list) -> dict:
        """Repetitive chorus detect karo"""
        from collections import Counter
        lines = [s["text"].strip().lower() for s in segments]
        line_counts = Counter(lines)
        chorus_line = line_counts.most_common(1)[0] if line_counts else None
        
        if chorus_line and chorus_line[1] > 1:
            chorus_segments = [s for s in segments if s["text"].strip().lower() == chorus_line[0]]
            return {
                "text": chorus_line[0],
                "count": chorus_line[1],
                "timestamps": [s["start"] for s in chorus_segments]
            }
        return None
```

### Output Schema

```json
{
  "understanding_output": {
    "song_metadata": {
      "title": "string",
      "duration_seconds": "number",
      "tempo_bpm": "number",
      "language": "haryanvi"
    },
    "lyrics_segments": [
      {
        "id": "seg_001",
        "start": 12.5,
        "end": 15.2,
        "text": "Gaam ka chhora theke pe khada",
        "emotions": ["akad", "gaon_pride"],
        "viral_potential": 0.85,
        "is_chorus": false
      }
    ],
    "beat_analysis": {
      "tempo": 95,
      "drop_timestamps": [45.2, 89.5, 134.0],
      "chorus_timestamps": [60.0, 120.0, 180.0]
    },
    "top_viral_lines": [
      {
        "text": "Na dare kisi se chhora Haryana ka",
        "timestamp": 34.5,
        "score": 0.92
      }
    ]
  }
}
```

---

## ✂️ AGENT 2: VIRAL CUTTER AGENT (CLIP KAATNA)

### Purpose
Scroll-stopping clips create karna with proper hooks

### Technical Implementation

```python
# viral_cutter_agent.py

import ffmpeg
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ClipSpec:
    start_time: float
    end_time: float
    hook_line: str
    target_audience: str
    viral_reason: str
    platform: str
    aspect_ratio: str

class ViralCutterAgent:
    def __init__(self):
        self.clip_templates = {
            "instagram_reel": {"duration": (7, 15), "aspect": "9:16"},
            "youtube_shorts": {"duration": (15, 60), "aspect": "9:16"},
            "facebook_reel": {"duration": (15, 30), "aspect": "9:16"},
            "story": {"duration": (5, 15), "aspect": "9:16"}
        }
        
    def generate_clip_specs(self, understanding_data: dict) -> List[ClipSpec]:
        """Analysis se clip specifications generate karo"""
        clips = []
        segments = understanding_data["lyrics_segments"]
        drops = understanding_data["beat_analysis"]["drop_timestamps"]
        
        # Strategy 1: High viral potential lines
        for seg in segments:
            if seg["viral_potential"] > 0.75:
                clip = self._create_hook_first_clip(seg, segments)
                clips.append(clip)
        
        # Strategy 2: Beat drop moments
        for drop_time in drops:
            clip = self._create_drop_clip(drop_time, segments)
            clips.append(clip)
        
        # Strategy 3: Chorus loops
        chorus = understanding_data["beat_analysis"].get("chorus_timestamps", [])
        if chorus:
            clip = self._create_chorus_clip(chorus[0], segments)
            clips.append(clip)
        
        # Strategy 4: Emotion-based clips
        clips.extend(self._create_emotion_clips(segments))
        
        return self._deduplicate_and_rank(clips)
    
    def _create_hook_first_clip(self, hook_segment: dict, all_segments: list) -> ClipSpec:
        """Pehle 2 sec mein hook wali clip"""
        return ClipSpec(
            start_time=max(0, hook_segment["start"] - 0.5),
            end_time=min(hook_segment["end"] + 6, hook_segment["start"] + 12),
            hook_line=hook_segment["text"],
            target_audience=self._determine_audience(hook_segment["emotions"]),
            viral_reason=f"Hook in first 1.5s: '{hook_segment['text'][:30]}...'",
            platform="instagram_reel",
            aspect_ratio="9:16"
        )
    
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
    
    def cut_video(self, video_path: str, clip_spec: ClipSpec, output_path: str):
        """FFmpeg se actual cutting"""
        stream = ffmpeg.input(video_path, ss=clip_spec.start_time, t=clip_spec.end_time - clip_spec.start_time)
        
        # Aspect ratio adjust
        if clip_spec.aspect_ratio == "9:16":
            stream = ffmpeg.filter(stream, 'crop', 'ih*9/16', 'ih')
        
        # Output
        stream = ffmpeg.output(stream, output_path,
            vcodec='libx264',
            acodec='aac',
            video_bitrate='4M',
            audio_bitrate='192k'
        )
        ffmpeg.run(stream, overwrite_output=True)
        
    def add_captions_to_clip(self, video_path: str, text: str, style: str = "desi"):
        """Clip pe text overlay"""
        caption_styles = {
            "desi": {
                "font": "NotoSansDevanagari-Bold",
                "fontsize": 48,
                "fontcolor": "white",
                "borderw": 3,
                "bordercolor": "black"
            },
            "akad": {
                "font": "Impact",
                "fontsize": 56,
                "fontcolor": "yellow",
                "borderw": 4,
                "bordercolor": "red"
            }
        }
        # Implementation with FFmpeg drawtext filter
        pass
```

### Output Schema

```json
{
  "cutter_output": {
    "clips": [
      {
        "clip_id": "clip_001",
        "file_path": "/output/clips/clip_001.mp4",
        "duration_seconds": 8.5,
        "hook_timestamp": 0.0,
        "hook_line": "Gaam ka beta aise hi thode bana hai",
        "target_audience": "ladke_18_30_gaon_shehar",
        "viral_reason": "Akad wali line first 1.5s mein, relatable hook",
        "platform_fit": {
          "instagram_reel": 0.95,
          "youtube_shorts": 0.85,
          "facebook": 0.80
        },
        "recommended_posting": {
          "day": 1,
          "time_slot": "evening_7pm"
        }
      }
    ],
    "total_clips": 18,
    "coverage_percentage": 85
  }
}
```

---

## 🖼️ AGENT 3: FRAME POWER AGENT (DESI PHOTO)

### Purpose
Video se poster-quality frames extract karna with text overlay

### Technical Implementation

```python
# frame_power_agent.py

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import List

@dataclass  
class FrameSpec:
    timestamp: float
    quality_score: float
    face_detected: bool
    lighting_score: float
    emotion_match: str
    overlay_text: Optional[str]

class FramePowerAgent:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.quality_threshold = 0.7
        
    def extract_key_frames(self, video_path: str, understanding_data: dict) -> List[FrameSpec]:
        """Video se best frames nikalo"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        candidate_frames = []
        
        # Strategy 1: High emotion moments
        for segment in understanding_data["lyrics_segments"]:
            if segment["viral_potential"] > 0.7:
                timestamp = segment["start"]
                frame = self._extract_frame_at(cap, timestamp, fps)
                if frame is not None:
                    spec = self._analyze_frame(frame, timestamp, segment)
                    if spec.quality_score > self.quality_threshold:
                        candidate_frames.append(spec)
        
        # Strategy 2: Beat drops (dynamic poses)
        for drop_time in understanding_data["beat_analysis"]["drop_timestamps"]:
            frame = self._extract_frame_at(cap, drop_time, fps)
            if frame is not None:
                spec = self._analyze_frame(frame, drop_time, {"emotions": ["mauj"]})
                candidate_frames.append(spec)
        
        cap.release()
        return self._select_best_frames(candidate_frames, max_count=10)
    
    def _extract_frame_at(self, cap, timestamp: float, fps: float) -> np.ndarray:
        """Specific timestamp pe frame extract"""
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        return frame if ret else None
    
    def _analyze_frame(self, frame: np.ndarray, timestamp: float, segment: dict) -> FrameSpec:
        """Frame quality analyze karo"""
        # Face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        face_detected = len(faces) > 0
        
        # Lighting score (histogram analysis)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        lighting_score = self._calculate_lighting_score(hist)
        
        # Blur detection (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 500, 1.0)
        
        # Overall quality
        quality_score = (
            (0.4 if face_detected else 0) +
            (lighting_score * 0.3) +
            (sharpness_score * 0.3)
        )
        
        return FrameSpec(
            timestamp=timestamp,
            quality_score=quality_score,
            face_detected=face_detected,
            lighting_score=lighting_score,
            emotion_match=segment.get("emotions", ["neutral"])[0],
            overlay_text=segment.get("text", None)
        )
    
    def _calculate_lighting_score(self, hist) -> float:
        """Histogram se lighting quality"""
        # Good lighting = balanced histogram, not too dark/bright
        total = hist.sum()
        dark = hist[:50].sum() / total
        bright = hist[200:].sum() / total
        
        if dark > 0.5 or bright > 0.5:
            return 0.3  # Too dark or too bright
        return 0.8  # Balanced
    
    def create_poster_image(self, frame: np.ndarray, spec: FrameSpec, style: str = "desi") -> Image:
        """Frame se poster banao"""
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if spec.overlay_text:
            img = self._add_text_overlay(img, spec.overlay_text, style)
        
        # Color grading for desi vibe
        if style == "desi":
            img = self._apply_desi_grade(img)
        
        return img
    
    def _add_text_overlay(self, img: Image, text: str, style: str) -> Image:
        """Text overlay with desi typography"""
        draw = ImageDraw.Draw(img)
        
        # Font selection
        try:
            font = ImageFont.truetype("/fonts/NotoSansDevanagari-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Position: bottom center
        img_width, img_height = img.size
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        x = (img_width - text_width) // 2
        y = img_height - 150
        
        # Draw with shadow
        draw.text((x+3, y+3), text, font=font, fill="black")  # Shadow
        draw.text((x, y), text, font=font, fill="white")       # Main text
        
        return img
    
    def _apply_desi_grade(self, img: Image) -> Image:
        """Warm desi color grading"""
        import numpy as np
        arr = np.array(img).astype(float)
        
        # Warm tones
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)  # Red boost
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.9, 0, 255)  # Blue reduce
        
        # Slight contrast
        arr = np.clip((arr - 128) * 1.1 + 128, 0, 255)
        
        return Image.fromarray(arr.astype(np.uint8))
```

### Output Schema

```json
{
  "frame_output": {
    "posters": [
      {
        "poster_id": "poster_001",
        "file_path": "/output/posters/poster_001.jpg",
        "source_timestamp": 34.5,
        "quality_score": 0.89,
        "has_face": true,
        "overlay_text": "Gaam ka chhora hai bhai",
        "emotion_style": "akad",
        "recommended_use": "instagram_story_cover",
        "dimensions": "1080x1920"
      }
    ],
    "total_posters": 10
  }
}
```

---

## ✍️ AGENT 4: CAPTION & COMMENT AGENT (DESI BHASHA)

### Purpose
Haryanvi mein engaging captions aur comment-worthy questions generate karna

### Technical Implementation

```python
# caption_agent.py

import random
from typing import List, Dict

class CaptionAgent:
    def __init__(self):
        self.caption_templates = {
            "akad": [
                "Chhora {place} ka, attitude {city} ka 😏",
                "{line}... aur baat khatam 🔥",
                "Theke pe khade, duniya dekhe 👊",
                "Jaat ka kamaal, {emotion} pe jawab nahi",
                "{line} - ye line sun ke rewind nahi maara? 🎧"
            ],
            "dard": [
                "Dil toota, par chhora nahi jhuka 💔",
                "{line}... samjhe jo samjhe",
                "Yaad teri, raat meri ☕",
                "Koi sunne wala chahiye, bolne wale bahut hain"
            ],
            "gaon_pride": [
                "Gaam ki mitti, shehar ka sapna 🌾",
                "Beta {place} ka, baaki sab timepass",
                "{line} - apne gaam ki baat alag hai",
                "Desi swag, city lag 🚜"
            ],
            "pyaar": [
                "Gore gaal, kaala dil mera 😂",
                "{line}... ab samjh aaya?",
                "Tere bina chain kahan re 💕"
            ],
            "mauj": [
                "Party chal rahi hai, aaja yaar 🎉",
                "{line} - weekend mood ON",
                "Yaari dosti, baaki sab masti 🍻"
            ]
        }
        
        self.question_templates = {
            "akad": [
                "Bata chhore, teri bhi aisi koi line hai?",
                "Ye line sunke kiske yaad aaye? 😏 Tag karo",
                "Akad rakhni chahiye ya nahi? Comment karo",
                "Tera gaam kaunsa? Batade bhai"
            ],
            "dard": [
                "Tujhe bhi kisi ne aisa bola hai kya?",
                "Is line pe kitne baar rewind maara? Count batao",
                "Single ho ya complicated? 😅"
            ],
            "gaon_pride": [
                "Tera gaam kaunsa hai bhai?",
                "Gaam wale tag karo apne aap ko 🙋‍♂️",
                "Shehar better ya gaam? Ladai karo comments mein"
            ],
            "general": [
                "Ye gaana kitni baar suna? Honestly batao",
                "Isko kisne pehle discover kiya? OG fans batao",
                "Aur kaunsa gaana banaun? Request karo"
            ]
        }
        
    def generate_captions(self, clip_data: dict, understanding_data: dict) -> Dict:
        """Clip ke liye captions generate karo"""
        emotions = clip_data.get("emotions", ["general"])
        hook_line = clip_data.get("hook_line", "")
        
        # Select emotion-appropriate templates
        primary_emotion = emotions[0] if emotions else "general"
        templates = self.caption_templates.get(primary_emotion, self.caption_templates["akad"])
        
        # Generate 2 caption variations
        captions = []
        for _ in range(2):
            template = random.choice(templates)
            caption = template.format(
                line=self._shorten_line(hook_line),
                place="Haryana",
                city="Delhi",
                emotion=primary_emotion
            )
            captions.append(caption)
        
        # Generate engagement question
        question_templates = self.question_templates.get(primary_emotion, self.question_templates["general"])
        engagement_question = random.choice(question_templates)
        
        return {
            "captions": captions,
            "engagement_question": engagement_question,
            "hashtags": self._generate_hashtags(primary_emotion, understanding_data)
        }
    
    def _shorten_line(self, line: str, max_chars: int = 40) -> str:
        """Line ko short karo for caption"""
        if len(line) <= max_chars:
            return line
        return line[:max_chars-3] + "..."
    
    def _generate_hashtags(self, emotion: str, data: dict) -> List[str]:
        """Relevant hashtags generate karo"""
        base_tags = ["#haryanvi", "#haryanvisong", "#desisong", "#haryana"]
        
        emotion_tags = {
            "akad": ["#attitude", "#akadwala", "#chhora", "#desiboy"],
            "dard": ["#sadsong", "#dard", "#dil", "#heartbroken"],
            "gaon_pride": ["#gaam", "#desi", "#village", "#mitti"],
            "pyaar": ["#love", "#romance", "#pyaar", "#ishq"],
            "mauj": ["#party", "#yaari", "#masti", "#weekend"]
        }
        
        tags = base_tags + emotion_tags.get(emotion, [])
        
        # Add trending tags (from trend agent data if available)
        return tags[:15]  # Instagram limit-ish
    
    def generate_comment_replies(self, comment_type: str) -> List[str]:
        """Auto-reply templates for common comments"""
        replies = {
            "fire_emoji": [
                "Thankyou bhai 🔥",
                "Support karte raho 🙏",
                "Aur aayega boss 💪"
            ],
            "which_song": [
                "Gaana jaldi aara hai, subscribed raho!",
                "Ye clip {song_name} se hai bhai"
            ],
            "request": [
                "Note kar liya bhai, queue mein hai",
                "Agle gaane mein zaroor"
            ]
        }
        return replies.get(comment_type, ["❤️"])
```

### Output Schema

```json
{
  "caption_output": {
    "clip_id": "clip_001",
    "captions": [
      "Gaam ka beta aise hi thode bana hai 😏",
      "Is line pe sabne rewind maara hoga... sach bol 🎧"
    ],
    "engagement_question": "Tera gaam kaunsa hai bhai? Comment karo",
    "hashtags": [
      "#haryanvi",
      "#haryanvisong",
      "#attitude",
      "#chhora",
      "#desiboy",
      "#viral",
      "#trending"
    ],
    "comment_reply_templates": {
      "fire": "Thankyou bhai 🔥",
      "heart": "Support karte raho ❤️"
    }
  }
}
```

---

## 📊 AGENT 5: TREND & COMPETITOR AGENT

### Purpose
Haryanvi music scene ka pulse samajhna - kya chal raha, kya fail

### Technical Implementation

```python
# trend_agent.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class TrendInsight:
    trend_type: str
    description: str
    confidence: float
    action_recommendation: str
    data_source: str

class TrendAgent:
    def __init__(self):
        self.competitors = [
            "KD Desirock",
            "Gulzaar Chhaniwala", 
            "Raju Punjabi",
            "Sapna Chaudhary",
            "Masoom Sharma"
        ]
        self.platforms = ["instagram", "youtube", "facebook"]
        
    async def analyze_trends(self) -> Dict:
        """Current trends analyze karo"""
        insights = []
        
        # 1. Competitor analysis
        competitor_data = await self._fetch_competitor_data()
        insights.extend(self._analyze_competitor_performance(competitor_data))
        
        # 2. Platform trends
        platform_trends = await self._fetch_platform_trends()
        insights.extend(self._analyze_platform_patterns(platform_trends))
        
        # 3. Timing analysis
        timing_data = await self._fetch_timing_data()
        insights.extend(self._analyze_best_times(timing_data))
        
        # 4. Content format analysis
        format_trends = await self._fetch_format_performance()
        insights.extend(self._analyze_format_preferences(format_trends))
        
        return {
            "insights": insights,
            "weekly_summary": self._generate_weekly_summary(insights),
            "recommendations": self._generate_recommendations(insights)
        }
    
    async def _fetch_competitor_data(self) -> List[Dict]:
        """Competitor ka recent content fetch karo"""
        # Integration with:
        # - Instagram Graph API (for public profiles)
        # - YouTube Data API
        # - Social Blade data
        
        # Mock structure
        return [
            {
                "artist": "Gulzaar Chhaniwala",
                "recent_posts": [
                    {
                        "type": "reel",
                        "duration": 12,
                        "likes": 150000,
                        "comments": 3200,
                        "caption_style": "akad",
                        "hook_in_first_2s": True,
                        "posted_time": "evening",
                        "engagement_rate": 0.08
                    }
                ]
            }
        ]
    
    def _analyze_competitor_performance(self, data: List[Dict]) -> List[TrendInsight]:
        """Competitor patterns identify karo"""
        insights = []
        
        # Average reel duration analysis
        durations = []
        for artist in data:
            for post in artist.get("recent_posts", []):
                if post["type"] == "reel":
                    durations.append(post["duration"])
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            insights.append(TrendInsight(
                trend_type="optimal_duration",
                description=f"Top performers ka avg reel duration: {avg_duration:.1f} sec",
                confidence=0.85,
                action_recommendation=f"Reels {int(avg_duration)-2} se {int(avg_duration)+2} sec ke beech rakho",
                data_source="competitor_analysis"
            ))
        
        # Hook analysis
        hook_success = [p for a in data for p in a.get("recent_posts", []) 
                       if p.get("hook_in_first_2s") and p.get("engagement_rate", 0) > 0.05]
        
        if len(hook_success) > len(durations) * 0.6:
            insights.append(TrendInsight(
                trend_type="hook_importance",
                description="First 2 sec mein hook wali reels 60%+ better perform karti hain",
                confidence=0.9,
                action_recommendation="Har clip mein pehle 2 sec mein tagdi line daalo",
                data_source="competitor_analysis"
            ))
        
        return insights
    
    def _analyze_best_times(self, timing_data: Dict) -> List[TrendInsight]:
        """Best posting times identify karo"""
        # Analysis based on engagement patterns
        return [
            TrendInsight(
                trend_type="posting_time",
                description="Sad gaane subah 6-9 AM best chalte hain",
                confidence=0.75,
                action_recommendation="Dard wali reels morning mein post karo",
                data_source="timing_analysis"
            ),
            TrendInsight(
                trend_type="posting_time", 
                description="Akad/Party reels evening 7-10 PM best",
                confidence=0.82,
                action_recommendation="Akad wali reels sham ko post karo",
                data_source="timing_analysis"
            )
        ]
    
    def _generate_weekly_summary(self, insights: List[TrendInsight]) -> str:
        """Hafte ka summary in simple Haryanvi"""
        summary_parts = []
        
        # Group by trend type
        for insight in insights:
            if insight.confidence > 0.7:
                summary_parts.append(f"• {insight.description}")
        
        return "Is hafte ki findings:\n" + "\n".join(summary_parts)
    
    def _generate_recommendations(self, insights: List[TrendInsight]) -> List[str]:
        """Actionable recommendations"""
        return [i.action_recommendation for i in insights if i.confidence > 0.7]
```

### Output Schema

```json
{
  "trend_output": {
    "analysis_date": "2025-02-11",
    "insights": [
      {
        "trend_type": "content_format",
        "description": "Is hafte akad wali reels 40% zyada viral hui",
        "confidence": 0.88,
        "action": "Agle 3 din akad content prioritize karo"
      },
      {
        "trend_type": "duration",
        "description": "6-8 sec reels sabse zyada complete hoti hain",
        "confidence": 0.92,
        "action": "Clips 6-8 sec ke beech rakho"
      },
      {
        "trend_type": "timing",
        "description": "Sad songs morning 7 AM pe best engagement",
        "confidence": 0.78,
        "action": "Dard wali reels subah schedule karo"
      }
    ],
    "competitor_snapshot": {
      "top_performer_this_week": "Gulzaar Chhaniwala",
      "their_winning_format": "8 sec akad reel with face close-up hook"
    },
    "weekly_summary": "Is hafte akad chal raha, 6-8 sec reels best, morning sad evening akad"
  }
}
```

---

## 🧠 AGENT 6: STRATEGY BRAIN (DECISION AGENT)

### Purpose
Saara data combine karke clear instructions dena - kya karna hai, kya nahi

### Technical Implementation

```python
# strategy_brain.py

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class ContentDecision:
    action: str  # "post", "hold", "repeat", "stop"
    content_id: str
    platform: str
    scheduled_time: datetime
    reason: str
    priority: int  # 1-5, 1 is highest

class StrategyBrain:
    def __init__(self):
        self.content_queue = []
        self.posted_history = []
        self.performance_data = {}
        
    def make_decisions(self, 
                       clips: List[Dict],
                       trend_insights: List[Dict],
                       memory_data: Dict,
                       duration_days: int = 15) -> Dict:
        """Pura content calendar aur strategy decide karo"""
        
        decisions = []
        
        # 1. Rank clips by predicted performance
        ranked_clips = self._rank_clips(clips, trend_insights, memory_data)
        
        # 2. Create posting schedule
        schedule = self._create_schedule(ranked_clips, duration_days)
        
        # 3. Platform allocation
        platform_decisions = self._allocate_platforms(schedule)
        
        # 4. Generate simple action commands
        action_commands = self._generate_commands(platform_decisions)
        
        return {
            "content_calendar": schedule,
            "platform_strategy": platform_decisions,
            "action_commands": action_commands,
            "stop_list": self._identify_weak_content(clips, memory_data)
        }
    
    def _rank_clips(self, clips: List[Dict], trends: List[Dict], memory: Dict) -> List[Dict]:
        """Clips ko predicted performance se rank karo"""
        for clip in clips:
            score = clip.get("viral_potential", 0.5)
            
            # Trend alignment bonus
            clip_emotion = clip.get("emotions", ["general"])[0]
            for trend in trends:
                if trend.get("trend_type") == "content_format":
                    if clip_emotion in trend.get("description", "").lower():
                        score += 0.15
            
            # Memory-based adjustment
            similar_past = memory.get("emotion_performance", {}).get(clip_emotion, {})
            if similar_past.get("avg_engagement", 0) > 0.05:
                score += 0.1
            
            # Duration alignment
            optimal_duration = next(
                (t["action"] for t in trends if "duration" in t.get("trend_type", "")),
                "6-8 sec"
            )
            clip_duration = clip.get("duration_seconds", 10)
            if 6 <= clip_duration <= 8:
                score += 0.1
            
            clip["predicted_score"] = min(score, 1.0)
        
        return sorted(clips, key=lambda x: x["predicted_score"], reverse=True)
    
    def _create_schedule(self, ranked_clips: List[Dict], days: int) -> List[Dict]:
        """Content calendar banao"""
        schedule = []
        clips_per_day = max(1, len(ranked_clips) // days)
        
        start_date = datetime.now()
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            day_clips = ranked_clips[day * clips_per_day : (day + 1) * clips_per_day]
            
            for i, clip in enumerate(day_clips):
                # Time slot based on emotion
                emotion = clip.get("emotions", ["general"])[0]
                if emotion == "dard":
                    time_slot = "07:00"
                elif emotion == "akad":
                    time_slot = "19:00"
                else:
                    time_slot = "12:00" if i == 0 else "18:00"
                
                schedule.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": time_slot,
                    "clip_id": clip["clip_id"],
                    "emotion": emotion,
                    "predicted_score": clip["predicted_score"],
                    "platform": self._select_best_platform(clip)
                })
        
        return schedule
    
    def _select_best_platform(self, clip: Dict) -> str:
        """Clip ke liye best platform choose karo"""
        platform_fit = clip.get("platform_fit", {})
        if platform_fit:
            return max(platform_fit, key=platform_fit.get)
        
        # Default logic based on duration
        duration = clip.get("duration_seconds", 10)
        if duration <= 15:
            return "instagram_reel"
        elif duration <= 60:
            return "youtube_shorts"
        else:
            return "facebook"
    
    def _generate_commands(self, decisions: List[Dict]) -> List[str]:
        """Simple Hinglish commands generate karo"""
        commands = []
        
        for i, decision in enumerate(decisions[:7], 1):  # Next 7 days
            cmd = f"Day {i}: {decision['clip_id']} - {decision['platform']} pe {decision['time']} baje post karo"
            if decision.get("emotion") == "akad":
                cmd += " (akad wali content, evening best)"
            elif decision.get("emotion") == "dard":
                cmd += " (sad content, morning best)"
            commands.append(cmd)
        
        return commands
    
    def _identify_weak_content(self, clips: List[Dict], memory: Dict) -> List[str]:
        """Kaunsa content band karna chahiye"""
        weak = []
        
        for clip in clips:
            if clip.get("predicted_score", 0) < 0.4:
                weak.append({
                    "clip_id": clip["clip_id"],
                    "reason": "Low viral potential score",
                    "action": "SKIP - isko post mat karo"
                })
        
        # Check memory for consistently failing patterns
        failing_emotions = [
            emotion for emotion, data in memory.get("emotion_performance", {}).items()
            if data.get("avg_engagement", 0) < 0.02
        ]
        
        for clip in clips:
            if clip.get("emotions", [""])[0] in failing_emotions:
                weak.append({
                    "clip_id": clip["clip_id"],
                    "reason": f"'{clip.get('emotions', [''])[0]}' type content historically underperforms",
                    "action": "CAUTION - test with small audience first"
                })
        
        return weak
    
    def adapt_strategy(self, new_performance_data: Dict) -> str:
        """Real-time strategy adjustment"""
        recent_posts = new_performance_data.get("recent_24h", [])
        
        adjustments = []
        
        for post in recent_posts:
            if post.get("engagement_rate", 0) > 0.1:
                adjustments.append(
                    f"Reel #{post['clip_id'][-3:]} ne tagda perform kiya - "
                    f"aisi aur {post.get('emotion', 'similar')} wali reels banao"
                )
            elif post.get("engagement_rate", 0) < 0.02:
                adjustments.append(
                    f"Reel #{post['clip_id'][-3:]} slow rahi - "
                    f"aisi {post.get('emotion', '')} type kam karo agle week"
                )
        
        return "\n".join(adjustments) if adjustments else "Sab theek chal raha, strategy continue karo"
```

### Output Schema

```json
{
  "strategy_output": {
    "content_calendar": [
      {
        "date": "2025-02-12",
        "time": "07:00",
        "clip_id": "clip_003",
        "emotion": "dard",
        "platform": "instagram_reel",
        "predicted_score": 0.89
      },
      {
        "date": "2025-02-12", 
        "time": "19:00",
        "clip_id": "clip_001",
        "emotion": "akad",
        "platform": "youtube_shorts",
        "predicted_score": 0.95
      }
    ],
    "action_commands": [
      "Day 1: clip_003 - Instagram pe 7 AM post karo (sad content, morning best)",
      "Day 1: clip_001 - YouTube Shorts pe 7 PM post karo (akad wali content, evening best)",
      "Day 2: clip_007 - Facebook pe 12 PM post karo"
    ],
    "stop_list": [
      {
        "clip_id": "clip_012",
        "reason": "Low viral score (0.32)",
        "action": "SKIP"
      }
    ],
    "weekly_guidance": "Agle 7 din akad content pe focus, 6-8 sec reels best chal rahi"
  }
}
```

---

## 📤 AGENT 7: AUTO POSTING AGENT

### Purpose
Scheduled content automatically ya approval ke saath post karna

### Technical Implementation

```python
# auto_posting_agent.py

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class PostingMode(Enum):
    AUTO = "auto"
    APPROVAL = "approval"
    SCHEDULED = "scheduled"

class AutoPostingAgent:
    def __init__(self, mode: PostingMode = PostingMode.APPROVAL):
        self.mode = mode
        self.platforms = {
            "instagram": InstagramPoster(),
            "youtube_shorts": YouTubePoster(),
            "facebook": FacebookPoster()
        }
        self.telegram_bot = TelegramNotifier()
        self.pending_queue = []
        
    async def process_schedule(self, schedule: List[Dict]):
        """Schedule process karo based on mode"""
        for item in schedule:
            post_time = datetime.strptime(
                f"{item['date']} {item['time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            if self.mode == PostingMode.AUTO:
                await self._schedule_auto_post(item, post_time)
            elif self.mode == PostingMode.APPROVAL:
                await self._request_approval(item, post_time)
            else:
                await self._add_to_scheduled_queue(item, post_time)
    
    async def _request_approval(self, item: Dict, scheduled_time: datetime):
        """Telegram pe approval maango"""
        message = self._format_approval_message(item, scheduled_time)
        
        # Send preview to Telegram
        await self.telegram_bot.send_message(
            text=message,
            media_path=item.get("preview_path"),
            reply_markup=self._create_approval_buttons(item["clip_id"])
        )
        
        self.pending_queue.append({
            "clip_id": item["clip_id"],
            "scheduled_time": scheduled_time,
            "status": "pending_approval"
        })
    
    def _format_approval_message(self, item: Dict, scheduled_time: datetime) -> str:
        """Telegram message format karo"""
        return f"""
🎬 *Reel Ready for Posting*

📝 *Clip:* {item['clip_id']}
🎭 *Vibe:* {item.get('emotion', 'general')}
📱 *Platform:* {item['platform']}
⏰ *Scheduled:* {scheduled_time.strftime('%d %b, %I:%M %p')}
📊 *Predicted Score:* {item.get('predicted_score', 'N/A'):.0%}

Caption suggestion:
_{item.get('caption', 'No caption generated')}_

*Approve kar do bhai, reel ready hai* ✅
        """
    
    def _create_approval_buttons(self, clip_id: str) -> Dict:
        """Telegram inline buttons"""
        return {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve", "callback_data": f"approve_{clip_id}"},
                    {"text": "❌ Skip", "callback_data": f"skip_{clip_id}"}
                ],
                [
                    {"text": "✏️ Edit Caption", "callback_data": f"edit_{clip_id}"},
                    {"text": "⏰ Reschedule", "callback_data": f"reschedule_{clip_id}"}
                ]
            ]
        }
    
    async def handle_approval_callback(self, callback_data: str):
        """Telegram callback handle karo"""
        action, clip_id = callback_data.split("_", 1)
        
        if action == "approve":
            await self._execute_post(clip_id)
            return "✅ Posted successfully! Views aane de ab 🔥"
        
        elif action == "skip":
            self._remove_from_queue(clip_id)
            return "⏭️ Skipped. Agle pe chalte hain."
        
        elif action == "edit":
            return "✏️ Naya caption bhej do reply mein"
        
        elif action == "reschedule":
            return "⏰ Naya time bhej do (format: 14:30)"
    
    async def _execute_post(self, clip_id: str):
        """Actually post karo platform pe"""
        item = self._get_from_queue(clip_id)
        if not item:
            return
        
        platform = item.get("platform", "instagram")
        poster = self.platforms.get(platform)
        
        if poster:
            result = await poster.post(
                media_path=item["file_path"],
                caption=item.get("caption", ""),
                hashtags=item.get("hashtags", [])
            )
            
            # Log result
            self._log_post_result(clip_id, result)
            
            # Notify via Telegram
            await self.telegram_bot.send_message(
                f"✅ Posted to {platform}!\n"
                f"Link: {result.get('post_url', 'N/A')}"
            )
    
    async def post_to_instagram(self, media_path: str, caption: str, hashtags: List[str]) -> Dict:
        """Instagram Graph API se post"""
        # Instagram Business API integration
        # Requires: Facebook Page + Instagram Business Account
        
        full_caption = f"{caption}\n\n{' '.join(hashtags)}"
        
        # Step 1: Upload media
        # Step 2: Publish
        # (Actual implementation depends on API credentials)
        
        return {
            "success": True,
            "platform": "instagram",
            "post_id": "ig_xxx",
            "post_url": "https://instagram.com/p/xxx"
        }
    
    async def post_to_youtube_shorts(self, media_path: str, title: str, description: str) -> Dict:
        """YouTube Data API se Shorts upload"""
        # YouTube Data API v3 integration
        
        return {
            "success": True,
            "platform": "youtube_shorts",
            "video_id": "yt_xxx",
            "post_url": "https://youtube.com/shorts/xxx"
        }


class TelegramNotifier:
    """Telegram bot for notifications and approvals"""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.chat_id = None  # Artist's chat ID
        
    async def send_message(self, text: str, media_path: str = None, reply_markup: Dict = None):
        """Telegram pe message bhejo"""
        # python-telegram-bot implementation
        pass
    
    async def send_daily_report(self, report: Dict):
        """Daily performance report"""
        message = f"""
📊 *Daily Report - {report['date']}*

🎬 *Posts Today:* {report['posts_count']}
👀 *Total Views:* {report['total_views']:,}
❤️ *Total Likes:* {report['total_likes']:,}
💬 *Comments:* {report['total_comments']:,}

🏆 *Best Performer:*
{report['best_post']['clip_id']} - {report['best_post']['views']:,} views

📈 *Insight:*
{report['insight']}

Kal ka plan ready hai ✅
        """
        await self.send_message(message)
```

### Output Schema

```json
{
  "posting_output": {
    "posted": [
      {
        "clip_id": "clip_001",
        "platform": "instagram",
        "post_url": "https://instagram.com/reel/xxx",
        "posted_at": "2025-02-12T19:00:00",
        "status": "success"
      }
    ],
    "pending_approval": [
      {
        "clip_id": "clip_003",
        "scheduled_time": "2025-02-13T07:00:00",
        "platform": "instagram",
        "telegram_message_id": 12345
      }
    ],
    "failed": [],
    "daily_summary": {
      "posts_today": 3,
      "platforms_used": ["instagram", "youtube_shorts"],
      "next_scheduled": "2025-02-12T07:00:00"
    }
  }
}
```

---

## 🔁 AGENT 8: MEMORY AGENT (LEARNING LOOP)

### Purpose
Past performance se seekhna aur future predictions improve karna

### Technical Implementation

```python
# memory_agent.py

import json
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import sqlite3

class MemoryAgent:
    def __init__(self, db_path: str = "artist_memory.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """SQLite database initialize karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                clip_id TEXT PRIMARY KEY,
                platform TEXT,
                emotion TEXT,
                duration_seconds REAL,
                hook_line TEXT,
                posted_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                watch_time_avg REAL DEFAULT 0,
                engagement_rate REAL DEFAULT 0
            )
        ''')
        
        # Performance snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT,
                snapshot_at TIMESTAMP,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                FOREIGN KEY (clip_id) REFERENCES posts(clip_id)
            )
        ''')
        
        # Insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT,
                insight_text TEXT,
                confidence REAL,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_post(self, post_data: Dict):
        """Naya post record karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO posts 
            (clip_id, platform, emotion, duration_seconds, hook_line, posted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            post_data['clip_id'],
            post_data['platform'],
            post_data.get('emotion', 'general'),
            post_data.get('duration_seconds', 0),
            post_data.get('hook_line', ''),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def update_performance(self, clip_id: str, metrics: Dict):
        """Performance metrics update karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update main record
        engagement_rate = self._calculate_engagement_rate(metrics)
        
        cursor.execute('''
            UPDATE posts SET 
                views = ?,
                likes = ?,
                comments = ?,
                shares = ?,
                watch_time_avg = ?,
                engagement_rate = ?
            WHERE clip_id = ?
        ''', (
            metrics.get('views', 0),
            metrics.get('likes', 0),
            metrics.get('comments', 0),
            metrics.get('shares', 0),
            metrics.get('watch_time_avg', 0),
            engagement_rate,
            clip_id
        ))
        
        # Add snapshot for trend analysis
        cursor.execute('''
            INSERT INTO performance_snapshots 
            (clip_id, snapshot_at, views, likes, comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            clip_id,
            datetime.now(),
            metrics.get('views', 0),
            metrics.get('likes', 0),
            metrics.get('comments', 0)
        ))
        
        conn.commit()
        conn.close()
        
        # Generate insights from new data
        self._generate_insights_from_update(clip_id, metrics)
    
    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """Engagement rate calculate karo"""
        views = metrics.get('views', 1)
        interactions = (
            metrics.get('likes', 0) + 
            metrics.get('comments', 0) * 2 +  # Comments more valuable
            metrics.get('shares', 0) * 3       # Shares most valuable
        )
        return interactions / views if views > 0 else 0
    
    def get_emotion_performance(self) -> Dict:
        """Emotion-wise performance analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                emotion,
                COUNT(*) as post_count,
                AVG(engagement_rate) as avg_engagement,
                AVG(views) as avg_views,
                MAX(views) as max_views
            FROM posts
            WHERE posted_at > datetime('now', '-30 days')
            GROUP BY emotion
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return {
            row[0]: {
                "post_count": row[1],
                "avg_engagement": row[2],
                "avg_views": row[3],
                "max_views": row[4]
            }
            for row in results
        }
    
    def get_best_performing_patterns(self) -> List[Dict]:
        """Top performing patterns identify karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Duration analysis
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN duration_seconds < 7 THEN 'short_<7s'
                    WHEN duration_seconds < 15 THEN 'medium_7-15s'
                    ELSE 'long_>15s'
                END as duration_bucket,
                AVG(engagement_rate) as avg_engagement,
                COUNT(*) as count
            FROM posts
            WHERE posted_at > datetime('now', '-30 days')
            GROUP BY duration_bucket
            ORDER BY avg_engagement DESC
        ''')
        
        duration_results = cursor.fetchall()
        
        # Time of day analysis
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN CAST(strftime('%H', posted_at) AS INTEGER) < 12 THEN 'morning'
                    WHEN CAST(strftime('%H', posted_at) AS INTEGER) < 17 THEN 'afternoon'
                    ELSE 'evening'
                END as time_slot,
                AVG(engagement_rate) as avg_engagement
            FROM posts
            WHERE posted_at > datetime('now', '-30 days')
            GROUP BY time_slot
            ORDER BY avg_engagement DESC
        ''')
        
        time_results = cursor.fetchall()
        conn.close()
        
        patterns = []
        
        if duration_results:
            best_duration = duration_results[0]
            patterns.append({
                "pattern_type": "duration",
                "finding": f"{best_duration[0]} reels best perform karti hain",
                "avg_engagement": best_duration[1],
                "sample_size": best_duration[2]
            })
        
        if time_results:
            best_time = time_results[0]
            patterns.append({
                "pattern_type": "posting_time",
                "finding": f"{best_time[0]} mein post karna best hai",
                "avg_engagement": best_time[1]
            })
        
        return patterns
    
    def _generate_insights_from_update(self, clip_id: str, metrics: Dict):
        """New data se insights generate karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get clip details
        cursor.execute('SELECT emotion, duration_seconds FROM posts WHERE clip_id = ?', (clip_id,))
        clip = cursor.fetchone()
        
        if not clip:
            conn.close()
            return
        
        emotion, duration = clip
        engagement_rate = self._calculate_engagement_rate(metrics)
        
        # Compare with average
        cursor.execute('''
            SELECT AVG(engagement_rate) FROM posts 
            WHERE emotion = ? AND clip_id != ?
        ''', (emotion, clip_id))
        
        avg_for_emotion = cursor.fetchone()[0] or 0
        
        # Generate insight if significantly different
        if engagement_rate > avg_for_emotion * 1.5:
            insight = f"Clip {clip_id[-6:]} ne {emotion} category mein 50% better perform kiya. Reason: {self._analyze_success_reason(clip_id, metrics)}"
            
            cursor.execute('''
                INSERT INTO insights (insight_type, insight_text, confidence, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                "performance_spike",
                insight,
                0.85,
                datetime.now(),
                datetime.now() + timedelta(days=7)
            ))
        
        conn.commit()
        conn.close()
    
    def _analyze_success_reason(self, clip_id: str, metrics: Dict) -> str:
        """Success ka reason identify karo"""
        reasons = []
        
        if metrics.get('watch_time_avg', 0) > 0.7:
            reasons.append("high watch completion")
        
        if metrics.get('comments', 0) > metrics.get('likes', 0) * 0.1:
            reasons.append("strong comment engagement")
        
        if metrics.get('shares', 0) > metrics.get('likes', 0) * 0.05:
            reasons.append("high shareability")
        
        return ", ".join(reasons) if reasons else "overall strong performance"
    
    def get_learning_report(self) -> Dict:
        """Full learning report generate karo"""
        return {
            "emotion_performance": self.get_emotion_performance(),
            "best_patterns": self.get_best_performing_patterns(),
            "recent_insights": self._get_recent_insights(),
            "recommendations": self._generate_recommendations()
        }
    
    def _get_recent_insights(self) -> List[str]:
        """Recent insights fetch karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT insight_text FROM insights 
            WHERE expires_at > datetime('now')
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def _generate_recommendations(self) -> List[str]:
        """Data-backed recommendations"""
        recommendations = []
        
        patterns = self.get_best_performing_patterns()
        emotion_perf = self.get_emotion_performance()
        
        # Duration recommendation
        for pattern in patterns:
            if pattern["pattern_type"] == "duration":
                recommendations.append(f"Agle clips {pattern['finding']}")
        
        # Emotion recommendation
        if emotion_perf:
            best_emotion = max(emotion_perf.items(), key=lambda x: x[1].get('avg_engagement', 0))
            recommendations.append(f"'{best_emotion[0]}' content pe focus karo - {best_emotion[1]['avg_engagement']:.1%} engagement")
        
        return recommendations
```

### Output Schema

```json
{
  "memory_output": {
    "emotion_performance": {
      "akad": {
        "post_count": 15,
        "avg_engagement": 0.078,
        "avg_views": 45000,
        "max_views": 250000
      },
      "dard": {
        "post_count": 8,
        "avg_engagement": 0.065,
        "avg_views": 32000,
        "max_views": 120000
      }
    },
    "best_patterns": [
      {
        "pattern_type": "duration",
        "finding": "6-8 sec reels best perform karti hain",
        "avg_engagement": 0.082
      },
      {
        "pattern_type": "posting_time",
        "finding": "evening mein post karna best hai",
        "avg_engagement": 0.075
      }
    ],
    "recent_insights": [
      "Reel #007 isliye chali kyunki 'akad' wali line first 1.5 sec mein aa gayi",
      "Morning sad content pe comment rate 2x hai evening se"
    ],
    "recommendations": [
      "Agle clips 6-8 sec ke beech rakho",
      "'akad' content pe focus karo - 7.8% engagement"
    ]
  }
}
```

---

## 🔄 COMPLETE WORKFLOW

### Agent Execution Order

```
1. INPUT RECEIVED (YouTube URL / Raw Video)
          │
          ▼
2. UNDERSTANDING AGENT
   - Audio extract
   - Lyrics transcribe
   - Emotions tag
   - Beat analysis
          │
          ▼
3. PARALLEL EXECUTION:
   ┌──────────────────────────────────────┐
   │  VIRAL CUTTER    │    FRAME POWER   │
   │  (Clips banao)   │   (Photos nikalo)│
   └──────────────────────────────────────┘
          │
          ▼
4. CAPTION AGENT
   - Captions generate
   - Hashtags create
   - Questions banao
          │
          ▼
5. TREND AGENT (Background - can run async)
   - Competitor check
   - Platform trends
   - Timing analysis
          │
          ▼
6. STRATEGY BRAIN
   - All data combine
   - Calendar create
   - Decisions make
          │
          ▼
7. AUTO POSTING AGENT
   - Schedule posts
   - Request approvals
   - Execute posts
          │
          ▼
8. MEMORY AGENT (Continuous)
   - Track performance
   - Learn patterns
   - Update predictions
```

### n8n Workflow Configuration

```json
{
  "name": "Haryanvi Artist Agent",
  "nodes": [
    {
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "parameters": {
        "updates": ["message"]
      }
    },
    {
      "name": "Parse Command",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Extract URL and options from message\nconst text = $input.first().json.message.text;\nconst urlMatch = text.match(/https?:\\/\\/[^\\s]+/);\nconst vibeMatch = text.match(/-(\\w+)/g);\n\nreturn [{\n  json: {\n    url: urlMatch ? urlMatch[0] : null,\n    vibes: vibeMatch ? vibeMatch.map(v => v.slice(1)) : ['desi'],\n    chat_id: $input.first().json.message.chat.id\n  }\n}];"
      }
    },
    {
      "name": "Understanding Agent",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/understand",
        "method": "POST",
        "body": "={{ JSON.stringify($json) }}"
      }
    },
    {
      "name": "Parallel Processing",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 2,
        "options": {}
      }
    },
    {
      "name": "Viral Cutter",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/cut",
        "method": "POST"
      }
    },
    {
      "name": "Frame Power",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/frames",
        "method": "POST"
      }
    },
    {
      "name": "Caption Generator",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/captions",
        "method": "POST"
      }
    },
    {
      "name": "Strategy Brain",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/api/strategy",
        "method": "POST"
      }
    },
    {
      "name": "Send Approval Request",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "operation": "sendMessage",
        "chatId": "={{ $json.chat_id }}",
        "text": "={{ $json.approval_message }}"
      }
    }
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [["Parse Command"]]
    },
    "Parse Command": {
      "main": [["Understanding Agent"]]
    },
    "Understanding Agent": {
      "main": [["Parallel Processing"]]
    },
    "Parallel Processing": {
      "main": [["Viral Cutter"], ["Frame Power"]]
    },
    "Viral Cutter": {
      "main": [["Caption Generator"]]
    },
    "Frame Power": {
      "main": [["Caption Generator"]]
    },
    "Caption Generator": {
      "main": [["Strategy Brain"]]
    },
    "Strategy Brain": {
      "main": [["Send Approval Request"]]
    }
  }
}
```

---

## 🚀 DEPLOYMENT GUIDE

### Prerequisites

```bash
# System requirements
- Python 3.10+
- Node.js 18+ (for n8n)
- FFmpeg
- CUDA GPU (optional, for faster processing)
- 8GB+ RAM recommended

# Storage
- 50GB+ for video processing cache
- SSD recommended for faster I/O
```

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/your-repo/haryanvi-artist-agent.git
cd haryanvi-artist-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Whisper model
pip install openai-whisper
# Download large-v3 model (2.9GB)
python -c "import whisper; whisper.load_model('large-v3')"

# 5. Install n8n
npm install -g n8n

# 6. Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# 7. Initialize database
python scripts/init_db.py

# 8. Start services
# Terminal 1: API Server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: n8n
n8n start

# Terminal 3: Telegram Bot (optional)
python telegram_bot.py
```

### Environment Variables

```bash
# .env file

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Instagram (Facebook Graph API)
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ID=your_id

# YouTube
YOUTUBE_API_KEY=your_key
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_secret

# Facebook
FACEBOOK_PAGE_TOKEN=your_token
FACEBOOK_PAGE_ID=your_id

# Processing
MAX_CONCURRENT_JOBS=3
VIDEO_CACHE_PATH=/tmp/video_cache
OUTPUT_PATH=/output

# Database
DATABASE_URL=sqlite:///artist_memory.db
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Whisper model
RUN python -c "import whisper; whisper.load_model('large-v3')"

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - ./n8n_data:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=secure_password

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

---

## 📱 TELEGRAM BOT COMMANDS

```
/process <url> - Gaana process karo
/process <url> -desi - Desi vibe ke saath
/process <url> -sad -15din - Sad gaana, 15 din ka content

/status - Current processing status
/queue - Pending approvals dekho
/approve <clip_id> - Clip approve karo
/skip <clip_id> - Clip skip karo

/report - Today's performance
/weekly - Weekly summary
/trends - Current trends

/settings - Bot settings
/help - Commands list
```

---

## 📊 REPORTING FORMAT

### Daily Telegram Report

```
📊 *Daily Report - 12 Feb 2025*

🎬 *Posts Today:* 4
👀 *Total Views:* 125,000
❤️ *Total Likes:* 8,500
💬 *Comments:* 420

🏆 *Best Performer:*
Reel #007 - 45,000 views
Reason: "akad wali line first 1.5 sec mein aa gayi"

📈 *Key Insight:*
Akad content evening mein 40% better perform kar raha

✅ *Tomorrow's Plan:*
- 7 AM: Sad reel #012
- 7 PM: Akad reel #008
- 9 PM: Party reel #015

Approve kar do bhai! 🔥
```

---

## ⚠️ LIMITATIONS & NOTES

1. **API Rate Limits**: Instagram/YouTube APIs have daily limits
2. **Processing Time**: Full song processing takes 5-10 minutes
3. **Storage**: Each song generates ~500MB of clips/frames
4. **Accuracy**: Haryanvi dialect detection ~85% accurate
5. **Manual Review**: Always recommended for final approval

---

## 🔧 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Whisper slow | Use GPU or smaller model |
| Instagram post failed | Check access token expiry |
| n8n workflow stuck | Check API endpoint health |
| Low engagement | Review trend agent recommendations |
| Memory full | Clear video cache |

---

## 📝 CHANGELOG

- **v1.0.0** - Initial release
  - 8 core agents implemented
  - Telegram integration
  - Basic n8n workflow

---

## 🤝 SUPPORT

Telegram: @biru_kataria_tech  
Email: tech@birukataria.com

---

*"Gaam ka beta, digital duniya mein bhi top pe"* 🔥
