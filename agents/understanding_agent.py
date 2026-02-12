import os

class UnderstandingAgent:
    def __init__(self):
        # Lazy load dependencies ONLY when needed or instantiated
        # This prevents Vercel from crashing on import
        try:
            import imageio_ffmpeg
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            self.ffmpeg_path = "ffmpeg" # Fallback if not installed

        self.whisper_model = None
        self.emotion_classifier = None
        
        # We don't load models in init to keep startup fast
        print("Understanding Agent initialized (Lazy Loading Enabled)")
    
    def _load_resources(self):
        # Actually load heavy models here
        if self.whisper_model: return
        
        try:
            import whisper
            from transformers import pipeline
            import imageio_ffmpeg
            
            # Ensure FFmpeg is in PATH for Whisper
            ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
            if ffmpeg_dir not in os.environ["PATH"]:
                 print(f"UnderstandingAgent: Adding FFmpeg to PATH: {ffmpeg_dir}")
                 os.environ["PATH"] += os.pathsep + ffmpeg_dir
            
            # Load Whisper model (can take time)
            print("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")  # Using 'base' for faster testing
            
            # Initialize emotion classifier
            try:
                self.emotion_classifier = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base" 
                )
            except Exception as e:
                print(f"Warning: Could not load emotion classifier: {e}")
        except ImportError as e:
            print(f"Warning: Could not load AI models. Are dependencies installed? {e}")
        
    def extract_audio(self, video_path: str) -> str:
        """FFmpeg se audio extract"""
        import subprocess
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        
        # Use imageio_ffmpeg binary path
        subprocess.run([
            self.ffmpeg_path, '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-y', audio_path # Added -y to overwrite
        ], check=True)
        return audio_path
    
    def transcribe_with_timestamps(self, audio_path: str) -> dict:
        """Whisper se lyrics + timestamps with safety checks"""
        self._load_resources()
        if not self.whisper_model:
            return {"text": "AI model not loaded", "segments": []}

        import librosa
        import numpy as np

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            print("Warning: Audio file is empty or missing.")
            return {"text": "", "segments": []}

        # Load audio via librosa
        audio, _ = librosa.load(audio_path, sr=16000, mono=True)
        
        # Guard: Check if audio is empty or effectively silent
        if len(audio) == 0:
            print("Warning: Loaded audio array has zero length.")
            return {"text": "", "segments": []}
            
        if np.abs(audio).max() < 1e-5:
            print("Warning: Audio appears to be silent.")
            return {"text": "", "segments": []}

        audio = audio.astype(np.float32)
        
        try:
            # Added fp16=False for better compatibility on CPU/Windows
            result = self.whisper_model.transcribe(
                audio,
                language="hi",
                word_timestamps=True,
                fp16=False if os.name == 'nt' else True 
            )
            return result
        except Exception as e:
            print(f"Whisper transcription failed: {e}")
            return {"text": "", "segments": []}
    
    def detect_beat_drops(self, audio_path: str) -> dict:
        """Librosa se beat detection"""
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Onset strength for drops
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10)
        drop_times = librosa.frames_to_time(peaks, sr=sr)
        
        return {
            "tempo": float(tempo),
            "beat_times": beat_times.tolist(),
            "drop_times": drop_times.tolist()
        }
    
    def tag_emotions(self, lyrics_segments: list) -> list:
        """Har line ko emotion tag karo"""
        emotion_map = {
            "akad": ["theke pe", "chhore", "attitude", "na dare", "jaat", "bhai", "yaar"],
            "dard": ["roya", "dil", "judai", "yaad", "tanha", "dhoka"],
            "pyaar": ["gore", "naina", "ishq", "dil", "sajna", "love"],
            "gaon_pride": ["gaam", "khap", "desi", "haryana", "tau", "khet"],
            "mauj": ["party", "daaru", "masti", "yaari", "chakk", "fun"]
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
        if not line_counts:
            return None
            
        chorus_line = line_counts.most_common(1)[0]
        
        if chorus_line[1] > 1:
            chorus_segments = [s for s in segments if s["text"].strip().lower() == chorus_line[0]]
            return {
                "text": chorus_line[0],
                "count": chorus_line[1],
                "timestamps": [s["start"] for s in chorus_segments]
            }
        return None

if __name__ == "__main__":
    # Test script for Understanding Agent
    agent = UnderstandingAgent()
    print("Understanding Agent initialized.")
    # Add dummy test if needed
