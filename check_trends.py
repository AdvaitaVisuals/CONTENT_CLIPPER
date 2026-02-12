import asyncio
from agents import TrendAgent

async def main():
    print("Initializing Trend Agent...")
    agent = TrendAgent()
    
    print("Analyzing Haryanvi Music Trends and Competitor Data...")
    try:
        report = await agent.analyze_trends()
        
        print("\n--- TREND REPORT ---")
        print(f"Weekly Summary:\n{report['weekly_summary']}\n")
        
        print("Top Recommendations:")
        for rec in report['recommendations']:
            print(f"✅ {rec}")
            
        print("\nDetailed Insights:")
        for insight in report['insights']:
            print(f"- [{insight['trend_type'].upper()}] {insight['description']} (Conf: {insight['confidence']:.0%})")
            
    except Exception as e:
        print(f"Error executing trend analysis: {e}")

if __name__ == "__main__":
    asyncio.run(main())
