import requests
import json
import time
from typing import List, Dict, Optional

class VizardAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://rest.vizard.ai/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }

    def submit_video(self, video_url: str, project_name: str = "BiruBhaiProject") -> Optional[str]:
        """Submit a video URL to Vizard AI for clipping"""
        if not self.api_key:
            return None
            
        payload = {
            "projectName": project_name,
            "videoUrl": video_url,
            "lang": "auto",
            "subtitleSwitch": 1,
            "headlineSwitch": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/project",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            # Assuming the response contains a projectId
            return data.get("data", {}).get("projectId")
        except Exception as e:
            print(f"Vizard Submission Failed: {e}")
            return None

    def get_clips(self, project_id: str) -> List[Dict]:
        """Poll for clips from a processed project"""
        if not self.api_key:
            return []
            
        try:
            response = requests.get(
                f"{self.base_url}/project/{project_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            # The data structure might vary, but we're looking for the 'clips' or 'highlights'
            result = data.get("data", {})
            status = result.get("status")
            
            if status == "completed":
                return result.get("clips", [])
            else:
                return [] # Still processing or failed
        except Exception as e:
            print(f"Vizard Poll Failed: {e}")
            return []

    def status_check(self, project_id: str) -> str:
        """Check the status of a project"""
        if not self.api_key:
            return "no_api_key"
            
        try:
            response = requests.get(
                f"{self.base_url}/project/{project_id}",
                headers=self.headers
            )
            data = response.json()
            return data.get("data", {}).get("status", "unknown")
        except:
            return "error"
