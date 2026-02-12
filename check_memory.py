from agents import MemoryAgent
import time
import random

def main():
    print("--- Biru Bhai Memory System ---")
    
    agent = MemoryAgent() # Connects to artist_memory.db
    
    # 1. Simulate Recording Posts
    print("\nRecording demo posts...")
    
    dummy_posts = [
        {"clip_id": "clip_001", "platform": "instagram", "emotion": "akad", "posted_at": "2026-02-10 18:00"},
        {"clip_id": "clip_002", "platform": "youtube_shorts", "emotion": "dard", "posted_at": "2026-02-11 08:00"},
        {"clip_id": "clip_003", "platform": "instagram", "emotion": "akad", "posted_at": "2026-02-11 19:00"},
        {"clip_id": "clip_004", "platform": "facebook", "emotion": "mauj", "posted_at": "2026-02-12 12:00"},
    ]
    
    for post in dummy_posts:
        agent.record_post(post)
        
    print(f"Recorded {len(dummy_posts)} posts.")
    
    # 2. Simulate Performance Updates (after some time)
    print("\nUpdating performance metrics...")
    
    # Random metrics generator
    updates = [
        {"clip_id": "clip_001", "views": 50000, "likes": 4000, "comments": 200, "shares": 50}, # Strong
        {"clip_id": "clip_002", "views": 12000, "likes": 500, "comments": 20, "shares": 5},    # Weak
        {"clip_id": "clip_003", "views": 65000, "likes": 6000, "comments": 450, "shares": 100}, # Viral
        {"clip_id": "clip_004", "views": 25000, "likes": 1500, "comments": 100, "shares": 20}   # Average
    ]
    
    for update in updates:
        metrics = {k: v for k, v in update.items() if k != 'clip_id'}
        agent.update_performance(update['clip_id'], metrics)
        
    print("Metrics updated.")
    
    # 3. Generate Report
    print("\n--- LEARNING REPORT ---")
    report = agent.get_learning_report()
    
    print("\nEmotion Performance:")
    for emotion, data in report['emotion_performance'].items():
        print(f"   [{emotion.upper()}] Avg Views: {data['avg_views']:.0f} | Engagement: {data['avg_engagement']:.1%}")
        
    print("\nRecent AI Insights:")
    for insight in report['recent_insights']:
        print(f"   💡 {insight}")
        
    print("\nRecommendations for Next Strategy:")
    for rec in report['recommendations']:
        print(f"   ✅ {rec}")

if __name__ == "__main__":
    main()
