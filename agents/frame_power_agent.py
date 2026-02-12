import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import List, Optional
import os

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
        # Load Haar Cascade for face detection
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        if not os.path.exists(cascade_path):
            print(f"Warning: Haar cascade not found at {cascade_path}. Face detection might fail.")
            
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.quality_threshold = 0.6  # Slightly lowered for robustness
        
    def extract_key_frames(self, video_path: str, understanding_data: dict) -> List[FrameSpec]:
        """Video se best frames nikalo"""
        if not os.path.exists(video_path):
             print(f"Error: Video file not found: {video_path}")
             return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
             print(f"Error: Could not open video: {video_path}")
             return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        
        candidate_frames = []
        
        # Strategy 1: High emotion moments from understanding data
        segments = understanding_data.get("lyrics_segments", [])
        for segment in segments:
            if segment.get("viral_potential", 0) > 0.7:
                timestamp = segment["start"]
                frame = self._extract_frame_at(cap, timestamp, fps)
                if frame is not None:
                    spec = self._analyze_frame(frame, timestamp, segment)
                    if spec.quality_score > self.quality_threshold:
                        candidate_frames.append(spec)
        
        # Strategy 2: Beat drops (dynamic poses)
        drops = understanding_data.get("beat_analysis", {}).get("drop_timestamps", [])
        for drop_time in drops:
            frame = self._extract_frame_at(cap, drop_time, fps)
            if frame is not None:
                spec = self._analyze_frame(frame, drop_time, {"emotions": ["mauj"], "text": "Feel the Beat 🔥"})
                if spec.quality_score > self.quality_threshold:
                    candidate_frames.append(spec)
        
        cap.release()
        return self._select_best_frames(candidate_frames, max_count=5)
    
    def _extract_frame_at(self, cap, timestamp: float, fps: float) -> Optional[np.ndarray]:
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
        # Normalizing variance: usually >100 is ok, >500 is good. capping at 500.
        sharpness_score = min(laplacian_var / 500.0, 1.0)
        
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
        if total == 0: return 0.0
        
        dark = hist[:50].sum() / total
        bright = hist[200:].sum() / total
        
        if dark > 0.6 or bright > 0.6: # Relaxed threshold slightly
            return 0.4  # Too dark or too bright
        return 0.8  # Balanced
    
    def _select_best_frames(self, frames: List[FrameSpec], max_count: int) -> List[FrameSpec]:
        """Best frames select karo, avoid duplicates"""
        frames.sort(key=lambda x: x.quality_score, reverse=True)
        
        selected = []
        timestamps = []
        
        for frame in frames:
            # Check if too close to existing selected frame (within 2 seconds)
            is_close = False
            for t in timestamps:
                if abs(frame.timestamp - t) < 2.0:
                    is_close = True
                    break
            
            if not is_close:
                selected.append(frame)
                timestamps.append(frame.timestamp)
            
            if len(selected) >= max_count:
                break
                
        return selected

    def create_poster_image(self, video_path: str, spec: FrameSpec, output_path: str, style: str = "desi"):
        """Frame se poster banao and save"""
        # Re-extract frame (inefficient but cleaner for now vs passing numpy array)
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame = self._extract_frame_at(cap, spec.timestamp, fps)
        cap.release()
        
        if frame is None:
            print(f"Error: Could not extract frame at {spec.timestamp}")
            return

        # Convert to RGB (OpenCV uses BGR)
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Overlay Text - REMOVED for clean "no text" look
        # if spec.overlay_text:
        #     img = self._add_text_overlay(img, spec.overlay_text, style)
        
        # Color grading for desi vibe
        if style == "desi":
            img = self._apply_desi_grade(img)
        
        img.save(output_path)
        print(f"Poster saved: {output_path}")

    def _add_text_overlay(self, img: Image, text: str, style: str) -> Image:
        """Text overlay with desi typography"""
        draw = ImageDraw.Draw(img)
        
        # Fallback to default font if custom font not present
        # In a real setup, we'd ensure fonts/NotoSansDevanagari-Bold.ttf exists
        try:
            # Trying to load a system font or a specific one. 
            # For simplicity in this env, use default or a basic one.
            # Windows usually has arial.ttf
            font_size = 60
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            try:
                # Try Linux path or generic
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            except:
                print("Warning: Could not load custom font, using default.")
                font = ImageFont.load_default()
        
        # Wrap text if too long (simple approach) or just cut it
        if len(text) > 30:
            text = text[:30] + "..."

        # Position: bottom center
        img_width, img_height = img.size
        
        try:
             text_bbox = draw.textbbox((0, 0), text, font=font)
             text_width = text_bbox[2] - text_bbox[0]
             text_height = text_bbox[3] - text_bbox[1]
        except AttributeError:
             # Older PIL versions
             text_width, text_height = draw.textsize(text, font=font)

        x = (img_width - text_width) // 2
        y = img_height - 150
        
        # Draw with shadow/outline for readability
        outline_color = "black"
        text_color = "white"
        
        # Thick outline simulation
        for adj in range(-2, 3):
             for adj2 in range(-2, 3):
                  draw.text((x+adj, y+adj2), text, font=font, fill=outline_color)

        draw.text((x, y), text, font=font, fill=text_color)       # Main text
        
        return img
    
    def _apply_desi_grade(self, img: Image) -> Image:
        """Warm desi color grading"""
        arr = np.array(img).astype(float)
        
        # Warm tones: slightly boost Red, reduce Blue
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)  # Red boost
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.9, 0, 255)  # Blue reduce
        
        # Increase Contrast
        # (pixel - 128) * contrast + 128
        arr = np.clip((arr - 128) * 1.1 + 128, 0, 255)
        
        return Image.fromarray(arr.astype(np.uint8))

if __name__ == "__main__":
    agent = FramePowerAgent()
    print("Frame Power Agent initialized.")
