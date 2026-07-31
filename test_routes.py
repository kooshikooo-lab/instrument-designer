import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\instrument-designer')
from woodwind_designer.engine.design_server import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("Testing /design/...")
response = client.post("/design/", json={"preset": "folk_whistle", "quick": True})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

print("\nTesting /design/design/...")
response = client.post("/design/design", json={"preset": "folk_whistle", "quick": True})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")