import requests
import json
import time
import re
from typing import List, Dict, Optional

class VizardAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://elb-api.vizard.ai/hvizard-server-front/open-api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "VIZARDAI_API_KEY": api_key or ""
        }

    def _detect_video_type(self, url: str) -> int:
        """Detect videoType from URL. Returns int per Vizard API spec."""
        if re.search(r'youtube\.com|youtu\.be', url):
            return 2  # YouTube
        elif 'drive.google.com' in url:
            return 3  # Google Drive
        elif 'vimeo.com' in url:
            return 4  # Vimeo
        elif 'streamyard.com' in url:
            return 5  # StreamYard
        elif 'tiktok.com' in url:
            return 6  # TikTok
        elif 'twitter.com' in url or 'x.com' in url:
            return 7  # Twitter/X
        elif 'twitch.tv' in url:
            return 9  # Twitch
        elif 'loom.com' in url:
            return 10  # Loom
        elif 'facebook.com' in url:
            return 11  # Facebook
        elif 'linkedin.com' in url:
            return 12  # LinkedIn
        else:
            return 1  # Remote file (default)

    def submit_video(self, video_url: str, project_name: str = "BiruBhaiProject") -> Optional[str]:
        """Submit a video URL to Vizard AI for clipping"""
        if not self.api_key:
            print("Vizard Submission Failed: No API Key")
            return None

        video_type = self._detect_video_type(video_url)

        payload = {
            "videoUrl": video_url,
            "videoType": video_type,
            "lang": "auto",
            "preferLength": [0],  # Auto length
            "projectName": project_name,
            "subtitleSwitch": 1,
            "headlineSwitch": 1
        }

        # Add file extension for remote files
        if video_type == 1:
            ext = video_url.rsplit('.', 1)[-1].lower() if '.' in video_url.split('/')[-1] else "mp4"
            payload["ext"] = ext

        try:
            response = requests.post(
                f"{self.base_url}/project/create",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            print(f"Vizard Response [{response.status_code}]: {response.text[:200]}")
            response.raise_for_status()
            data = response.json()
            return str(data.get("projectId", ""))
        except requests.exceptions.HTTPError as e:
            print(f"Vizard Submission Failed (HTTP {e.response.status_code}): {e.response.text[:200]}")
            raise
        except Exception as e:
            print(f"Vizard Submission Failed: {e}")
            raise

    def status_check(self, project_id: str) -> str:
        """Check the status of a project. Returns 'processing', 'completed', or 'error'."""
        if not self.api_key:
            return "no_api_key"

        try:
            response = requests.get(
                f"{self.base_url}/project/query/{project_id}",
                headers=self.headers,
                timeout=15
            )
            data = response.json()
            code = data.get("code")

            if code == 2000:
                videos = data.get("videos", [])
                if videos:
                    return "completed"
                return "processing"
            elif code == 1000:
                return "processing"
            else:
                return "error"
        except Exception as e:
            print(f"Vizard Status Check Failed: {e}")
            return "error"

    def get_clips(self, project_id: str) -> List[Dict]:
        """Retrieve clips from a completed project"""
        if not self.api_key:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/project/query/{project_id}",
                headers=self.headers,
                timeout=15
            )
            data = response.json()
            code = data.get("code")

            if code == 2000:
                videos = data.get("videos", [])
                clips = []
                for v in videos:
                    clips.append({
                        "title": v.get("title", "Vizard Clip"),
                        "videoUrl": v.get("videoUrl", ""),
                        "duration": v.get("videoMsDuration", 0),
                        "viralScore": v.get("viralScore", ""),
                        "transcript": v.get("transcript", "")
                    })
                return clips
            return []
        except Exception as e:
            print(f"Vizard Clips Fetch Failed: {e}")
            return []
