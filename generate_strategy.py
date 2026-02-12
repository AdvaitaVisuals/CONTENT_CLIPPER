import argparse
import json
import os
from agents import StrategyBrain

def main():
    parser = argparse.ArgumentParser(description="Generate content strategy from clips and trends.")
    parser.add_argument("--clips_file", default="output/clip_specs.json", help="Path to clip specs JSON")
    parser.add_argument("--trends_file", default="output/trends.json", help="Path to trends JSON (optional)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to plan for")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.clips_file):
        print(f"Error: Clips file not found: {args.clips_file}")
        print("Run process_video.py first.")
        return

    print("Loading clip data...")
    with open(args.clips_file, "r", encoding="utf-8") as f:
        clips = json.load(f)
        
    print(f"Loaded {len(clips)} clips.")
    
    # Mock trend data if file missing or using default empty
    trends = []
    if os.path.exists(args.trends_file):
        with open(args.trends_file, "r", encoding="utf-8") as f:
            trends = json.load(f)
    else:
        print("Using default trend assumptions (no file provided).")
        trends = [{"trend_type": "content_format", "description": "akad wali reels chal rahi hain"}]

    # Mock memory data (placeholder)
    memory_data = {
        "emotion_performance": {
            "akad": {"avg_engagement": 0.08},
            "dard": {"avg_engagement": 0.06},
            "general": {"avg_engagement": 0.04}
        }
    }
    
    brain = StrategyBrain()
    print("Generating strategy...")
    
    strategy = brain.make_decisions(clips, trends, memory_data, duration_days=args.days)
    
    print("\n--- STRATEGY PLAN ---")
    print(f"Guidance: {strategy['weekly_guidance']}\n")
    
    print("Content Calendar:")
    if not strategy['action_commands']:
         print("No content scheduled (maybe all clips were weak?).")
    
    for cmd in strategy['action_commands']:
        print(f"✅ {cmd}")
        
    if strategy['stop_list']:
        print("\nSkipped Content (Weak/Bad Fit):")
        for item in strategy['stop_list']:
            print(f"❌ {item['clip_id']}: {item['reason']}")

    # Save strategy
    output_path = "output/strategy_plan.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2, default=str)
    print(f"\nFull strategy saved to {output_path}")

if __name__ == "__main__":
    main()
