import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json
import os

class PostingMode(Enum):
    AUTO = "auto"
    APPROVAL = "approval"
    SCHEDULED = "scheduled"

# Mock classes for platforms
class InstagramPoster:
    async def post(self, media_path: str, caption: str, hashtags: List[str]) -> Dict:
        print(f"   [Instagram] Uploading {media_path}...")
        await asyncio.sleep(1) # Simulate network
        return {"success": True, "platform": "instagram", "post_id": "ig_12345", "url": "https://instagram.com/p/mock_id"}

class YouTubePoster:
    async def post(self, media_path: str, title: str, description: str) -> Dict:
        print(f"   [YouTube] Uploading {media_path}...")
        await asyncio.sleep(1.5)
        return {"success": True, "platform": "youtube_shorts", "post_id": "yt_67890", "url": "https://youtube.com/shorts/mock_id"}

class FacebookPoster:
    async def post(self, media_path: str, caption: str) -> Dict:
        print(f"   [Facebook] Uploading {media_path}...")
        await asyncio.sleep(1)
        return {"success": True, "platform": "facebook", "post_id": "fb_54321", "url": "https://facebook.com/mock_id"}

class TelegramNotifier:
    """Mock Telegram bot for notifications"""
    async def send_message(self, text: str):
        print(f"\n[Telegram Bot] 🔔 {text}\n")

class AutoPostingAgent:
    def __init__(self, mode: PostingMode = PostingMode.APPROVAL):
        self.mode = mode
        self.platforms = {
            "instagram_reel": InstagramPoster(),
            "youtube_shorts": YouTubePoster(),
            "facebook": FacebookPoster()
        }
        self.telegram_bot = TelegramNotifier()
        self.posted_history = []
        
    async def process_schedule(self, strategy_data: Dict):
        """Process the content calendar from strategy brain"""
        calendar = strategy_data.get("content_calendar", [])
        
        print(f"📅 Processing {len(calendar)} scheduled items...")
        
        for item in calendar:
            # Check if it's time to post (Mock: assume we post everything for demo)
            # In real app: if datetime.now() >= item['scheduled_time']:
            
            print(f"Processing item: {item['content_id']} for {item['platform']}")
            
            if self.mode == PostingMode.AUTO:
                await self._execute_post(item)
            elif self.mode == PostingMode.APPROVAL:
                await self._request_approval(item)
            else:
                print(f"   Queued for scheduling: {item['scheduled_time']}")

    async def _request_approval(self, item: Dict):
        """Simulate sending approval request"""
        msg = f"APPROVAL NEEDED: Clip {item['content_id']} on {item['platform']}\n   Time: {item['scheduled_time']}\n   Reason: {item['reason']}"
        await self.telegram_bot.send_message(msg)
        
        # Simulating manual approval for demo purposes
        user_input = "y" # input("Approve this post? (y/n): ")
        if user_input.lower() == 'y':
            await self._execute_post(item)
        else:
            print("   ❌ Post rejected/skipped.")

    async def _execute_post(self, item: Dict):
        """Actually execute the post on the platform"""
        platform_key = item.get("platform", "instagram_reel")
        poster = self.platforms.get(platform_key)
        
        if not poster:
            print(f"   Warning: No poster found for {platform_key}")
            return

        # Locate file (mock logic for path)
        # Assuming clip_id maps to a file in output/clips or we take the first matching file
        # For this demo, we'll pretend the file exists
        media_path = f"output/clips/{item['content_id']}.mp4" 
        
        # Prepare content
        caption = f"Desi Swag! 🔥 #BiruKataria #Haryanvi" # Placeholder, theoretically comes from CaptionAgent
        
        try:
            if platform_key == "youtube_shorts":
                result = await poster.post(media_path, title=item['content_id'], description=caption)
            else:
                result = await poster.post(media_path, caption=caption, hashtags=[])
            
            if result['success']:
                print(f"   ✅ SUCCESS: Posted to {result['platform']} - {result['url']}")
                self.posted_history.append(result)
                await self.telegram_bot.send_message(f"Listen up! New drop on {platform_key}: {result['url']}")
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

if __name__ == "__main__":
    agent = AutoPostingAgent(mode=PostingMode.APPROVAL)
    print("Auto Posting Agent initialized.")
