import asyncio
import json
import os
from agents import AutoPostingAgent, PostingMode

async def main():
    print("--- Biru Bhai Auto Poster (Simulation) ---")
    
    # Load Strategy
    strategy_file = "output/strategy_plan.json"
    if not os.path.exists(strategy_file):
        print(f"Error: {strategy_file} not found. Run generate_strategy.py first.")
        return
        
    with open(strategy_file, "r") as f:
        strategy_data = json.load(f)
        
    print(f"Loaded Strategy Plan: {len(strategy_data.get('content_calendar', []))} posts scheduled.")
    
    # In real world, we would loop and wait for scheduled times.
    # For simulation, we'll process 3 mock posts from the calendar.
    
    poster = AutoPostingAgent(mode=PostingMode.APPROVAL)
    
    print("\n--- Starting Posting Run ---")
    
    # Mock some data if calendar is empty or just use the first few
    calendar = strategy_data.get("content_calendar", [])
    if not calendar:
        print("Calendar is empty! Creating a dummy post for demo.")
        calendar = [{
            "content_id": "clip_001_akad",
            "platform": "instagram_reel",
            "scheduled_time": "2026-02-12 19:00",
            "reason": "Demo Post",
            "predicted_score": 0.95
        }]
    
    # Let's just process the first 2 items to show flow
    poster.mode = PostingMode.AUTO # Force auto for demo speed, or Approval for interaction
    
    await poster.process_schedule({"content_calendar": calendar[:2]})
    
    print("\n--- Posting Complete ---")
    print(f"Total Successful Posts: {len(poster.posted_history)}")

if __name__ == "__main__":
    asyncio.run(main())
