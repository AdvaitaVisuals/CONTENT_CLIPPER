try:
    from agents.viral_cutter_agent import ViralCutterAgent
    print("Success: agents.viral_cutter_agent imported")
except ImportError as e:
    print(f"Error: {e}")

try:
    import api.factory_graph
    print("Success: api.factory_graph imported")
except ImportError as e:
    print(f"Error: {e}")
