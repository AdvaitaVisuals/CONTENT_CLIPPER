import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("VIZARD_API_KEY")
if not API_KEY:
    print("[ERROR] VIZARD_API_KEY is missing in .env file.")
    exit(1)

print(f"[INFO] Using API Key: {API_KEY[:8]}... (hidden)")

def test_vizard_submission():
    from agents.vizard_agent import VizardAgent
    agent = VizardAgent(api_key=API_KEY)

    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    print(f"[INFO] Submitting: {test_url}")

    try:
        project_id = agent.submit_video(test_url, project_name="Test_Biru_Bhai")
        if project_id:
            print(f"[SUCCESS] Project created! ID: {project_id}")
            print(f"[INFO] Checking status...")
            status = agent.status_check(project_id)
            print(f"[INFO] Status: {status}")
        else:
            print("[FAIL] submit_video returned None (no API key?)")
    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    test_vizard_submission()
