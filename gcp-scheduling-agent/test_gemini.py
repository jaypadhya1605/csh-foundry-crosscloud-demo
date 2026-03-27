"""Quick test of the Gemini-powered GCP agent."""
import httpx
import json

URL = "https://csh-scheduling-agent-732227602168.us-central1.run.app"

# Test 1: existing /invoke still works
print("=" * 60)
print("TEST 1: /invoke (existing endpoint)")
print("=" * 60)
r = httpx.post(f"{URL}/invoke", json={"action": "find_available", "parameters": {"specialty": "Cardiology"}}, timeout=30)
d = r.json()
print(f"Status: {r.status_code}, Count: {d.get('count')}")

# Test 2: Gemini /chat - find appointment
print()
print("=" * 60)
print("TEST 2: /chat — 'I need a Cardiology appointment at St. Luke'")
print("=" * 60)
r = httpx.post(f"{URL}/chat", json={"message": "I need a Cardiology appointment at St. Luke"}, timeout=30)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Model: {d.get('model')}")
print(f"Gemini reasoning: {d.get('gemini_reasoning')}")
print(f"Action: {d.get('action')}")
print(f"Params: {d.get('parameters')}")
print(f"Data count: {d.get('data', {}).get('count', '?')}")
print(f"Summary: {d.get('summary', '')[:300]}")

# Test 3: Gemini /chat - patient lookup
print()
print("=" * 60)
print("TEST 3: /chat — 'What appointments does Maria Garcia have?'")
print("=" * 60)
r = httpx.post(f"{URL}/chat", json={"message": "What appointments does patient P-1001 Maria Garcia have?"}, timeout=30)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Model: {d.get('model')}")
print(f"Gemini reasoning: {d.get('gemini_reasoning')}")
print(f"Action: {d.get('action')}")
print(f"Data count: {d.get('data', {}).get('count', '?')}")
print(f"Summary: {d.get('summary', '')[:300]}")

# Test 4: Gemini /chat - ambiguous
print()
print("=" * 60)
print("TEST 4: /chat — 'What is the weather like today?'")
print("=" * 60)
r = httpx.post(f"{URL}/chat", json={"message": "What is the weather like today?"}, timeout=30)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Action: {d.get('action')}")
print(f"Reasoning: {d.get('reasoning', d.get('gemini_reasoning', ''))}")
